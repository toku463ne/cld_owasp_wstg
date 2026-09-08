#!/usr/bin/env python3
"""docs/owasp の WSTG 原文から、テスト一覧 `matrix/wstg_tests.yaml` を生成する。

生成物はコミットするので、原文が手元になくても他のスクリプト
（export_checklist.py / new_activity.py / build_coverage.py）は動く。

    python scripts/build_wstg_index.py
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wstg_parse import REPO_ROOT, load_tests  # noqa: E402

OUT = REPO_ROOT / "matrix" / "wstg_tests.yaml"
WSTG_VERSION = "4.2"


def _q(text: str) -> str:
    """YAML のダブルクォート文字列にエスケープする。"""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(tests) -> str:
    today = _dt.date.today().isoformat()
    lines = [
        "# 自動生成ファイル — 手で編集しない。",
        "# 生成元: scripts/build_wstg_index.py（docs/owasp の WSTG 原文を解析）",
        f"# 生成日: {today}",
        f'wstg_version: "{WSTG_VERSION}"',
        f"count: {len(tests)}",
        "tests:",
    ]
    for t in tests:
        lines.append(f"  - id: {t.id}")
        lines.append(f"    category: {t.category}")
        lines.append(f"    category_name: {_q(t.category_name)}")
        lines.append(f"    title: {_q(t.title)}")
        if t.deprecated:
            lines.append("    deprecated: true")
            lines.append(f"    merged_into: {_q(t.merged_into)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--docs-root", help="WSTG 原文のルート（既定: docs/owasp）")
    ap.add_argument("--check", action="store_true", help="生成せず、差分の有無だけ確認する")
    args = ap.parse_args()

    tests = load_tests(Path(args.docs_root) if args.docs_root else None)
    if not tests:
        print("WSTG テストが1件も見つかりませんでした。原文の取得を確認してください。", file=sys.stderr)
        return 1

    text = render(tests)
    if args.check:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        same = current.split("\n", 3)[3:] == text.split("\n", 3)[3:]  # 生成日の行は無視
        print("最新です" if same else "差分あり: python scripts/build_wstg_index.py を実行してください")
        return 0 if same else 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    active = sum(1 for t in tests if not t.deprecated)
    print(f"{OUT.relative_to(REPO_ROOT)} を生成: {len(tests)} 件（実施対象 {active} 件 / 統合済み {len(tests) - active} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
