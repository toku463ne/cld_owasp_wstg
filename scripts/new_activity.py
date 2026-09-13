#!/usr/bin/env python3
"""収集アクティビティ用のエビデンスフォルダと run.yaml 雛形を作る。

    uv run scripts/new_activity.py burp-crawl-authn
    uv run scripts/new_activity.py tls-scan --date 20260910 --tester TOKU
    uv run scripts/new_activity.py recon-osint --target example.com   # 複数サイトはこれ

生成物:
    evidence/<activity_id>[-<target>]-<yyyymmdd>/
      run.yaml       covers: を matrix/coverage.yaml から自動プリフィル（verdict: todo）
      worksheet.md   カードのコマンドを埋めた収集ワークシート（出力をここに貼る）
      cmd/           run_cmd.py / capture.py の出力先
      artifacts/     Burp エクスポート・スクショ等。coverage.yaml の outputs にある
                     .md 成果物は検索しやすい雛形（templates/artifacts/）で自動生成
      notes.md

収集フロー（貼付方式）:
    1. worksheet.md の各コマンドを実行し、出力を直後の ```paste ブロックに貼る
    2. 各 WSTG-ID の @verdict / @finding を記入
    3. uv run scripts/capture.py <このフォルダ>  で cmd/*.txt と run.yaml を生成

このスクリプトは evidence/ に「書く」だけで、中身を読み返したり要約したりはしない。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import shlex
from pathlib import Path

import yaml

try:  # スラグ生成は run_cmd.py と共通化する（同じ命名規則にするため）
    from run_cmd import make_slug
except ImportError:  # 直接 import できない実行形態のフォールバック
    def make_slug(command, explicit=None):
        base = re.sub(r"[^A-Za-z0-9._-]+", "-", Path(command[0]).name).strip("-")
        return (base or "cmd")[:48]

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
    "whois", "theharvester", "amass", "nmap", "curl", "wget", "ffuf", "gobuster",
    "sqlmap", "testssl.sh", "sslyze", "nikto", "whatweb", "httpx", "dig", "nslookup",
    "ncat", "nc", "hydra", "dotdotpwn", "wfuzz", "retire", "git-dumper", "aws",
    "padbuster",
}


# GUI 主体のツール（run.yaml の type: を埋めるための当たり）
GUI_TOOLS = {"burp suite", "owasp zap", "wappalyzer", "burp sequencer", "burp intruder",
             "burp collaborator", "burp repeater", "graphql voyager", "inql",
             "ブラウザ開発者ツール", "dom invader", "メールクライアント", "手動レビュー",
             "手動操作", "手動", "ヒアリング", "業務仕様書", "手動 payload"}


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


def extract_commands(steps: list, target: str | None) -> list:
    """手順の `backtick` から、実際に走らせる CLI コマンドだけを抜き出す。

    採用条件: 先頭語が CLI_BINARIES に含まれ、かつ target を参照していること
    （`curl` 単独のような不完全な言及や、dork/ペイロードの backtick を除く）。
    """
    cmds = []
    for step in steps or []:
        for span in re.findall(r"`([^`]+)`", step):
            span = span.strip()
            toks = span.split()
            if not toks:
                continue
            binary = toks[0].split("/")[-1].lower()
            if binary in CLI_BINARIES and "target" in span.lower():
                cmds.append(sub_target(span, target))
    return cmds


def render_worksheet(activity: dict, tests: dict, criteria: dict, target: str | None, date: str) -> str:
    """カードのコマンドを埋めた収集ワークシートを作る（出力をここに貼る）。"""
    tgt = target or "target"
    out = [
        f"# {activity['id']} — {tgt}  収集ワークシート",
        "#",
        "# 使い方:",
        "#   1. 各コマンド（$ 行）を実行し、出力を直後の ```paste ブロックに貼る",
        "#      （target は置換済み。GUI/手動中心のカードはコマンド行が無い）",
        "#   2. 各 WSTG-ID の @verdict（pass|fail|info|na|todo）と @finding を記入",
        f"#   3. uv run scripts/capture.py evidence/{Path(_dir_name(activity, target, date)).name}",
        "#      で cmd/*.txt と run.yaml（commands / covers）を生成する",
        "#",
        f"# activity: {activity['id']}",
        f"# target:   {tgt}",
        "",
    ]
    seen: set = set()
    for cov in activity.get("covers", []):
        wid = cov["id"]
        title = tests.get(wid, {}).get("title", "")
        out.append(f"### {wid} | {title}")
        emitted = False
        used_paths: set = set()
        for cmd in extract_commands(criteria.get(wid, {}).get("steps", []), target):
            if cmd in seen:
                continue
            seen.add(cmd)
            try:
                slug = make_slug(shlex.split(cmd), None)
            except ValueError:
                slug = make_slug([cmd.split()[0]], None)
            path = f"cmd/{slug}.txt"
            n = 2
            while path in used_paths:
                path = f"cmd/{slug}-{n}.txt"
                n += 1
            used_paths.add(path)
            out += [f"@cmd {slug} | {path}", f"$ {cmd}", "```paste", "```", ""]
            emitted = True
        if not emitted:
            out.append("# （CLI コマンドなし＝GUI/手動中心。artifacts/ に手記録し @finding を記入）")
        out += ["@verdict todo", "@finding ", ""]
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
    ap.add_argument("activity_id", help="matrix/coverage.yaml に定義済みの activity_id")
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

    if args.activity_id not in activities:
        print(f"未知の activity_id: {args.activity_id}")
        print("定義済み:")
        for aid, a in activities.items():
            print(f"  {aid:26s} {a.get('title','')}")
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
    worksheet = target_dir / "worksheet.md"
    if not worksheet.exists() or args.force:
        worksheet.write_text(
            render_worksheet(activity, tests, criteria, args.target, args.date), encoding="utf-8"
        )

    covered = ", ".join(c["id"] for c in activity.get("covers", []))
    print(f"作成: {target_dir}")
    print(f"  covers ({len(activity.get('covers', []))} 件): {covered}")
    if stubs:
        print(f"  成果物の雛形: {', '.join(stubs)}")
    print(f"  ワークシート: {worksheet}（コマンド出力を貼る）")
    print(f"  次: worksheet.md に貼付 → uv run scripts/capture.py {target_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
