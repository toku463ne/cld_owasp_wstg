#!/usr/bin/env python3
"""記入済みの record.md（実施記録）を取り込み、run.yaml の判定を更新する。

    uv run scripts/capture.py evidence/recon-osint-example.com-20260913

record.md には手順ごとの結果（コマンド出力・画面の観察）が Q&A 形式で貼ってある。
このファイル自体がエビデンス本体なので、ここでは中身を分解・コピーはしない。
やることは「WSTG-ID ごとの @verdict / @finding を run.yaml の covers: に転記する」だけ:

  - 各 `## WSTG-XXX | ...` セクション（旧形式の `=== ... ===` も可）の @verdict と @finding を読む
  - run.yaml の covers: の該当 id ブロックの verdict / finding / evidence 行を部分置換する
    （evidence にはこの record.md のパスを入れ、raw はそこを見れば分かるようにする）

run.yaml はテキストとして部分置換する（コメント・並び・手記録を壊さない）。
finding は要約のみ。生トークン・資格情報・生ホスト名は record.md 側にだけ残し、ここには写さない。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

VALID_VERDICTS = {"pass", "fail", "info", "na", "todo"}


def yaml_dq(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def parse_record(text: str) -> list:
    """record.md を WSTG-ID ごとの (id, verdict, finding, results_written) に分解する。

    セクション見出しは `## WSTG-XXX | ...`（旧 `=== WSTG-XXX | ... ===` も受ける）。
    """
    lines = text.split("\n")
    sections: list = []
    cur = None
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        m = re.match(r"^(?:#{1,6}|===)\s+(WSTG-[A-Z]+-\d+)\b", line)
        if m:
            cur = {"id": m.group(1), "verdict": None, "finding": None, "results": 0}
            sections.append(cur)
            i += 1
            continue
        if cur is not None and line.strip() == "結果:":
            # 直後の ``` ブロックに中身が貼られているか数える（記入状況の把握用）
            j = i + 1
            if j < n and lines[j].strip().startswith("```"):
                j += 1
                body = []
                while j < n and not lines[j].strip().startswith("```"):
                    body.append(lines[j])
                    j += 1
                if "".join(body).strip():
                    cur["results"] += 1
                i = j + 1 if j < n else j
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
            while i < n and not lines[i].startswith(("@", "===", "#")):
                if lines[i].strip() == "":
                    break
                buf.append(lines[i].strip())
                i += 1
            cur["finding"] = " ".join(x for x in buf if x).strip()
            continue
        i += 1
    return sections


def set_cover(text: str, wid: str, verdict, finding, evidence) -> str:
    """covers: の該当 id ブロックの verdict / finding / evidence 行だけを部分置換する。"""
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
    ap.add_argument("--record", default="record.md", help="取り込む実施記録名（既定: record.md）")
    ap.add_argument("--dry-run", action="store_true", help="書き込まず、取り込む内容だけ表示する")
    args = ap.parse_args()

    activity_dir = Path(args.activity_dir)
    run_yaml = activity_dir / "run.yaml"
    record = activity_dir / args.record
    if not run_yaml.exists():
        print(f"run.yaml が見つかりません: {run_yaml}", file=sys.stderr)
        print("  uv run scripts/new_activity.py <activity_id> で先に作成してください。", file=sys.stderr)
        return 2
    if not record.exists():
        print(f"実施記録が見つかりません: {record}", file=sys.stderr)
        return 2

    sections = parse_record(record.read_text(encoding="utf-8"))
    rel = args.record  # covers の evidence にはフォルダ内相対パスを入れる
    updates = []
    for sec in sections:
        verdict = sec["verdict"] if sec["verdict"] in VALID_VERDICTS else None
        finding = sec["finding"] or None
        # 何か記入されている（判定 or 所見 or 結果あり）セクションだけ反映
        if verdict in (None, "todo") and not finding and sec["results"] == 0:
            continue
        updates.append((sec["id"], verdict, finding, rel))

    if not updates:
        print("[capture] record.md にまだ記入がありません（@verdict / @finding / 結果を埋めてください）。")
        return 0

    # 「結果は貼ったが @verdict が todo のまま」は更新対象に入るが run.yaml は変わらない。
    # 件数をまとめて出すと「反映済み」に見えてしまうので、未記入は分けて出す。
    pending = [wid for wid, verdict, finding, _ in updates
               if verdict in (None, "todo") and not finding]
    for wid, verdict, finding, ev in updates:
        if wid in pending:
            print(f"  {wid}: 判定未記入（結果のみ）")
        else:
            print(f"  {wid}: verdict={verdict or 'todo'}  finding={'有' if finding else '—'}")

    if args.dry_run:
        print(f"[capture] dry-run: covers {len(updates)} 件を反映予定"
              f"（うち判定未記入 {len(pending)} 件）")
        return 0

    original = run_yaml.read_text(encoding="utf-8")
    text = original
    for wid, verdict, finding, ev in updates:
        text = set_cover(text, wid, verdict, finding, ev)
    if text != original:
        run_yaml.write_text(text, encoding="utf-8")

    decided = [wid for wid, *_ in updates if wid not in pending]
    if decided:
        print(f"[capture] run.yaml の covers を {len(decided)} 件更新しました（evidence → {rel}）。")
    elif text != original:
        print(f"[capture] 転記する判定はありません（evidence → {rel} を記録しただけです）。")
    else:
        print("[capture] run.yaml に変更はありませんでした。")
    if pending:
        print(f"  判定未記入: {', '.join(pending)}")
        print(f"  → {record} の各 WSTG-ID 末尾の @verdict（pass|fail|info|na）と @finding を記入して、"
              "もう一度実行してください（todo のままでは CSV も未実施のままです）。")
    if decided:
        print("  次: uv run scripts/export_checklist.py  で CSV に反映（目視レビュー後に共有）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
