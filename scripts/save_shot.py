#!/usr/bin/env python3
"""クリップボードの画像（スクショ）をアクティビティの artifacts/ に保存する。

    uv run scripts/save_shot.py <activity_dir> --wid WSTG-INFO-01
    uv run scripts/save_shot.py <activity_dir> --wid WSTG-INFO-01 --step 3
    uv run scripts/save_shot.py <activity_dir> --from /path/to/existing.png --wid WSTG-CONF-05

やること:
  1. クリップボードの PNG 画像を取り出し（X11=xclip / Wayland=wl-paste を自動判定）、
     <activity_dir>/artifacts/shot-<WID>[-s<n>]-<日時>.png に保存する。
  2. record.html が読む evidence.js を作り直す（--wid のスクショはそのカードに <img> で出る）。
  3. 貼り付け用に、保存した相対パスを表示する（手動手順の manual-*.txt に控える用）。

クリップボードに画像が無い／ツール未導入のときは、次にやることを添えて終了する。
撮影から一気にやるなら flameshot（`flameshot gui -c` でクリップボードへ）と併用する。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_activity import refresh_record, print_missing_run_yaml  # noqa: E402

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def clipboard_png() -> bytes:
    """表示サーバを判定し、クリップボードの PNG をバイト列で返す（無ければ空）。"""
    wayland = bool(os.environ.get("WAYLAND_DISPLAY")) or \
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    if wayland:
        cmd, pkg = ["wl-paste", "--type", "image/png"], "wl-clipboard"
    else:
        cmd, pkg = ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"], "xclip"
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise SystemExit(
            f"{cmd[0]} が見つかりません。`sudo apt install -y {pkg}` で入れてください。"
        )
    return proc.stdout or b""


def make_name(wid: str | None, step: int | None, explicit: str | None) -> str:
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    if explicit:
        stem = re.sub(r"[^A-Za-z0-9._-]+", "-", explicit).strip("-") or "shot"
        return stem if stem.lower().endswith(".png") else f"{stem}.png"
    if wid:
        s = f"-s{step}" if step else ""
        return f"shot-{wid}{s}-{ts}.png"
    return f"shot-{ts}.png"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("activity_dir", help="evidence/<activity_id>[-<target>]-<yyyymmdd>")
    ap.add_argument("--wid", help="紐づける WSTG-ID（record.html のそのカードに <img> で出る）")
    ap.add_argument("--step", type=int, help="手順番号（ファイル名に付けるだけ）")
    ap.add_argument("--name", help="ファイル名を明示（既定は shot-<WID>-<日時>.png）")
    ap.add_argument("--from", dest="src", help="クリップボードの代わりに既存の画像ファイルから保存")
    ap.add_argument("--force", action="store_true", help="同名ファイルを上書きする")
    args = ap.parse_args()

    activity_dir = Path(args.activity_dir)
    if not (activity_dir / "run.yaml").exists():
        print_missing_run_yaml(activity_dir, "save_shot.py")
        return 2

    if args.src:
        data = Path(args.src).read_bytes()
    else:
        data = clipboard_png()

    if not data:
        print("クリップボードに画像がありません（または取得に失敗）。", file=sys.stderr)
        print("  スクショを撮ってからもう一度。範囲選択して直接クリップボードへ入れるなら "
              "`flameshot gui -c`（要 `sudo apt install -y flameshot`）。", file=sys.stderr)
        return 1
    if not data.startswith(PNG_MAGIC):
        print("取得したデータが PNG ではありません（クリップボードにテキストしか無い等）。", file=sys.stderr)
        print("  画像をコピーし直してから再実行してください。", file=sys.stderr)
        return 1

    art = activity_dir / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    dest = art / make_name(args.wid, args.step, args.name)
    if dest.exists() and not args.force:
        print(f"既に存在します: {dest}（--force で上書き）", file=sys.stderr)
        return 1
    dest.write_bytes(data)

    rel = dest.relative_to(activity_dir).as_posix()
    print(f"保存: {dest}  ({len(data)} バイト)")
    print(f"  相対パス: {rel}")
    if args.wid:
        refresh_record(activity_dir)
        print(f"  record.html を更新（{args.wid} のカードに <img> で表示）。ブラウザをリロードしてください。")
    else:
        print("  --wid を付けると record.html の該当カードに <img> で表示されます。")
        print(f"  手動手順の記録に貼る場合: artifacts/manual-*.txt に `{rel}` を控える。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
