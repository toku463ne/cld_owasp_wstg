#!/usr/bin/env python3
"""収集アクティビティ用のエビデンスフォルダと run.yaml 雛形を作る。

    uv run scripts/new_activity.py burp-crawl-authn
    uv run scripts/new_activity.py tls-scan --date 20260910 --tester TOKU
    uv run scripts/new_activity.py recon-osint --target example.com   # 複数サイトはこれ

生成物:
    evidence/<activity_id>[-<target>]-<yyyymmdd>/
      run.yaml       covers: を matrix/coverage.yaml から自動プリフィル（verdict: todo）。
                     判定（verdict/finding）はこの covers に直接書く（唯一の判定置き場）
      record.html    実施記録の表示ビューア（静的）。中身は evidence.js から読み込む
      evidence.js    表示用データ（run_activity.py / gen_record.py が生成・更新する）
      cmd/           run_activity.py / run_cmd.py が実行したコマンドの出力（＝純粋なエビデンス）
      artifacts/     ツールの出力ファイル・スクショ・Burp エクスポート、および手動手順の
                     観察を書く manual-<WSTG-ID>-s<n>.txt（手順の OUTDIR はここに置換される）。
                     coverage.yaml の outputs の .md 成果物は雛形（templates/artifacts/）で自動生成
      notes.md

収集フロー:
    1. uv run scripts/run_activity.py <このフォルダ>       # コマンド手順を実行→cmd/ に純粋なエビデンス
    2. 手動手順は artifacts/manual-*.txt に観察を書く（Burp・ヒアリング等）
    3. run.yaml の covers に verdict / finding を直接記入する（要約のみ。生値は evidence: で参照）
    4. uv run scripts/gen_record.py <このフォルダ>        # record.html を最新化
    5. uv run scripts/export_checklist.py                 # run.yaml → CSV（目視レビュー後に共有）

エビデンス本体は cmd/・artifacts/ の各ファイル。record.html はそれを読むだけの表示なので、
上流（criteria.yaml 等）を更新して手順が変わっても、gen_record.py で作り直せばよく、
過去のエビデンスを別ファイルからコピーし直す必要がない。
このスクリプトは evidence/ に「書く」だけで、中身を読み返したり要約したりはしない。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_YAML = REPO_ROOT / "matrix" / "coverage.yaml"
WSTG_TESTS = REPO_ROOT / "matrix" / "wstg_tests.yaml"
CRITERIA_YAML = REPO_ROOT / "matrix" / "criteria.yaml"
# .md 成果物の雛形置き場。<basename> 専用の雛形が無ければ _findings.md を使う。
ARTIFACT_TEMPLATES = REPO_ROOT / "templates" / "artifacts"

# 手順の `backtick` から「実際に走らせるコマンド」を拾うための CLI バイナリ集合。
# GUI（Burp 等）は対象外。判定は「先頭語が CLI で、かつ target を参照している」こと
# （`curl` 単独のような不完全な言及を除くため）。
CLI_BINARIES = {
    "whois", "theharvester", "amass", "subfinder", "nmap", "curl", "wget",
    "ffuf", "gobuster",
    "sqlmap", "testssl.sh", "sslyze", "nikto", "whatweb", "httpx", "dig", "nslookup", "traceroute",
    "ncat", "nc", "hydra", "dotdotpwn", "wfuzz", "retire", "git-dumper", "aws",
    "padbuster", "grep", "jq",
}


# GUI 主体のツール（run.yaml の type: を埋めるための当たり）
GUI_TOOLS = {"burp suite", "owasp zap", "wappalyzer", "burp sequencer", "burp intruder",
             "burp collaborator", "burp repeater", "graphql voyager", "inql",
             "ブラウザ開発者ツール", "dom invader", "メールクライアント", "手動レビュー",
             "手動操作", "手動", "ヒアリング", "業務仕様書", "手動 payload"}


# record.html は静的なビューア（表示専用）。生のエビデンスは cmd/・artifacts/ に置き、
# 中身は同フォルダの evidence.js（run_activity.py / gen_record.py が生成）から読み込む。
# file:// で開くと .txt の fetch はブラウザに遮断されるため、<script src> でデータを渡す。
RECORD_HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>実施記録</title>
<style>
  :root { --bg:#fff; --fg:#1a1a1a; --mut:#666; --line:#e2e2e2; --card:#fafafa;
          --pre:#f4f4f4; --cmd:#0b3d2e; --cmdbg:#eaf5ef; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#16181c; --fg:#e6e6e6; --mut:#9aa0a6; --line:#2c2f36; --card:#1d2026;
            --pre:#111318; --cmd:#8fe3c0; --cmdbg:#12251d; } }
  * { box-sizing:border-box; }
  body { margin:0; padding:24px 16px 80px; background:var(--bg); color:var(--fg);
         font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans JP",sans-serif;
         line-height:1.6; max-width:960px; margin-inline:auto; }
  h1 { font-size:1.4rem; margin:0 0 4px; }
  .meta { color:var(--mut); font-size:.85rem; margin-bottom:20px; }
  .item { border:1px solid var(--line); border-radius:10px; padding:16px 18px;
          margin:18px 0; background:var(--card); }
  .item h2 { font-size:1.05rem; margin:0 0 8px; display:flex; gap:10px; align-items:center;
             flex-wrap:wrap; }
  .badge { font-size:.72rem; font-weight:700; padding:2px 8px; border-radius:999px;
           border:1px solid var(--line); white-space:nowrap; }
  .v-pass{background:#e7f6ec;color:#0a7c33;border-color:#bfe6cd;}
  .v-fail{background:#fdeaea;color:#c62828;border-color:#f3bcbc;}
  .v-info{background:#eaf2fd;color:#1565c0;border-color:#bcd6f3;}
  .v-na{background:#eee;color:#666;}
  .v-todo{background:#fff5e6;color:#b26a00;border-color:#f0d9ad;}
  .role{color:var(--mut);font-weight:600;}
  .k-manual{background:#fff5e6;color:#b26a00;border-color:#f0d9ad;}
  .k-cmd{background:#eaf5ef;color:#0b6b47;border-color:#c2e6d6;}
  .crit{font-size:.85rem;color:var(--mut);margin:2px 0;}
  .crit b{color:var(--fg);}
  .finding{margin:8px 0 0;padding:8px 10px;border-left:3px solid var(--line);
           background:var(--pre);border-radius:0 6px 6px 0;font-size:.9rem;}
  .step{margin:14px 0 0;padding-top:10px;border-top:1px dashed var(--line);}
  .step .t{font-size:.9rem;margin:0 0 6px;}
  pre{margin:6px 0;padding:10px 12px;border-radius:8px;overflow:auto;
      font:.82rem/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
      white-space:pre-wrap;word-break:break-word;}
  pre.cmd{background:var(--cmdbg);color:var(--cmd);}
  pre.out{background:var(--pre);}
  .rc{font-size:.78rem;color:var(--mut);}
  .rc.bad{color:#c62828;font-weight:700;}
  .empty{color:var(--mut);font-style:italic;font-size:.85rem;}
  .warn{color:#b26a00;}
</style>
</head>
<body>
<div id="app"><p class="empty">evidence.js を読み込んでいます…</p></div>
<script src="evidence.js"></script>
<script>
(function () {
  var app = document.getElementById("app");
  var d = window.WSTG_EVIDENCE;
  function el(tag, cls, txt) { var e = document.createElement(tag);
    if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }
  if (!d) { app.innerHTML = "";
    app.appendChild(el("p", "warn",
      "evidence.js が見つかりません。uv run scripts/gen_record.py <このフォルダ> で生成してください。"));
    return; }
  app.innerHTML = "";
  app.appendChild(el("h1", null, "実施記録 — " + d.activity_id + (d.target ? " / " + d.target : "")));
  var meta = el("div", "meta",
    [d.title, d.date && ("date " + d.date), d.tester && ("tester " + d.tester),
     d.generated_at && ("生成 " + d.generated_at)].filter(Boolean).join("  ·  "));
  app.appendChild(meta);

  (d.items || []).forEach(function (it) {
    var box = el("div", "item");
    var h = el("h2");
    h.appendChild(el("span", null, it.wid));
    if (it.title) h.appendChild(el("span", "role", it.title));
    h.appendChild(el("span", "badge v-" + (it.verdict || "todo"), (it.verdict || "todo").toUpperCase()));
    h.appendChild(el("span", "role", it.role));
    box.appendChild(h);
    if (it.purpose) box.appendChild(el("div", "crit", "目的: " + it.purpose));
    if (it.pass) { var cp = el("div", "crit"); cp.appendChild(el("b", null, "pass ")); 
      cp.appendChild(document.createTextNode(it.pass)); box.appendChild(cp); }
    if (it.fail) { var cf = el("div", "crit"); cf.appendChild(el("b", null, "fail "));
      cf.appendChild(document.createTextNode(it.fail)); box.appendChild(cf); }
    if (it.finding) box.appendChild(el("div", "finding", "finding: " + it.finding));

    (it.steps || []).forEach(function (st) {
      var s = el("div", "step");
      var t = el("p", "t");
      t.appendChild(el("span", "badge k-" + st.kind, st.kind === "cmd" ? "コマンド" : "手動"));
      t.appendChild(document.createTextNode(" 手順" + st.idx + "： " + st.text));
      s.appendChild(t);
      if (st.commands && st.commands.length) {
        var pc = el("pre", "cmd", st.commands.map(function (c) { return "$ " + c; }).join("\n"));
        s.appendChild(pc);
      }
      if (st.output && st.output.trim()) {
        s.appendChild(el("pre", "out", st.output + (st.truncated ? "\n…(以下略。全文は " + st.output_path + ")" : "")));
        var rc = el("div", (st.exit_code ? "rc bad" : "rc"),
          "→ " + st.output_path + (st.exit_code != null ? "  (exit " + st.exit_code + ")" : "")
          + (st.ran_at ? "  " + st.ran_at : ""));
        s.appendChild(rc);
      } else {
        s.appendChild(el("p", "empty", st.kind === "cmd"
          ? "未実行（uv run scripts/run_activity.py でこの手順を実行）"
          : "未記入（" + st.output_path + " に観察を書く）"));
      }
      box.appendChild(s);
    });
    app.appendChild(box);
  });
})();
</script>
</body>
</html>
"""


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"{path} がありません。scripts/build_wstg_index.py などを先に実行してください。")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _yaml_str(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def iso_date(yyyymmdd: str) -> str:
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}" if len(yyyymmdd) == 8 else yyyymmdd


