#!/usr/bin/env python3
"""WSTG 原文 + matrix/criteria.yaml から、1テスト=1枚のプレイブックカードを生成する。

    uv run scripts/gen_playbooks.py
    uv run scripts/gen_playbooks.py --only WSTG-INFO-06

カードは自己完結・小サイズ（数百トークン）。社内 Gemini にデータと一緒に貼れること、
新人への説明台本・報告フォーマットに流用できることを狙う。

分担:
  - 機械抽出（手順・使用ツール・原文リンク） … WSTG 原文から毎回再生成
  - 判断（目的・pass/fail の見分け）          … matrix/criteria.yaml（手で育てる）
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wstg_parse import REPO_ROOT, load_tests  # noqa: E402

PLAYBOOK_DIR = REPO_ROOT / "playbooks"
COVERAGE_YAML = REPO_ROOT / "matrix" / "coverage.yaml"
CRITERIA_YAML = REPO_ROOT / "matrix" / "criteria.yaml"

WSTG_BASE = "https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing"
# criteria.yaml の手順に書く保存先プレースホルダ。カードでは説明的なパスに開く
# （実施記録では new_activity.py が実フォルダの artifacts/ に置換する）。
CARD_OUTDIR = "evidence/<活動フォルダ>/artifacts"
MAX_STEPS = 7
MAX_STEP_CHARS = 190


def clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text.replace("’", "'").replace("“", '"').replace("”", '"')


def truncate(text: str, limit: int = MAX_STEP_CHARS) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = cut.rfind(". ")
    return (cut[: dot + 1] if dot > limit * 0.5 else cut.rstrip() + " …")


def condense_steps(how_to_test: str) -> list[str]:
    lines = [l.strip() for l in how_to_test.splitlines() if l.strip()]
    skip_head = re.compile(r"^(example|sample|result|references?|summary)\b", re.I)
    heads = [l[4:].strip() for l in lines if l.startswith("### ") and not skip_head.match(l[4:].strip())]
    if len(heads) >= 2:
        steps = heads[:MAX_STEPS]
        # 見出しだけだと薄いので、各見出し直後の1文を添える
        detailed = []
        for head in steps:
            idx = lines.index(f"### {head}")
            first = ""
            for line in lines[idx + 1 :]:
                if line.startswith("### "):
                    break
                cand = clean(re.sub(r"^(\d+\.|-)\s*", "", line)).split(". ")[0]
                if len(cand) >= 20:
                    first = cand
                    break
            detailed.append(f"**{head}** — {truncate(first, 140)}" if first else f"**{head}**")
        return detailed
    body = [l for l in lines if not l.startswith("### ")]
    steps = []
    for line in body:
        line = re.sub(r"^(\d+\.|-)\s*", "", line)
        if len(clean(line)) < 25:
            continue
        steps.append(truncate(line))
        if len(steps) >= MAX_STEPS:
            break
    return steps


# 手順に現れたツール名 → カード上の正式表記。手順を唯一の真実にして、
# 「## 使用ツール」を手順から機械的に導出する（手順に出ないツールは載せない）。
# 正規表現は小文字化した手順テキストに対して照合する。上から順に評価する。
TOOL_PATTERNS = [
    (r"theharvester", "theHarvester"), (r"crt\.sh", "crt.sh"),
    (r"subfinder", "subfinder"), (r"\bamass\b", "amass"),
    (r"\bwhois\b", "whois"), (r"\bnslookup\b", "nslookup"), (r"\bdig\b", "dig"),
    (r"wayback|web\.archive", "Wayback Machine"), (r"\bdork|site:", "Google/Bing dorking"),
    (r"\bcurl\b", "curl"), (r"\bwget\b", "wget"), (r"\bnmap\b", "nmap"),
    (r"\bjq\b", "jq"), (r"searchsploit", "searchsploit"), (r"traceroute", "traceroute"),
    (r"\bffuf\b", "ffuf"), (r"gobuster", "gobuster"), (r"\bsqlmap\b", "sqlmap"),
    (r"testssl", "testssl.sh"), (r"\bsslyze\b", "sslyze"), (r"\bnikto\b", "nikto"),
    (r"\bwhatweb\b", "whatweb"), (r"wappalyzer", "Wappalyzer"), (r"\bhttpx\b", "httpx"),
    (r"retire", "Retire.js"), (r"git-dumper", "git-dumper"), (r"\bncat\b|\bnc \b", "ncat"),
    (r"\bhydra\b", "hydra"), (r"dotdotpwn", "DotDotPwn"), (r"\bwfuzz\b", "wfuzz"),
    (r"aws s3", "AWS CLI"), (r"\beicar\b", "EICAR テスト検体"), (r"padbuster", "padbuster"),
    (r"\bicacls\b", "icacls"), (r"\bnamei\b", "namei"), (r"accesschk", "AccessChk"),
    (r"\bls -l", "ls -l"),
    (r"burp sequencer", "Burp Sequencer"), (r"burp intruder", "Burp Intruder"),
    (r"burp repeater", "Burp Repeater"), (r"\bburp\b", "Burp Suite"),
    (r"\bzap\b|owasp zap", "OWASP ZAP"),
    (r"開発者ツール|devtools|sources\s*→|network\s*→|application\s*→|"
     r"application で|sources で|network で|network タブ", "ブラウザ開発者ツール"),
    (r"iframe|別ブラウザ|ブラウザで", "ブラウザ"),
]
_TOOL_RE = [(re.compile(p), name) for p, name in TOOL_PATTERNS]


def tools_from_steps(steps: list) -> list:
    """手順テキストに現れたツールを、出現順・ユニークで抜き出す。"""
    text = " ".join(steps).lower()
    hits = []
    for rx, name in _TOOL_RE:
        m = rx.search(text)
        if m:
            hits.append((m.start(), name))
    out: list = []
    for _, name in sorted(hits):
        if name not in out:
            out.append(name)
    # 具体的な Burp 機能名があれば、汎用の「Burp Suite」は重複なので落とす
    if any(t.startswith("Burp ") and t != "Burp Suite" for t in out):
        out = [t for t in out if t != "Burp Suite"]
    return out


def load_yaml(path: Path, default=None):
    if not path.exists():
        return default
    return yaml.safe_load(path.read_text(encoding="utf-8")) or default


def source_url(source: str) -> str:
    """ローカルの原文パスから owasp.org の URL を組み立てる。"""
    m = re.search(r"4-Web_Application_Security_Testing/(.+)$", source)
    if not m:
        return WSTG_BASE
    tail = re.sub(r"\.(html|md)$", "", m.group(1))
    return f"{WSTG_BASE}/{tail}"


def render_card(test, criteria: dict, activities: list, act_defs: dict) -> str:
    c = criteria.get(test.id, {})
    objectives = [
        clean(re.sub(r"^(\d+\.|-)\s*", "", l))
        for l in test.section("objectives").splitlines()
        if clean(l)
    ]
    tool_fallback = []
    for aid in activities:
        tool_fallback += act_defs.get(aid, {}).get("tools", [])
    outputs = []
    for aid in activities:
        outputs += act_defs.get(aid, {}).get("outputs", [])

    out: list[str] = []
    w = out.append
    w(f"# {test.id} — {test.title}")
    w("")
    w("<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。")
    w("     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->")
    w("")

    if test.deprecated:
        w(f"> **v4.2 で統合済み**: このテストは「{test.merged_into}」に統合された。単独では実施せず、")
        w("> 統合先のカードに従うこと。チェックリスト上は `na` で構わない。")
        w("")
        w(f"原文: {source_url(test.source)}")
        w("")
        return "\n".join(out)

    w("## 目的")
    w("")
    w(c.get("purpose") or truncate(test.section("summary"), 260) or "（原文の Summary 参照）")
    w("")
    if objectives:
        w("WSTG の Test Objectives:")
        w("")
        for o in objectives[:4]:
            w(f"- {o}")
        w("")

    w("## 前提 / スコープ")
    w("")
    w(c.get("scope") or "- 対象: 検査スコープ内のホスト・アプリ")
    if not c.get("scope"):
        w("- 権限: 必要な認証済みアカウント（ロールごとに1つ）")
        w("- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）")
    w("")

    w("## 手順")
    w("")
    steps = c.get("steps") or condense_steps(test.section("how_to_test"))
    steps = [s.replace("OUTDIR", CARD_OUTDIR) for s in steps]
    load_notes = c.get("load_notes") or {}
    if steps:
        for i, s in enumerate(steps, 1):
            w(f"{i}. {s}")
            ln = load_notes.get(i) or load_notes.get(str(i))
            if ln:
                w(f"   > ⚠️ **負荷注意（手順{i}）**: {clean(ln)}")
    else:
        w("1. 原文の How to Test を参照（このカードは要約のみ）")
    w("")

    if load_notes:
        w("## ⚠️ 負荷・レート制限・想定外への注意")
        w("")
        w("本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・"
          "外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・"
          "アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。")
        w("")
        for i in sorted(load_notes, key=lambda k: int(k)):
            w(f"- **手順{i}**: {clean(load_notes[i])}")
        w("")

    w("## 使用ツール")
    w("")
    # 手順に出てきたツールを列挙する（手順＝唯一の真実）。criteria の tools で
    # 明示上書きでき、手順からも活動定義からも拾えない場合だけ活動ツールに退避。
    tools = c.get("tools") or tools_from_steps(steps) or tool_fallback[:8]
    for t in tools:
        w(f"- {t}")
    w("")

    w("## 判定基準（pass / fail の見分け）")
    w("")
    if c.get("pass") or c.get("fail"):
        w(f"- **pass**: {c.get('pass', '（要記入）')}")
        w(f"- **fail**: {c.get('fail', '（要記入）')}")
        if c.get("note"):
            w(f"- 補足: {c['note']}")
    else:
        w("- **pass**: （要記入）`matrix/criteria.yaml` に追記すると次回生成から反映される")
        w("- **fail**: （要記入）")
    w("")

    w("## 記録すべき成果物（run.yaml へ）")
    w("")
    w("- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す")
    w("- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く")
    if outputs:
        seen = list(dict.fromkeys(outputs))[:5]
        w(f"- `artifacts:` — {', '.join(f'`{o}`' for o in seen)}")
    else:
        w("- `artifacts:` — スキャン結果・スクリーンショット・エクスポート")
    w(f"- `covers:` — `{{id: {test.id}, verdict: pass|fail|info|na, finding: 要約, evidence: パス}}`")
    w("")

    w("## カバーするアクティビティ")
    w("")
    if activities:
        for aid in activities:
            title = act_defs.get(aid, {}).get("title", "")
            w(f"- `{aid}` — {title}")
    else:
        w("- （未割当：`matrix/coverage.yaml` にアクティビティを追加すること）")
    w("")
    w(f"原文: {source_url(test.source)}")
    w("")
    return "\n".join(out)


def render_index(tests, by_wstg, act_defs) -> str:
    out = ["# プレイブックカード一覧", "",
           "> 自動生成: `uv run scripts/gen_playbooks.py`", "",
           "1テスト=1枚。社内 Gemini への貼り付け・新人への説明台本にそのまま使える粒度。", ""]
    cat = None
    for t in tests:
        if t.category != cat:
            cat = t.category
            out += ["", f"## {cat} — {t.category_name}", "",
                    "| カード | テスト名 | アクティビティ |", "|---|---|---|"]
        roles = by_wstg.get(t.id, {}) or {}
        acts = list(roles.get("primary", [])) + list(roles.get("secondary", []))
        name = t.title + ("（v4.2 で統合済み）" if t.deprecated else "")
        out.append(f"| [{t.id}]({t.id}.md) | {name} | {', '.join(f'`{a}`' for a in acts) or '—'} |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="指定した WSTG-ID だけ生成する")
    ap.add_argument("--out-dir", default=str(PLAYBOOK_DIR))
    args = ap.parse_args()

    tests = load_tests()
    coverage = load_yaml(COVERAGE_YAML, {}) or {}
    criteria = load_yaml(CRITERIA_YAML, {}) or {}
    act_defs = {a["id"]: a for a in coverage.get("activities", [])}
    by_wstg = coverage.get("by_wstg", {})

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written, missing_criteria = 0, []
    for test in tests:
        if args.only and test.id != args.only:
            continue
        roles = by_wstg.get(test.id, {}) or {}
        activities = list(roles.get("primary", [])) + list(roles.get("secondary", []))
        (out_dir / f"{test.id}.md").write_text(
            render_card(test, criteria, activities, act_defs), encoding="utf-8"
        )
        written += 1
        if not test.deprecated and test.id not in criteria:
            missing_criteria.append(test.id)

    try:
        shown = out_dir.relative_to(REPO_ROOT)
    except ValueError:
        shown = out_dir
    if not args.only:
        (out_dir / "INDEX.md").write_text(render_index(tests, by_wstg, act_defs), encoding="utf-8")
    print(f"{written} 枚のカードを {shown}/ に生成しました。")
    if missing_criteria:
        print(f"判定基準が未記入: {len(missing_criteria)} 件 — matrix/criteria.yaml に追記してください")
        print("  " + ", ".join(missing_criteria))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
