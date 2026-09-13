#!/usr/bin/env python3
"""記入済みの worksheet.md を取り込み、エビデンス（cmd/*.txt と run.yaml）を生成する。

    uv run scripts/capture.py evidence/recon-osint-example.com-20260913

やること:
  1. worksheet.md の各 ```paste ブロックの中身を、宣言された出力パス（cmd/xxx.txt 等）へ保存
  2. run.yaml の commands: に、貼付元のコマンド行・出力パス・取り込み時刻を追記
  3. run.yaml の covers: の verdict / finding / evidence を worksheet の記入で更新

実施者は「ツールを実行して出力を貼る」だけでよく、体裁の揃ったエビデンスが出来上がる。
run.yaml はテキストとして追記・部分置換する（コメント・並び・手記録を壊さない）。
空欄／プレースホルダのままの ```paste は取り込まない（実施した分だけが残る）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from pathlib import Path

VALID_VERDICTS = {"pass", "fail", "info", "na", "todo"}
PLACEHOLDERS = {"", "（ここに出力を貼る）", "（出力を貼る）", "(paste here)"}


def yaml_dq(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def is_empty(content) -> bool:
    if content is None:
        return True
    s = content.strip()
    return s in PLACEHOLDERS


def parse_worksheet(text: str) -> list:
    """worksheet.md を WSTG-ID ごとのセクションに分解する。"""
    lines = text.split("\n")
    sections: list = []
    cur = None
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^###\s+(WSTG-[A-Z]+-\d+)\b", line)
        if m:
            cur = {"id": m.group(1), "cmds": [], "verdict": None, "finding": None}
            sections.append(cur)
            i += 1
            continue
        m = re.match(r"^@cmd\s+(\S+)\s*\|\s*(\S+)", line)
        if m and cur is not None:
            slug, path = m.group(1), m.group(2)
            i += 1
            cmdline = ""
            if i < n and lines[i].startswith("$ "):
                cmdline = lines[i][2:].strip()
                i += 1
            while i < n and lines[i].strip() == "":  # ```paste まで空行を読み飛ばす
                i += 1
            content = None
            if i < n and lines[i].strip().startswith("```"):
                i += 1
                buf = []
                while i < n and not lines[i].strip().startswith("```"):
                    buf.append(lines[i])
                    i += 1
                if i < n:
                    i += 1  # 閉じ ``` を消費
                content = "\n".join(buf)
            cur["cmds"].append({"slug": slug, "path": path, "cmd": cmdline, "content": content})
            continue
        m = re.match(r"^@verdict\s+(\S+)", line)
        if m and cur is not None:
            cur["verdict"] = m.group(1).lower()
            i += 1
            continue
        m = re.match(r"^@finding\b(.*)$", line)
        if m and cur is not None:
            buf = [m.group(1).strip()]
            i += 1
            while i < n and not lines[i].startswith(("@", "###")):
                if lines[i].strip() == "":
                    break
                buf.append(lines[i].strip())
                i += 1
            cur["finding"] = " ".join(x for x in buf if x).strip()
            continue
        i += 1
    return sections


def write_output(dest: Path, cmd: str, content: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    header = [
        f"# captured : {now}",
        f"# command  : {cmd or '（手動/GUI）'}",
        "# source   : worksheet.md 貼付",
        "# " + "-" * 68,
    ]
    dest.write_text("\n".join(header) + "\n" + content.rstrip("\n") + "\n", encoding="utf-8")


def append_commands(run_yaml: Path, entries: list) -> None:
    """run.yaml の commands: 末尾に貼付コマンドを追記する（既存の出力は重複追記しない）。"""
    lines = run_yaml.read_text(encoding="utf-8").split("\n")
    existing = {re.sub(r'^\s*output:\s*', "", l).strip() for l in lines if re.match(r"^\s*output:", l)}
    now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    item: list = []
    for e in entries:
        if e["path"] in existing:
            continue
        item += [
            f"  - cmd: {yaml_dq(e['cmd'] or '（手動/GUI）')}",
            f"    output: {e['path']}",
            f"    captured_at: {yaml_dq(now)}",
            "    source: worksheet",
        ]
    if not item:
        return

    key_idx = next((i for i, l in enumerate(lines) if re.match(r"^commands\s*:", l)), None)
    if key_idx is None:
        lines += ["", "commands:"] + item
    elif re.match(r"^commands\s*:\s*\[\s*\]\s*$", lines[key_idx]):
        lines[key_idx] = "commands:"
        lines[key_idx + 1:key_idx + 1] = item
    else:
        insert_at = last = key_idx
        j = key_idx + 1
        while j < len(lines):
            if lines[j].strip() == "":
                j += 1
                continue
            if lines[j].startswith((" ", "\t")):
                last = j
                j += 1
                continue
            break
        insert_at = last + 1
        lines[insert_at:insert_at] = item
    run_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")


def set_cover(text: str, wid: str, verdict, finding, evidence) -> str:
    """covers: の該当 id ブロックの verdict / finding / evidence を部分置換する。"""
    lines = text.split("\n")
    start = next((i for i, l in enumerate(lines)
                  if re.match(rf"^\s*-\s*id:\s*{re.escape(wid)}(\s|$|#)", l)), None)
    if start is None:
        return text
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\s*-\s*id:\s*WSTG-", lines[j]) or re.match(r"^[A-Za-z_#]", lines[j]):
            end = j
            break
    block = lines[start:end]
    for k, l in enumerate(block):
        indent = re.match(r"^(\s*)", l).group(1)
        if verdict and re.match(r"^\s*verdict:", l):
            block[k] = re.sub(r"(verdict:\s*)\S+", rf"\g<1>{verdict}", l)
        elif finding and re.match(r"^\s*finding:", l):
            block[k] = f"{indent}finding: {yaml_dq(finding)}"
        elif evidence and re.match(r"^\s*evidence:", l):
            block[k] = f"{indent}evidence: {yaml_dq(evidence)}"
    lines[start:end] = block
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("activity_dir", help="evidence/<activity_id>[-<target>]-<yyyymmdd>")
    ap.add_argument("--worksheet", default="worksheet.md", help="取り込むワークシート名（既定: worksheet.md）")
    ap.add_argument("--dry-run", action="store_true", help="書き込まず、取り込む内容だけ表示する")
    args = ap.parse_args()

    activity_dir = Path(args.activity_dir)
    run_yaml = activity_dir / "run.yaml"
    ws = activity_dir / args.worksheet
    if not run_yaml.exists():
        print(f"run.yaml が見つかりません: {run_yaml}", file=sys.stderr)
        print("  uv run scripts/new_activity.py <activity_id> で先に作成してください。", file=sys.stderr)
        return 2
    if not ws.exists():
        print(f"ワークシートが見つかりません: {ws}", file=sys.stderr)
        return 2

    sections = parse_worksheet(ws.read_text(encoding="utf-8"))
    entries: list = []       # commands: へ追記する分
    cover_updates: list = []  # covers: を更新する分
    written = 0

    for sec in sections:
        wid = sec["id"]
        ev_paths: list = []
        for c in sec["cmds"]:
            if is_empty(c["content"]):
                continue
            dest = activity_dir / c["path"]
            if not args.dry_run:
                write_output(dest, c["cmd"], c["content"])
            entries.append({"cmd": c["cmd"], "path": c["path"]})
            ev_paths.append(c["path"])
            written += 1
            print(f"  {'[dry]' if args.dry_run else '保存'}: {c['path']}  ({wid})")
        verdict = sec["verdict"] if sec["verdict"] in VALID_VERDICTS else None
        finding = sec["finding"] or None
        if verdict or finding or ev_paths:
            cover_updates.append((wid, verdict, finding, ", ".join(ev_paths)))

    if args.dry_run:
        for wid, v, f, e in cover_updates:
            print(f"  [dry] covers {wid}: verdict={v or '—'} finding={'有' if f else '—'} evidence={e or '—'}")
        print(f"[capture] dry-run: 出力 {written} 件 / covers 更新 {len(cover_updates)} 件")
        return 0

    if entries:
        append_commands(run_yaml, entries)
    text = run_yaml.read_text(encoding="utf-8")
    for wid, verdict, finding, evidence in cover_updates:
        text = set_cover(text, wid, verdict, finding, evidence)
    run_yaml.write_text(text, encoding="utf-8")

    print(f"[capture] エビデンス {written} 件を保存し、run.yaml を更新しました。")
    print(f"  covers 更新: {len(cover_updates)} 件")
    print(f"  次: uv run scripts/export_checklist.py  で CSV に反映（目視レビュー後に共有）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