def sub_target(text: str, target: str | None) -> str:
    """手順・コマンド中の target プレースホルダを実対象に置換する。"""
    if not target:
        return text
    text = text.replace("target.co.jp", target)
    return re.sub(r"\btarget\b", target, text)


def sub_outdir(text: str, act_dir: str) -> str:
    """手順の OUTDIR プレースホルダを、この実施の artifacts/ の実パスに置換する。

    ツールが吐くファイルをエビデンスフォルダの外に散らかさないための置換。
    コマンドはリポジトリルートから実行する前提のパスにする。
    """
    return text.replace("OUTDIR", f"{act_dir}/artifacts")


# for/while ループ（複数サブドメインを一括処理する等）を1つの実行コマンドとして拾う。
# 先頭が for/while で、ループ本体に CLI バイナリが現れ、target か OUTDIR を参照するもの。
LOOP_KEYWORDS = {"for", "while"}


def extract_commands(steps: list, target: str | None) -> list:
    """手順の `backtick` から、実際に走らせる CLI コマンドだけを抜き出す。

    採用条件（いずれか）:
      - 先頭語が CLI_BINARIES に含まれ、かつ target か OUTDIR（＝出力先）を参照している
        （`curl` 単独のような不完全な言及や、dork/ペイロードの backtick を除く。
        OUTDIR を書く grep 等の後処理コマンドもここで拾う）
      - 先頭語が for/while のループで、本体に CLI バイナリが現れ、
        target か OUTDIR（＝出力先）を参照している（サブドメインの一括処理など）
    """
    cmds = []
    for step in steps or []:
        for span in re.findall(r"`([^`]+)`", step):
            span = span.strip()
            toks = span.split()
            if not toks:
                continue
            low = span.lower()
            binary = toks[0].split("/")[-1].lower()
            if binary in CLI_BINARIES and ("target" in low or "OUTDIR" in span):
                cmds.append(sub_target(span, target))
            elif binary in LOOP_KEYWORDS and ("target" in low or "OUTDIR" in span) \
                    and any(re.search(rf"\b{re.escape(b)}\b", low) for b in CLI_BINARIES):
                cmds.append(sub_target(span, target))
    return cmds


