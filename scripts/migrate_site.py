#!/usr/bin/env python3
"""旧構成（evidence/ 直下に実施フォルダ・_findings・_state）を、サイトのフォルダ evidence/<サイト名>/ へ移す。

    uv run scripts/migrate_site.py <サイト名> --dry-run   # 移すもの・書き換える行数の確認だけ
    uv run scripts/migrate_site.py <サイト名>             # 移す

やること:
  1. evidence/ 直下の実施フォルダ（run.yaml を持つ）と _findings/・_state/ を evidence/<サイト名>/ へ移す
     （同じファイルシステム内の改名なので、中身・更新時刻はそのまま）
  2. 記録済みのコマンドに入っているパス（evidence/<フォルダ> → evidence/<サイト名>/<フォルダ>）を書き換える。
     対象は run.yaml（commands: と cmd_overrides:）と cmd/*.txt の先頭（`$ コマンド` から区切り線まで）だけ。
     コマンドの出力（区切り線より後ろ）・artifacts/・notes.md・所見の本文には触れない。
     コマンドが今の手順と同じまま残るので、run_target / run_activity --skip-done で再実行されない
  3. record.html / evidence.js を作り直す（所見の evidence パスはサイトのフォルダからの相対なので変わらない）

移したあとは、各スクリプトに --site <サイト名> を付ける（サイトが1つだけなら省略可）。
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sites  # noqa: E402

SEP = "# " + "-" * 68


def path_forms(base: Path) -> list:
    """コマンド中に現れうる evidence ルートの書き方（リポジトリ相対・絶対）。"""
    forms = [base.resolve().as_posix()]
    try:
        forms.append(base.resolve().relative_to(sites.REPO_ROOT).as_posix())
    except ValueError:
        pass
    return forms


def make_rewriter(base: Path, site: str, folders: list):
    """<ルート>/<フォルダ> を <ルート>/<サイト>/<フォルダ> にする置換関数（ほかの文字列の一部には当てない）。"""
    names = "|".join(re.escape(f) for f in sorted(folders, key=len, reverse=True))
    pats = [re.compile(r"(?<![\w./-])(" + re.escape(form) + r")/(" + names + r")(?=[/\s'\"`)]|$)", re.M)
            for form in path_forms(base)]

    def rewrite(text: str) -> tuple:
        n = 0
        for pat in pats:
            text, k = pat.subn(lambda m: f"{m.group(1)}/{site}/{m.group(2)}", text)
            n += k
        return text, n
    return rewrite


def rewrite_cmd_header(text: str, rewrite) -> tuple:
    """cmd/*.txt の先頭（`$ コマンド` 〜 最初の区切り線）だけを書き換える。出力部分は触らない。"""
    lines = text.split("\n")
    end = next((i for i, ln in enumerate(lines) if ln.startswith(SEP)), None)
    if end is None:
        return text, 0
    head, n = rewrite("\n".join(lines[:end]))
    return (head + "\n" + "\n".join(lines[end:]), n) if n else (text, 0)


def rewrite_file(path: Path, fn, dry_run: bool) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    new, n = fn(text)
    if n and not dry_run:
        st = path.stat()
        path.write_text(new, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))   # --skip-done の新旧判定（更新時刻）を変えない
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("site", help="移し先のサイト名（evidence/<サイト名>/。英数字で始め、英数字・. _ - だけ）")
    ap.add_argument("--base", default=str(sites.EVIDENCE_BASE), help="evidence ルート（既定: evidence/）")
    ap.add_argument("--dry-run", action="store_true", help="移すもの・書き換える行数を表示するだけ")
    args = ap.parse_args()

    base = Path(args.base)
    if not sites.SITE_RE.match(args.site):
        print(f"サイト名が不正です: {args.site}（英数字で始め、英数字・. _ - だけ。64 字以内）", file=sys.stderr)
        return 2
    items = sites.legacy_items(base)
    if not items:
        print(f"{base} 直下に移すもの（実施フォルダ・_findings・_state）はありません。移行済みです。")
        return 0
    dest = base / args.site
    if (dest / "run.yaml").exists() or any(i.name == args.site for i in items):
        print(f"{args.site} は既存の実施フォルダ名と同じです。別のサイト名を指定してください。", file=sys.stderr)
        return 2
    clash = [i.name for i in items if (dest / i.name).exists()]
    if clash:
        print(f"移し先に同名のものがあります: {', '.join(clash)}（{dest}）。上書きはしません。"
              "中身を確かめて片付けてから再実行してください。", file=sys.stderr)
        return 2

    folders = [i.name for i in items if (i / "run.yaml").exists()]
    rewrite = make_rewriter(base, args.site, folders)
    verb = "移す予定" if args.dry_run else "移動"
    if not args.dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    total = 0
    for item in items:
        moved = dest / item.name
        print(f"  {verb}: {item} → {moved}")
        if not args.dry_run:
            item.rename(moved)
        where = item if args.dry_run else moved
        if item.name not in folders:
            continue
        n = rewrite_file(where / "run.yaml", rewrite, args.dry_run)
        for f in sorted((where / "cmd").glob("*.txt")):
            n += rewrite_file(f, lambda t: rewrite_cmd_header(t, rewrite), args.dry_run)
        if n:
            print(f"      記録済みコマンドのパスを書き換え: {n} 箇所")
        total += n

    if args.dry_run:
        print(f"\n（dry-run）{len(items)} 件を {dest} へ移し、パスを {total} 箇所書き換える予定です。")
        return 0

    from new_activity import refresh_record
    for name in folders:
        try:
            refresh_record(dest / name)
        except SystemExit:
            print(f"  [警告] {name} の record.html を作り直せませんでした。"
                  f"uv run scripts/gen_record.py {dest / name} を試してください。", file=sys.stderr)
    print(f"\n{len(items)} 件を {dest} へ移しました（パスの書き換え {total} 箇所）。")
    print(f"  以後は --site {args.site} を付けて実行する（サイトが1つだけなら省略可）。例:")
    print(f"    uv run scripts/run_target.py --site {args.site} --target <対象> --list")
    print("  Web（serve_record.py）は再起動不要。/ を開き直すとサイトが選べる。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
