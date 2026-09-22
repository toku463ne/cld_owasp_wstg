#!/usr/bin/env python3
"""実行はせず、run.yaml と既存のエビデンスから record.html / evidence.js を作り直す。

    uv run scripts/gen_record.py <activity_dir>

いつ使うか:
  - criteria.yaml など上流を更新した後、既存の活動フォルダの表示を最新の手順に合わせたいとき
    （エビデンス本体は cmd/・artifacts/ に残るので、作り直しても失われない）
  - run.yaml の covers に verdict / finding を書き足した後、record.html に反映したいとき
  - 手動手順の artifacts/manual-*.txt に観察を書き足した後

コマンドの実行は run_activity.py の担当。ここは表示（record.html / evidence.js）を
作り直すだけで、run.yaml やエビデンスファイルには手を入れない。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_activity import refresh_record, print_missing_run_yaml  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("activity_dir", help="evidence/<activity_id>[-<target>]-<yyyymmdd>")
    args = ap.parse_args()

    activity_dir = Path(args.activity_dir)
    if not (activity_dir / "run.yaml").exists():
        print_missing_run_yaml(activity_dir, "gen_record.py")
        return 2

    data = refresh_record(activity_dir)
    n_items = len(data.get("items", []))
    n_out = sum(1 for it in data["items"] for st in it["steps"] if st["output"].strip())
    print(f"[gen_record] {activity_dir / 'record.html'} を更新（{n_items} 項目、出力あり {n_out} 手順）。")
    print(f"  ブラウザで {activity_dir / 'record.html'} を開いて確認してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