# 確認コマンドを足さない出力先（バイナリ・画像など先頭を出しても意味がないもの）
_BINARY_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".pcap")


def output_paths(cmd: str, act_dir: str) -> list:
    """コマンドが artifacts/ に書き出すファイルのパスを拾う。

    `-o path` / `-oN path` / `> path` はパスがそのまま出てくる。
    `mv a.xml a.json OUTDIR/` のようにディレクトリだけ指定する形は、
    その `mv`/`cp` の引数に出てくるファイル名と結合する（target に付いた
    ドメイン名などを拾わないよう、探す範囲は mv/cp 以降に限る）。
    """
    prefix = f"{act_dir}/artifacts/"
    toks = [tok.strip("'\"") for tok in cmd.split()]
    paths = []
    for i, tok in enumerate(toks):
        if not tok.startswith(prefix):
            continue
        if not tok.endswith("/"):
            paths.append(tok)
            continue
        # 直前の mv/cp までさかのぼり、その引数のファイル名を移動先に結合する
        head = next((j for j in range(i - 1, -1, -1)
                     if toks[j] in ("mv", "cp")), None)
        if head is None:
            continue
        for name in toks[head + 1:i]:
            if name.startswith("-") or "/" in name:
                continue
            if re.search(r"\.[A-Za-z0-9]{1,6}$", name):
                paths.append(tok + name)
    # 重複排除（順序は維持）。中身を覗いても意味が無いものは確認対象から外す
    seen, uniq = set(), []
    for path in paths:
        if path not in seen and not path.lower().endswith(_BINARY_SUFFIXES):
            seen.add(path)
            uniq.append(path)
    return uniq


