#!/usr/bin/env python3
"""全 evidence/*/run.yaml と所見を WSTG-ID 主キーで集約し、checklist_export.csv を出力する。

    uv run scripts/export_checklist.py
    uv run scripts/export_checklist.py --root evidence --out checklist_export.csv --summary

日常の確認は Web（serve_record.py の WSTG 索引）で行う。CSV は報告書に添付する等、
一覧を外に持ち出すときの出力（Web の /export.csv からも同じものが取れる）。

集約ステータス:
    fail > todo > info > pass > na  の優先度で「最も注意すべきもの」を採用。
    全 WSTG-ID を todo で初期化するので、未実施が一目で分かる。

このスクリプトは run.yaml の要約フィールドと所見のタイトル・深刻度だけを読む。
cmd/ や artifacts/ の中身は開かない。CSV を外に出すときは必ず人が目視レビューする（機密境界の保護）。

finding_summary には、各アクティビティの判定理由（covers[].finding）に続けて、その WSTG に
紐づく所見（取り下げ以外）を「[F-003 High 8.1] タイトル」の形で入れる。
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
        raise SystemExit(f"{WSTG_TESTS} がありません。uv run scripts/build_wstg_index.py を実行してください。")
    data = yaml.safe_load(WSTG_TESTS.read_text(encoding="utf-8"))
    return {t["id"]: t for t in data["tests"]}


def load_findings(root: Path) -> list:
    """evidence/_findings/ の所見（無ければ空）。"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import findings as _findings
    return _findings.list_all(root) if root.exists() else []


def to_csv(rows: list[dict]) -> str:
    """CSV 本文（Web の /export.csv と共用。BOM は付けない＝呼び側で付ける）。"""
    import io
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


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


def build_rows(tests: dict, runs: list, root: Path, findings=None) -> tuple[list[dict], list[str]]:
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

    for f in findings or []:
        if f.get("status") == "rejected":
            continue
        score = f" {f['base']}" if f.get("base") is not None else ""
        for wid in f.get("wstg") or []:
            if wid in rows:
                rows[wid]["finding_summary"].append(
                    f"[{f['id']} {f.get('severity_label', '')}{score}] {one_line(f.get('title', ''))}")

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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="エビデンスのルート（既定: evidence/）")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="出力 CSV（既定: checklist_export.csv）")
    ap.add_argument("--summary", action="store_true", help="ステータス別の件数を表示する")
    args = ap.parse_args()

    root = Path(args.root)
    tests = load_tests()
    runs = collect_runs(root) if root.exists() else []
    if not root.exists():
        print(f"[情報] {root} がありません。全項目 todo の雛形を出力します。")

    rows, warnings = build_rows(tests, runs, root, load_findings(root))
    for w in warnings:
        print(f"[警告] {w}", file=sys.stderr)

    out_path = Path(args.out)
    out_path.write_text(to_csv(rows), encoding="utf-8-sig", newline="")

    print(f"{out_path} を出力: {len(rows)} 行 / エビデンス {len(runs)} 件")
    if args.summary:
        print_summary(rows)
    print("\n次: CSV を外に出す前に目視レビュー（生値・資格情報が混じっていないか）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
