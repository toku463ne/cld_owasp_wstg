#!/usr/bin/env python3
"""evidence/ を「サイト」（WSTG を実施する対象サイト＝案件）ごとのフォルダに分けて扱う。

    evidence/<サイト名>/<活動>-<対象>-<日付>/   実施フォルダ（run.yaml・cmd/・artifacts/）
    evidence/<サイト名>/_findings/              所見（F-001 からサイトごとに採番）
    evidence/<サイト名>/_state/                 タスクの手動チェック

サイトを受け取るスクリプト（new_activity / run_target / findings / tasks / export_checklist）は
`--site <名前>`（または環境変数 WSTG_SITE）で選ぶ。サイトが1つだけなら省略できる。
`--root <フォルダ>` を渡すとサイトの解決をせず、そのフォルダをそのまま使う（selftest・一時フォルダ用）。

旧構成（evidence/ 直下に実施フォルダ・_findings/ がある）は移行してから使う:

    uv run scripts/migrate_site.py <サイト名>
"""

from __future__ import annotations

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_BASE = REPO_ROOT / "evidence"
SITE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SITE_ENV = "WSTG_SITE"
LEGACY_DIRS = ("_findings", "_state")


class SiteError(Exception):
    """サイトを決められない（メッセージに次にやることを含める）。"""


def is_site_dir(d: Path) -> bool:
    """サイトのフォルダか（名前が規則どおりで、実施フォルダ＝run.yaml を持つフォルダではない）。"""
    return d.is_dir() and bool(SITE_RE.match(d.name)) and not (d / "run.yaml").exists()


def list_sites(base: Path = EVIDENCE_BASE) -> list:
    """base 直下のサイト名（名前順）。"""
    base = Path(base)
    if not base.is_dir():
        return []
    return sorted(d.name for d in base.iterdir() if is_site_dir(d))


def legacy_items(base: Path = EVIDENCE_BASE) -> list:
    """旧構成の名残（base 直下の実施フォルダ・_findings・_state）。空なら移行済み。"""
    base = Path(base)
    if not base.is_dir():
        return []
    acts = [d for d in sorted(base.iterdir()) if d.is_dir() and (d / "run.yaml").exists()]
    return acts + [base / n for n in LEGACY_DIRS if (base / n).exists()]


def migrate_hint(base: Path = EVIDENCE_BASE) -> str:
    return (f"{base} 直下に旧構成（サイト分け前）の実施フォルダ・所見があります。"
            "先にサイトのフォルダへ移してください:\n"
            "  uv run scripts/migrate_site.py <サイト名> --dry-run   # 移す内容の確認\n"
            "  uv run scripts/migrate_site.py <サイト名>")


def resolve_root(root: str | None = None, site: str | None = None, *, create: bool = False,
                 base: Path = EVIDENCE_BASE) -> Path:
    """--root / --site / WSTG_SITE から、そのサイトのフォルダ（旧来の evidence ルート相当）を返す。

    create=True（new_activity・run_target）ならまだ無いサイトも返す（フォルダは呼び側が作る）。
    """
    if root:
        return Path(root)
    base = Path(base)
    site = (site or os.environ.get(SITE_ENV) or "").strip()
    if legacy_items(base):
        raise SiteError(migrate_hint(base))
    names = list_sites(base)
    if site:
        if not SITE_RE.match(site):
            raise SiteError(f"サイト名が不正です: {site}（英数字で始め、英数字・. _ - だけ。64 字以内）")
        if site not in names and not create:
            have = "、".join(names) or "（まだありません）"
            raise SiteError(f"サイト {site} がありません。既存のサイト: {have}\n"
                            f"  新しく始めるなら: uv run scripts/run_target.py --site {site} --target <対象>")
        return base / site
    if len(names) == 1:
        return base / names[0]
    if not names:
        raise SiteError("サイトがまだありません。--site <サイト名> を付けて始めてください:\n"
                        "  uv run scripts/run_target.py --site <サイト名> --target <対象>")
    raise SiteError(f"サイトが複数あります（{'、'.join(names)}）。--site <サイト名> で選ぶか、"
                    f"export {SITE_ENV}=<サイト名> を設定してください。")


def add_site_args(ap, root_help: str = "") -> None:
    """--site / --root を argparse に足す（各スクリプト共通）。"""
    ap.add_argument("--site", help=f"サイト名（evidence/<サイト名>/ を使う。環境変数 {SITE_ENV} でも可。"
                                   "サイトが1つだけなら省略可）")
    ap.add_argument("--root", help=root_help or "サイトを使わずこのフォルダを直接使う（一時フォルダでの確認用）")
