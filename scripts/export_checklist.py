#!/usr/bin/env python3
"""全 evidence/*/run.yaml を WSTG-ID 主キーで集約し、checklist_export.csv を出力する。

    python scripts/export_checklist.py
    python scripts/export_checklist.py --root evidence --out checklist_export.csv --summary

集約ステータス:
    fail > todo > info > pass > na  の優先度で「最も注意すべきもの」を採用。
    全 WSTG-ID を todo で初期化するので、未実施が一目で分かる。

このスクリプトは run.yaml の要約フィールドだけを読む。cmd/ や artifacts/ の中身は開かない。
出力した CSV は必ず人が目視レビューしてから Google Sheets に取り込む（機密境界の保護）。
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WSTG_TESTS = REPO_ROOT / "matrix" / "wstg_tests.yaml"
DEFAULT_ROOT = REPO_ROOT / "evidence"
DEFAULT_OUT = REPO_ROOT / "checklist_export.csv"

# 数字が小さいほど「注意すべき」＝集約時に勝つ
VERDICT_PRIORITY = {"fail": 0, "todo": 1, "info": 2, "pass": 3, "na": 4}
COLUMNS = [
    "wstg_id",
    "category",
    "title",
    "status",
    "activities",
    "evidence_paths",
    "finding_summary",
    "updated",
]


def load_tests() -> dict:
    if not WSTG_TESTS.exists():
        raise SystemExit(f"{WSTG_TESTS} がありません。python scripts/build_wstg_index.py を実行してください。")
    data = yaml.safe_load(WSTG_TESTS.read_text(encoding="utf-8"))
    return {t["id"]: t for t in data["tests"]}


def one_line(text) -> str:
    return " ".join(str(text).split())


def collect_runs(root: Path) -> list[tuple[Path, dict]]:
    runs = []
    for run_yaml in sorted(root.glob("*/run.yaml")):
        try:
            data = yaml.safe_load(run_yaml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            print(f"[警告] {run_yaml} を読めません: {exc}", file=sys.stderr)
            continue
        runs.append((run_yaml.parent, data))
    return runs


def build_rows(tests: dict, runs: list, root: Path) -> tuple[list[dict], list[str]]:
    warnings: list[str] = []
    rows = {
        wid: {
            "wstg_id": wid,
            "category": t["category"],
            "title": t["title"],
            "status": "todo",
            "_verdicts": [],
            "activities": [],
            "evidence_paths": [],
            "finding_summary": [],
            "updated": "",
        }
        for wid, t in tests.items()
    }

    # 統合済み項目は既定で na（単独実施しない）
    for wid, t in tests.items():
        if t.get("deprecated"):
            rows[wid]["status"] = "na"
            rows[wid]["finding_summary"].append(f"v4.2 で「{t.get('merged_into','')}」に統合。単独では実施しない。")

    for run_dir, data in runs:
        activity = data.get("activity_id") or run_dir.name
        date = one_line(data.get("date", ""))
        try:
            rel = run_dir.relative_to(REPO_ROOT)
        except ValueError:
            rel = run_dir
        for cov in data.get("covers") or []:
            if not isinstance(cov, dict) or "id" not in cov:
                warnings.append(f"{run_dir.name}: covers の書式が不正なエントリを飛ばしました")
                continue
            wid = cov["id"]
            if wid not in rows:
                warnings.append(f"{run_dir.name}: 未知の WSTG-ID {wid}")
                continue
            verdict = one_line(cov.get("verdict", "todo")).lower() or "todo"
            if verdict not in VERDICT_PRIORITY:
                warnings.append(f"{run_dir.name}/{wid}: 不正な verdict '{verdict}' を todo として扱います")
                verdict = "todo"
            row = rows[wid]
            row["_verdicts"].append(verdict)
            if activity not in row["activities"]:
                row["activities"].append(activity)
            path = f"{rel}/"
            if path not in row["evidence_paths"]:
                row["evidence_paths"].append(path)
            finding = one_line(cov.get("finding", ""))
            if finding:
                row["finding_summary"].append(f"[{activity}] {finding}")
            if date > row["updated"]:
                row["updated"] = date

    out = []
    for wid, row in rows.items():
        if row["_verdicts"]:
            row["status"] = min(row["_verdicts"], key=lambda v: VERDICT_PRIORITY[v])
        out.append(
            {
                "wstg_id": row["wstg_id"],
                "category": row["category"],
                "title": row["title"],
                "status": row["status"],
                "activities": ",".join(row["activities"]),
                "evidence_paths": ",".join(row["evidence_paths"]),
                "finding_summary": " / ".join(row["finding_summary"]),
                "updated": row["updated"],
            }
        )
    return out, warnings


def print_summary(rows: list[dict]) -> None:
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print("\n集約ステータス:")
    for status in ("fail", "todo", "info", "pass", "na"):
        if counts.get(status):
            print(f"  {status:5s} {counts[status]:3d}")
    fails = [r["wstg_id"] for r in rows if r["status"] == "fail"]
    if fails:
        print(f"  → fail: {', '.join(fails)}")


def push_to_sheets(rows: list[dict], sheet_id: str, worksheet: str, creds: str, assume_yes: bool) -> int:
    """任意機能: 目視レビュー済みの内容を Google Sheets に反映する。"""
    try:
        import gspread  # type: ignore
    except ImportError:
        print("gspread が必要です: pip install gspread google-auth", file=sys.stderr)
        return 2

    print(f"\n{len(rows)} 行を Google Sheets ({sheet_id} / {worksheet}) に上書きします。")
    print("CSV の中身を目視レビュー済みであることを確認してください（機密が混じっていないか）。")
    if not assume_yes and input("続行しますか? [y/N] ").strip().lower() != "y":
        print("中止しました。")
        return 1

    gc = gspread.service_account(filename=creds)
    sh = gc.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(worksheet)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=worksheet, rows=len(rows) + 10, cols=len(COLUMNS))
    ws.clear()
    ws.update([COLUMNS] + [[r[c] for c in COLUMNS] for r in rows])
    print("反映しました。")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="エビデンスのルート（既定: evidence/）")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="出力 CSV（既定: checklist_export.csv）")
    ap.add_argument("--summary", action="store_true", help="ステータス別の件数を表示する")
    ap.add_argument("--push", action="store_true", help="任意: Google Sheets へ反映（既定は CSV 出力のみ）")
    ap.add_argument("--sheet-id", help="--push 時の対象スプレッドシート ID")
    ap.add_argument("--worksheet", default="WSTG", help="--push 時のワークシート名")
    ap.add_argument("--creds", default="service_account.json", help="--push 時のサービスアカウント JSON")
    ap.add_argument("--yes", action="store_true", help="--push の確認プロンプトを省略する")
    args = ap.parse_args()

    root = Path(args.root)
    tests = load_tests()
    runs = collect_runs(root) if root.exists() else []
    if not root.exists():
        print(f"[情報] {root} がありません。全項目 todo の雛形を出力します。")

    rows, warnings = build_rows(tests, runs, root)
    for w in warnings:
        print(f"[警告] {w}", file=sys.stderr)

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{out_path} を出力: {len(rows)} 行 / エビデンス {len(runs)} 件")
    if args.summary:
        print_summary(rows)
    print("\n次: CSV を目視レビュー → Google Sheets で「ファイル → インポート → アップロード → 現在のシートを置換」")

    if args.push:
        if not args.sheet_id:
            print("--push には --sheet-id が必要です", file=sys.stderr)
            return 2
        return push_to_sheets(rows, args.sheet_id, args.worksheet, args.creds, args.yes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