def verify_commands(cmd: str, act_dir: str) -> list:
    """出力ファイルが「ちゃんと取れているか」を確認するコマンドを組み立てる。

    -s で黙るコマンド（curl 等）は「結果:」に貼るものが無くなり、失敗と
    「何も無い」の区別がつかなくなる。行数と先頭を必ず出させる。
    """
    checks = []
    for path in output_paths(cmd, act_dir):
        if path.lower().endswith((".json", ".xml", ".html")):
            checks.append(f"ls -l {path}; head -c 400 {path}; echo")
        else:
            checks.append(f"wc -l {path}; head -5 {path}")
    return checks


# ---- 実施記録の中身（手順の平坦リスト）: 生成・実行・表示で共有する唯一の定義 ----

def iter_steps(activity: dict, criteria: dict, target, act_dir: str) -> list:
    """アクティビティの手順を WSTG-ID 順・手順番号順に平らに並べて返す。

    record.html / evidence.js の生成（gen_record.py）と wrapper 実行（run_activity.py）が
    同じ手順・同じ出力パスを共有するための唯一の定義。1手順 = 1エビデンスファイル:
      - コマンド手順 … `cmd/<WSTG-ID>-s<n>.txt`（wrapper が実行して出力を保存）
      - 手動手順     … `artifacts/manual-<WSTG-ID>-s<n>.txt`（人が観察を書く）
    OUTDIR / target は act_dir の実パス・対象に置換済みで返す。
    """
    out = []
    for cov in activity.get("covers", []):
        wid = cov["id"]
        crit = criteria.get(wid, {})
        for idx, step in enumerate(crit.get("steps", []), 1):
            cmds = [sub_outdir(cmd, act_dir) for cmd in extract_commands([step], target)]
            checks = []
            for cmd in cmds:
                for chk in verify_commands(cmd, act_dir):
                    if chk not in checks:
                        checks.append(chk)
            out.append({
                "wid": wid,
                "role": cov.get("role", "primary"),
                "idx": idx,
                "text": sub_outdir(sub_target(step, target), act_dir),
                "kind": "cmd" if cmds else "manual",
                "commands": cmds,
                "checks": checks,
                "output": (f"cmd/{wid}-s{idx}.txt" if cmds
                           else f"artifacts/manual-{wid}-s{idx}.txt"),
            })
    return out


