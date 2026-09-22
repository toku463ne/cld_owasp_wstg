#!/usr/bin/env python3
"""実施タスクリストの生成と、進捗の表示。

    uv run scripts/tasks.py            # 今の進捗と「次にやること」を表示
    uv run scripts/tasks.py --write    # TASKS.md を再生成（順序・フェーズの変更後）
    uv run scripts/tasks.py --check    # TASKS.md が最新か確認（selftest 用）

順序の元データは matrix/coverage.yaml の phases: と各アクティビティの
phase / order / depends_on / impact。進捗は evidence/*/run.yaml の verdict から判定する
（要約フィールドのみを読み、cmd/ や artifacts/ の中身は開かない）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

try:  # 手順からコマンド（＝必要ツール）を拾うため new_activity と共有する
    from new_activity import extract_commands
except ImportError:
    def extract_commands(steps, target=None):
        return []

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_YAML = REPO_ROOT / "matrix" / "coverage.yaml"
WSTG_TESTS = REPO_ROOT / "matrix" / "wstg_tests.yaml"
CRITERIA_YAML = REPO_ROOT / "matrix" / "criteria.yaml"
TASKS_MD = REPO_ROOT / "TASKS.md"
DEFAULT_EVIDENCE = REPO_ROOT / "evidence"

IMPACT_LABEL = {"low": "低", "medium": "中", "high": "高（要事前合意）"}
DONE, DOING, TODO = "完了", "実施中", "未着手"

# ツール名 → Kali でのセットアップ。フェーズ単位で「未導入分の apt」を案内するため。
#   APT_PKG … `sudo apt install -y <pkg...>` にまとめる
#   OTHER   … apt 以外（pipx / npm / go / git）。個別コマンドをそのまま出す。ランタイム
#             （npm / go）は Kali 既定イメージに無いので、その導入も含めて1行で出す
#   BUILTIN … Kali 同梱 or Burp 内（インストール不要。名前だけ挙げる）
#   MANUAL  … 手動・ブラウザ・ヒアリング等（インストール不要）
# 分類は「小文字化した完全一致」→「先頭トークン一致」の順で引く。
APT_PKG = {
    "whois": "whois", "dig": "bind9-dnsutils", "nslookup": "bind9-dnsutils",
    "theharvester": "theharvester", "amass": "amass", "subfinder": "subfinder",
    "nmap": "nmap",
    "ncat": "ncat", "nc": "netcat-traditional", "curl": "curl", "wget": "wget",
    "ffuf": "ffuf", "gobuster": "gobuster", "dirsearch": "dirsearch",
    "sqlmap": "sqlmap", "nikto": "nikto", "whatweb": "whatweb",
    "testssl.sh": "testssl.sh", "sslyze": "sslyze", "hydra": "hydra",
    "dotdotpwn": "dotdotpwn", "wfuzz": "wfuzz", "padbuster": "padbuster",
    "httpx": "httpx-toolkit", "httpx-toolkit": "httpx-toolkit", "dnsx": "dnsx",
    "subjack": "subjack",
    "aws": "awscli", "awscli": "awscli", "grep/ripgrep": "ripgrep",
    "jq": "jq", "searchsploit": "exploitdb", "traceroute": "traceroute",
}
# nmap / ncat / nikto は 2025 年の nmap ライセンス変更で main → non-free に移った。
# Kali 既定の sources.list（main contrib non-free non-free-firmware）ならそのまま入るが、
# main だけに絞った社内ミラーでは「Unable to locate package nmap」になる。
# npm 系は Kali 既定イメージに npm が無く `sudo: npm: command not found` で止まるため、
# apt での導入まで含めて1行で出す。
NPM_I = "sudo apt install -y npm && sudo npm install -g"
# go 系も同様。`go install` の出力先（~/go/bin）は既定の PATH に無いので併せて案内する。
GO_I = "sudo apt install -y golang-go && go install"
GO_PATH = 'export PATH="$PATH:$(go env GOPATH)/bin"'
OTHER_CMD = {
    "retire": f"{NPM_I} retire", "retire.js": f"{NPM_I} retire",
    "git-dumper": "pipx install git-dumper",
    "wscat": f"{NPM_I} wscat",
    # interactsh は Kali にパッケージが無い（apt install interactsh は失敗する）。
    "interactsh": (f"{GO_I} github.com/projectdiscovery/interactsh/cmd/"
                   f"interactsh-client@latest && {GO_PATH}"),
    "interactsh-client": (f"{GO_I} github.com/projectdiscovery/interactsh/cmd/"
                          f"interactsh-client@latest && {GO_PATH}"),
}
# Kali の burpsuite パッケージは Community 版。Burp Collaborator と
# Burp HTTP Request Smuggler は Professional が要る（Community では使えない）ので、
# 該当手順は curl / 自前の外部受信先や手動確認で代替する前提で書く。
BUILTIN = {
    "burp suite", "burp collaborator", "burp http request smuggler", "burp intruder",
    "burp repeater", "burp sequencer", "dom invader", "inql", "autorize / authmatrix",
    "owasp zap",
}
MANUAL = {
    "google/bing dorking", "crt.sh", "wappalyzer", "graphql voyager",
    "cis benchmark チェックリスト", "securityheaders.io 相当の手動チェック",
    "ls -l / icacls", "eicar テストファイル", "ブラウザ2枚", "ブラウザ開発者ツール",
    "メールクライアント", "ヒアリング", "業務仕様書", "手動", "手動 payload",
    "手動レビュー", "手動操作",
}


def classify_tool(tool: str):
    """ツール名を ('apt'|'other'|'builtin'|'manual', 値) に分類する。"""
    low = tool.strip().lower()
    if low in BUILTIN:
        return ("builtin", tool.strip())
    if low in MANUAL:
        return ("manual", tool.strip())
    if low in APT_PKG:
        return ("apt", APT_PKG[low])
    if low in OTHER_CMD:
        return ("other", OTHER_CMD[low])
    head = re.split(r"[ /（(]", low)[0]
    if head in APT_PKG:
        return ("apt", APT_PKG[head])
    if head in OTHER_CMD:
        return ("other", OTHER_CMD[head])
    return ("manual", tool.strip())  # 未知はインストール指示を出さず手動扱い


def phase_tool_names(acts_in_phase: list, criteria: dict) -> list:
    """フェーズで使うツール名を集める（活動の tools + 手順中のコマンドのバイナリ）。"""
    names: list = []
    for a in acts_in_phase:
        for t in a.get("tools", []) or []:
            names.append(t)
        for cov in a.get("covers", []):
            steps = criteria.get(cov["id"], {}).get("steps", [])
            for cmd in extract_commands(steps, None):
                # for/while ループだと先頭が while で本体の dig 等を取りこぼすので、
                # コマンド内の全トークンのバイナリ名を見る（未知語は classify で手動扱い）。
                for tok in re.findall(r"[A-Za-z0-9_.-]+", cmd):
                    names.append(tok.split("/")[-1])
    return names


def render_phase_setup(acts_in_phase: list, criteria: dict) -> list:
    """フェーズ冒頭に置く『準備（Kali ツール）』の行を作る。"""
    apt: set = set()
    other: list = []
    builtin: set = set()
    for name in phase_tool_names(acts_in_phase, criteria):
        kind, val = classify_tool(name)
        if kind == "apt":
            apt.add(val)
        elif kind == "other":
            if val not in other:
                other.append(val)
        elif kind == "builtin":
            builtin.add(val)
    out: list = []
    if not (apt or other or builtin):
        return out
    out.append("**準備（このフェーズで使う Kali ツール。未導入のものだけ）**")
    if apt:
        out.append(f"- apt: `sudo apt install -y {' '.join(sorted(apt))}`")
    for cmd in other:
        out.append(f"- 個別: `{cmd}`")
    if builtin:
        out.append(f"- Kali 同梱 / Burp 内（導入不要）: {', '.join(sorted(builtin))}")
    out.append("")
    return out


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"{path} がありません。README の「生成物を作り直すとき」を参照。")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sorted_activities(coverage: dict) -> list:
    acts = coverage["activities"]
    missing = [a["id"] for a in acts if "order" not in a or "phase" not in a]
    if missing:
        raise SystemExit(f"phase / order の無いアクティビティ: {', '.join(missing)}")
    return sorted(acts, key=lambda a: a["order"])


def scan_progress(evidence_root: Path, activity_ids: set[str]) -> dict:
    """evidence/*/run.yaml から、アクティビティごとの進捗を集計する。"""
    progress = {aid: {"state": TODO, "dirs": [], "done": 0, "total": 0} for aid in activity_ids}
    if not evidence_root.exists():
        return progress
    for run_yaml in sorted(evidence_root.glob("*/run.yaml")):
        try:
            data = yaml.safe_load(run_yaml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        aid = data.get("activity_id")
        if aid not in progress:
            continue
        covers = [c for c in (data.get("covers") or []) if isinstance(c, dict)]
        done = sum(1 for c in covers if str(c.get("verdict", "todo")).lower() != "todo")
        p = progress[aid]
        p["dirs"].append(run_yaml.parent.name)
        p["done"] += done
        p["total"] += len(covers)
        p["state"] = DONE if (covers and done == len(covers)) else DOING
    return progress


def render_tasks_md(coverage: dict, tests: dict, criteria: dict) -> str:
    phases = coverage.get("phases", {})
    acts = sorted_activities(coverage)
    by_phase: dict = {}
    for a in acts:
        by_phase.setdefault(a["phase"], []).append(a)
    out: list[str] = []
    w = out.append

    w("# 実施タスクリスト（上から順に消化する）")
    w("")
    w("> 自動生成: `uv run scripts/tasks.py --write`")
    w("> 順序・依存の元データは `matrix/coverage.yaml`。ここを直接編集しない。")
    w("")
    w(f"アクティビティ {len(acts)} 本で、WSTG v4.2 の実施対象 "
      f"{sum(1 for t in tests.values() if not t.get('deprecated'))} 項目をカバーする。")
    w("進捗は `uv run scripts/tasks.py` で確認できる。")
    w("")

    w("## フェーズ0 — 準備（1回だけ）")
    w("")
    w("- [ ] 対象・時間帯・禁止事項・連絡先を合意する（`impact: high` の項目は特に）")
    w("- [ ] ロールごとのテストアカウントを入手する")
    w("- [ ] `uv sync` — Python 環境を用意（uv が無い会社PCでは `pip install pyyaml`）")
    w("- [ ] `./scripts/selftest.sh` — ツールが動くことを確認")
    w("- [ ] （原文を読みたいとき）`./scripts/fetch_wstg.sh`")
    w("- [ ] プロキシ配下なら外向き疎通を確認: `env | grep -i proxy` と "
      "`curl -sI https://crt.sh | head -1`")
    w("      - 通らないなら README「プロキシ配下での準備」を先に済ませる"
      "（`sudo` は `-E` か `env_keep`、DNS はプロキシを通らない）")
    w("- 実施できるアクティビティ ID の一覧: `uv run scripts/new_activity.py`（引数なし）")
    w("- 複数サイトを回すときは各アクティビティで `--target <site>` を付ける")
    w("")
    w("Kali のツール準備は各フェーズ冒頭の「準備」に未導入分の `apt` をまとめてある。")
    w("まず `sudo apt update`。`pipx` / `npm` / `go` を使う個別導入もフェーズ内に記載。")
    w("")

    w("## 実施記録の見方（record.html）")
    w("")
    w("各アクティビティのフォルダに `record.html`（WSTG-ID ごとのタブ）ができる。閲覧はダブルクリック")
    w("（`file://`・Firefox 推奨）でよい。結果とスクショは `cmd/`・`artifacts/` のファイルを参照表示する")
    w("ので、`.txt` を手で編集したらリロードで反映される（`evidence.js` の作り直しは不要）。")
    w("")
    w("- **スクショの撮影・削除ボタンを使う／Chrome で確実に表示する**には、ローカルサーバ経由で開く。")
    w("  1つのサーバで `evidence/` 全体を配信し、トップの索引から全アクティビティを辿れる")
    w("  （アクティビティごとに立てなくてよい。判定サマリ付き）:")
    w("  `uv run scripts/serve_record.py --open`（索引）／"
      "`uv run scripts/serve_record.py evidence/<activity>-<yyyymmdd> --open`（直接開く）")
    w("  （127.0.0.1 のみ待受。GET のたびに最新化するので findings.md/run.yaml の手編集はリロードで反映）")
    w("- 手順ごとの『📷 この手順のスクショを撮る』→ 上部の待ち時間(秒)の間に対象ウィンドウを前面へ→範囲選択。")
    w("  間違えたら各画像の『🗑 削除』で消せる（`artifacts/shot-*.png` のみ）。")
    w("- CLI で撮るなら: `uv run scripts/save_shot.py evidence/<activity>-<yyyymmdd> --wid <WSTG-ID> [--step n] --grab --delay 3`")
    w("  （`--list-tools` で使える撮影ツール確認。X11=maim/xfce4-screenshooter、Wayland=grim+slurp を自動判定）")
    w("")

    current = None
    for a in acts:
        if a["phase"] != current:
            current = a["phase"]
            ph = phases.get(current, {})
            w(f"## フェーズ{current} — {ph.get('name', '')}")
            w("")
            if ph.get("goal"):
                w(ph["goal"])
                w("")
            for line in render_phase_setup(by_phase[current], criteria):
                w(line)
        deps = a.get("depends_on") or []
        covers = [c["id"] for c in a.get("covers", [])]
        w(f"### {a['order']}. `{a['id']}` — {a.get('title','')}")
        w("")
        w(a.get("summary", ""))
        w("")
        w(f"- 影響度: {IMPACT_LABEL.get(a.get('impact','low'), a.get('impact','low'))}"
          + (f" / 前提: {', '.join(f'`{d}`' for d in deps)}" if deps else " / 前提: なし"))
        w(f"- カード: {', '.join(f'[{c}](playbooks/{c}.md)' for c in covers)}")
        w("")
        tools = ", ".join(a.get("tools", []))
        w(f"- [ ] `uv run scripts/new_activity.py {a['id']}` でフォルダ一式を作る"
          "（複数サイトは `--target <site>`）")
        w(f"- [ ] `uv run scripts/run_activity.py evidence/{a['id']}-<yyyymmdd>` で"
          f"コマンド手順（{len(covers)} 項目・{tools}）を実行 ← `cmd/` に純粋なエビデンスが残る")
        w("      - 手動手順（Burp・ヒアリング等）は `artifacts/manual-*.txt` に観察を書く")
        w(f"      - 単発の直接実行は `uv run scripts/run_cmd.py evidence/{a['id']}-<yyyymmdd> -- <コマンド>`")
        w("- [ ] `run.yaml` の covers に WSTG-ID ごとの `verdict`（pass|fail|info|na|todo）と `finding`（要約のみ）を直接記入")
        w(f"- [ ] `uv run scripts/gen_record.py evidence/{a['id']}-<yyyymmdd>` で `record.html` を最新化して確認")
        w(f"      - 見る/スクショを撮る/消す: `uv run scripts/serve_record.py evidence/{a['id']}-<yyyymmdd> --open`"
          "（`--open` 無し引数なしなら全アクティビティの索引。閲覧だけなら record.html を直接開く）")
        w("")

    w("## 仕上げ")
    w("")
    w("- [ ] `uv run scripts/tasks.py` で todo の残りが無いことを確認")
    w("- [ ] `uv run scripts/export_checklist.py --summary` で CSV を出力")
    w("- [ ] CSV を目視レビュー（機密が混じっていないか）")
    w("- [ ] Google Sheets へ取り込み（ファイル → インポート → 現在のシートを置換）")
    w("- [ ] `fail` の項目について報告書とカードの判定基準を見直す")
    w("")
    return "\n".join(out)


def show_progress(coverage: dict, evidence_root: Path) -> int:
    phases = coverage.get("phases", {})
    acts = sorted_activities(coverage)
    progress = scan_progress(evidence_root, {a["id"] for a in acts})

    if not evidence_root.exists():
        print(f"[情報] {evidence_root} がまだありません。すべて未着手として表示します。\n")

    current = None
    for a in acts:
        if a["phase"] != current:
            current = a["phase"]
            print(f"\nフェーズ{current} — {phases.get(current, {}).get('name', '')}")
        p = progress[a["id"]]
        detail = f"{p['done']}/{p['total']} 判定済み" if p["total"] else ""
        blockers = [d for d in (a.get("depends_on") or []) if progress[d]["state"] != DONE]
        if p["state"] == TODO and blockers:
            detail = "前提未完: " + ", ".join(blockers)
        mark = {DONE: "x", DOING: "~", TODO: " "}[p["state"]]
        print(f"  [{mark}] {a['order']:2d}. {a['id']:<26s} {p['state']:<4s} {detail}")

    ready = [
        a for a in acts
        if progress[a["id"]]["state"] != DONE
        and all(progress[d]["state"] == DONE for d in (a.get("depends_on") or []))
    ]
    done = sum(1 for a in acts if progress[a["id"]]["state"] == DONE)
    print(f"\n進捗: {done}/{len(acts)} アクティビティ完了")
    if ready:
        nxt = ready[0]
        print(f"次にやること: {nxt['order']}. {nxt['id']} — {nxt.get('title','')}")
        state = progress[nxt["id"]]["state"]
        if state == TODO:
            print(f"  uv run scripts/new_activity.py {nxt['id']}")
        else:
            print(f"  run.yaml の covers を埋める: evidence/{progress[nxt['id']]['dirs'][0]}/run.yaml")
        if len(ready) > 1:
            print(f"  （並行して着手可: {', '.join(a['id'] for a in ready[1:4])}）")
    else:
        print("すべて完了。仕上げへ: uv run scripts/export_checklist.py --summary")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="TASKS.md を生成する")
    ap.add_argument("--check", action="store_true", help="TASKS.md が最新か確認する")
    ap.add_argument("--root", default=str(DEFAULT_EVIDENCE), help="エビデンスのルート（既定: evidence/）")
    ap.add_argument("--out", default=str(TASKS_MD), help="TASKS.md の出力先")
    args = ap.parse_args()

    coverage = load(COVERAGE_YAML)
    tests = {t["id"]: t for t in load(WSTG_TESTS)["tests"]}
    criteria = yaml.safe_load(CRITERIA_YAML.read_text(encoding="utf-8")) if CRITERIA_YAML.exists() else {}

    if args.write or args.check:
        text = render_tasks_md(coverage, tests, criteria or {})
        out = Path(args.out)
        if args.check:
            same = out.exists() and out.read_text(encoding="utf-8") == text
            print("最新です" if same else "差分あり: uv run scripts/tasks.py --write を実行してください")
            return 0 if same else 1
        out.write_text(text, encoding="utf-8")
        print(f"{out.name} を生成: {len(coverage['activities'])} アクティビティ")
        return 0

    return show_progress(coverage, Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