def manual_stub_text(activity: dict, step: dict) -> str:
    """手動手順の観察を書き込むための素の .txt ひな型（これ自体がエビデンス）。"""
    return "\n".join([
        f"# {activity['id']} / {step['wid']} 手順{step['idx']}（手動）",
        f"# 手順: {step['text']}",
        "# 貼るもの: ① 操作した URL とクリック手順 ② 確認できたこと（無ければ「該当なし」）",
        "#           ③ スクショのパス（artifacts/*.png） ④ 件数・該当箇所",
        "# " + "-" * 68,
        "",
    ]) + "\n"


def _load_run_yaml(activity_dir: Path) -> dict:
    """run.yaml を読み込む（表示用の読み取り専用。書き戻しはしない）。"""
    rp = activity_dir / "run.yaml"
    return yaml.safe_load(rp.read_text(encoding="utf-8")) if rp.exists() else {}


# エビデンスファイルは大きくなり得るので、表示用データには先頭だけ載せる（本体は .txt を見る）
EVIDENCE_MAX_CHARS = 20000


def build_evidence(activity: dict, tests: dict, criteria: dict, target,
                   activity_dir: Path, act_dir: str) -> dict:
    """run.yaml（判定・コマンド記録）と各手順の出力ファイルから、表示用データを組む。"""
    run = _load_run_yaml(activity_dir)
    covers = {c["id"]: c for c in (run.get("covers") or [])}
    # commands: の各エントリを output（相対パス）で引けるようにする（最後の実行を採用）
    by_output: dict = {}
    for cmd in run.get("commands") or []:
        if isinstance(cmd, dict) and cmd.get("output"):
            by_output[cmd["output"]] = cmd

    items: list = []
    grouped: dict = {}
    for step in iter_steps(activity, criteria, target, act_dir):
        grouped.setdefault(step["wid"], []).append(step)

    for cov in activity.get("covers", []):
        wid = cov["id"]
        crit = criteria.get(wid, {})
        cv = covers.get(wid, {})
        steps_out = []
        for step in grouped.get(wid, []):
            fpath = activity_dir / step["output"]
            content, truncated = "", False
            if fpath.exists():
                raw = fpath.read_text(encoding="utf-8", errors="replace")
                content = raw[:EVIDENCE_MAX_CHARS]
                truncated = len(raw) > EVIDENCE_MAX_CHARS
            rec = by_output.get(step["output"], {})
            steps_out.append({
                "idx": step["idx"],
                "kind": step["kind"],
                "text": step["text"],
                "commands": step["commands"] + step["checks"],
                "output_path": step["output"],
                "output": content,
                "truncated": truncated,
                "exit_code": rec.get("exit_code"),
                "ran_at": rec.get("started_at"),
            })
        items.append({
            "wid": wid,
            "title": tests.get(wid, {}).get("title", ""),
            "role": cov.get("role", "primary"),
            "purpose": crit.get("purpose", ""),
            "pass": crit.get("pass", ""),
            "fail": crit.get("fail", ""),
            "verdict": cv.get("verdict", "todo"),
            "finding": cv.get("finding", ""),
            "evidence": cv.get("evidence", ""),
            "steps": steps_out,
        })

    return {
        "activity_id": activity["id"],
        "title": activity.get("title", ""),
        "target": target or "",
        "date": str(run.get("date", "")),   # run.yaml では既に ISO 文字列（PyYAML が date 化する）
        "tester": run.get("tester", ""),
        "generated_at": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "items": items,
    }


def write_evidence_js(activity_dir: Path, data: dict) -> Path:
    """evidence.js を書き出す（record.html が <script src> で読み込むデータ）。"""
    import json
    path = activity_dir / "evidence.js"
    path.write_text(
        "// 自動生成: scripts/run_activity.py / scripts/gen_record.py が更新する。\n"
        "// 生のエビデンスは cmd/ ・ artifacts/ の各ファイル。ここはその表示用コピー。\n"
        "window.WSTG_EVIDENCE = "
        + json.dumps(data, ensure_ascii=False, indent=2) + ";\n",
        encoding="utf-8",
    )
    return path


def write_record_html(activity_dir: Path, force: bool = False) -> Path:
    """record.html（表示専用ビューア）を書き出す。中身は evidence.js から読む。"""
    path = activity_dir / "record.html"
    if path.exists() and not force:
        return path
    path.write_text(RECORD_HTML, encoding="utf-8")
    return path


def _act_dir_str(target_dir: Path) -> str:
    """コマンド中の OUTDIR を置き換える基準パス（リポジトリ内なら相対、外は絶対）。"""
    try:
        return target_dir.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return target_dir.as_posix()


def resolve_activity(activity_dir: Path):
    """run.yaml を起点に (activity, tests, criteria, target, act_dir) を引く。

    run_activity.py / gen_record.py が既存フォルダを扱うための入口。
    """
    run = _load_run_yaml(activity_dir)
    aid = run.get("activity_id")
    if not aid:
        raise SystemExit(f"run.yaml に activity_id がありません: {activity_dir / 'run.yaml'}\n"
                         "  uv run scripts/new_activity.py <activity_id> で作り直してください。")
    coverage = load_yaml(COVERAGE_YAML)
    activities = {a["id"]: a for a in coverage["activities"]}
    if aid not in activities:
        raise SystemExit(f"未知の activity_id: {aid}（coverage.yaml に定義がありません）")
    tests = {t["id"]: t for t in load_yaml(WSTG_TESTS)["tests"]}
    criteria = load_yaml(CRITERIA_YAML) if CRITERIA_YAML.exists() else {}
    target = run.get("target_scope") or None
    return activities[aid], tests, criteria, target, _act_dir_str(activity_dir)


def refresh_record(activity_dir: Path) -> dict:
    """実行はせず、run.yaml と既存のエビデンスから record.html / evidence.js を最新化する。"""
    activity, tests, criteria, target, act_dir = resolve_activity(activity_dir)
    write_manual_stubs(activity, criteria, target, activity_dir, act_dir, force=False)
    write_record_html(activity_dir, force=False)
    data = build_evidence(activity, tests, criteria, target, activity_dir, act_dir)
    write_evidence_js(activity_dir, data)
    return data


def write_manual_stubs(activity: dict, criteria: dict, target,
                       activity_dir: Path, act_dir: str, force: bool) -> list:
    """手動手順の観察を書くための .txt ひな型を用意する（既存は壊さない）。"""
    made = []
    for step in iter_steps(activity, criteria, target, act_dir):
        if step["kind"] != "manual":
            continue
        dest = activity_dir / step["output"]
        if dest.exists() and not force:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(manual_stub_text(activity, step), encoding="utf-8")
        made.append(step["output"])
    return made


    return "\n".join(out) + "\n"


def _dir_name(activity: dict, target: str | None, date: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", target).strip("-") if target else ""
    stem = f"{activity['id']}-{safe}" if safe else activity["id"]
    return f"{stem}-{date}"


def render_run_yaml(activity: dict, tests: dict, date: str, tester: str, target: str | None = None) -> str:
    scope = _yaml_str(target) if target else '""'
    lines = [
        f"# {activity['id']} — {activity.get('title', '')}",
        "# finding は要約のみ。生トークン・資格情報・生ホスト名は書かず evidence: で参照する。",
        f"activity_id: {activity['id']}",
        f"title: {_yaml_str(activity.get('title', ''))}",
        f"date: {iso_date(date)}",
        f"tester: {tester}",
        f"target_scope: {scope}   # 対象の識別子（エイリアス可）",
        "",
        "tools:",
    ]
    for tool in activity.get("tools", []) or ["（使用ツール）"]:
        kind = "gui" if tool.strip().lower() in GUI_TOOLS else "cli"
        lines.append(f"  - name: {_yaml_str(tool)}")
        lines.append('    version: ""')
        lines.append(f"    type: {kind}          # cli | gui")

    lines += [
        "",
        "# CLI: scripts/run_cmd.py が自動追記する",
        "commands: []",
        "",
        "# GUI ツールの操作は手記録（再現メモ）",
        "steps: []",
        "",
        "# 判定: pass | fail | info | na | todo",
        "covers:",
    ]
    for cov in activity.get("covers", []):
        wid = cov["id"]
        test = tests.get(wid, {})
        role = cov.get("role", "primary")
        note = f"  # {cov['note']}" if cov.get("note") else ""
        lines.append(f"  - id: {wid}{note}")
        lines.append(f"    # {role}: {test.get('title', '')}")
        lines.append("    verdict: todo")
        lines.append('    finding: ""')
        lines.append('    evidence: ""')

    if activity.get("outputs"):
        lines += ["", "# 想定成果物: " + ", ".join(activity["outputs"])]
    return "\n".join(lines) + "\n"


def render_artifact(tmpl_text: str, activity: dict, date: str, basename: str) -> str:
    """.md 成果物の雛形にアクティビティ情報を差し込む（検索用の見出し・行を用意）。"""
    ids = [c["id"] for c in activity.get("covers", [])]
    rows = "\n".join(f"| {i} | todo |  |  | [info] |  |" for i in ids) \
        or "|  | todo |  |  | [info] |  |"
    repl = {
        "{{basename}}": basename,
        "{{activity_id}}": activity["id"],
        "{{title}}": activity.get("title", ""),
        "{{date}}": iso_date(date),
        "{{wstg_ids}}": ", ".join(ids) or "—",
        "{{rows}}": rows,
    }
    for key, val in repl.items():
        tmpl_text = tmpl_text.replace(key, val)
    return tmpl_text


def write_artifact_stubs(activity: dict, target: Path, date: str, force: bool) -> list:
    """coverage.yaml の outputs にある .md 成果物を、検索しやすい雛形で用意する。

    <basename> 専用の雛形（templates/artifacts/<basename>）があればそれを、
    無ければ汎用の _findings.md を使う。どちらも無ければ何もしない。
    notes.md はトップに別途生成するのでここでは扱わない。
    """
    created = []
    for out in activity.get("outputs", []) or []:
        if not out.endswith(".md"):
            continue
        name = Path(out).name
        if name == "notes.md":
            continue
        dest = target / out
        if dest.exists() and not force:
            continue
        tmpl = ARTIFACT_TEMPLATES / name
        if not tmpl.exists():
            tmpl = ARTIFACT_TEMPLATES / "_findings.md"
        if not tmpl.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            render_artifact(tmpl.read_text(encoding="utf-8"), activity, date, name),
            encoding="utf-8",
        )
        created.append(out)
    return created


def render_notes(activity: dict, date: str) -> str:
    return "\n".join(
        [
            f"# {activity['id']} — {activity.get('title', '')} ({iso_date(date)})",
            "",
            activity.get("summary", ""),
            "",
            "## 実施メモ",
            "",
            "- ",
            "",
            "## 気づき・次にやること",
            "",
            "- ",
            "",
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("activity_id", nargs="?",
                    help="matrix/coverage.yaml に定義済みの activity_id（省略すると一覧を表示）")
    ap.add_argument("--date", default=_dt.date.today().strftime("%Y%m%d"), help="yyyymmdd（既定: 今日）")
    ap.add_argument("--tester", default="TOKU")
    ap.add_argument("--target", help="対象サイト（複数サイト時。フォルダ名とコマンドの target 置換に使う）")
    ap.add_argument("--root", default=str(REPO_ROOT / "evidence"), help="出力先ルート（既定: evidence/）")
    ap.add_argument("--force", action="store_true", help="既存フォルダがあっても run.yaml 以外を作り直す")
    args = ap.parse_args()

    coverage = load_yaml(COVERAGE_YAML)
    tests = {t["id"]: t for t in load_yaml(WSTG_TESTS)["tests"]}
    criteria = load_yaml(CRITERIA_YAML) if CRITERIA_YAML.exists() else {}
    activities = {a["id"]: a for a in coverage["activities"]}

    def print_activities() -> None:
        print(f"定義済みアクティビティ {len(activities)} 本（引数に渡す ID）:")
        for aid, a in activities.items():
            print(f"  {aid:26s} {a.get('title','')}")
        print("\n例: uv run scripts/new_activity.py recon-osint --target example.com")

    if not args.activity_id:  # 引数なし＝一覧表示（何を実施できるかの確認用）
        print_activities()
        return 0

    if args.activity_id not in activities:
        print(f"未知の activity_id: {args.activity_id}\n")
        print_activities()
        return 2

    activity = activities[args.activity_id]
    target_dir = Path(args.root) / _dir_name(activity, args.target, args.date)
    run_yaml = target_dir / "run.yaml"

    if run_yaml.exists() and not args.force:
        print(f"既に存在します: {run_yaml}（上書きしません）")
        return 1

    for sub in ("cmd", "artifacts"):
        (target_dir / sub).mkdir(parents=True, exist_ok=True)
    run_yaml.write_text(
        render_run_yaml(activity, tests, args.date, args.tester, args.target), encoding="utf-8"
    )
    notes = target_dir / "notes.md"
    if not notes.exists():
        notes.write_text(render_notes(activity, args.date), encoding="utf-8")
    stubs = write_artifact_stubs(activity, target_dir, args.date, args.force)
    # 記録に載せるパス。リポジトリ内なら相対（evidence/...）、外（--root で一時
    # ディレクトリ等）ならそのままのパスにする。リポジトリルートから実行できること。
    try:
        act_dir = target_dir.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        act_dir = target_dir.as_posix()

    # 手動手順の観察を書く .txt ひな型・表示ビューア・表示データを用意する。
    # 生のエビデンスは cmd/・artifacts/ の各ファイル。record.html はそれを読むだけ。
    manual = write_manual_stubs(activity, criteria, args.target, target_dir, act_dir, args.force)
    write_record_html(target_dir, force=args.force)
    write_evidence_js(
        target_dir,
        build_evidence(activity, tests, criteria, args.target, target_dir, act_dir),
    )

    covered = ", ".join(c["id"] for c in activity.get("covers", []))
    print(f"作成: {target_dir}")
    print(f"  covers ({len(activity.get('covers', []))} 件): {covered}")
    if stubs:
        print(f"  成果物の雛形: {', '.join(stubs)}")
    if manual:
        print(f"  手動手順のひな型: {len(manual)} 件（artifacts/manual-*.txt に観察を書く）")
    print(f"  実施記録ビューア: {target_dir / 'record.html'}（evidence.js を読み込む）")
    print(f"  実行: uv run scripts/run_activity.py {target_dir}"
          "  でコマンド手順を実行→エビデンスと evidence.js を更新")
    print(f"  判定: {run_yaml} の covers に verdict / finding を直接記入し、"
          f"uv run scripts/gen_record.py {target_dir} で record.html を更新")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
