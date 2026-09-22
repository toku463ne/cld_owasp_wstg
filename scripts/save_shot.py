#!/usr/bin/env python3
"""スクショをアクティビティの artifacts/ に保存する（範囲選択キャプチャ or クリップボード）。

    uv run scripts/save_shot.py <activity_dir> --wid WSTG-INFO-01 --grab --delay 3  # 3秒後に範囲選択（その間にブラウザを前面へ）
    uv run scripts/save_shot.py <activity_dir> --wid WSTG-INFO-01          # クリップボードの画像を保存
    uv run scripts/save_shot.py <activity_dir> --wid WSTG-INFO-01 --step 3
    uv run scripts/save_shot.py <activity_dir> --from /path/to/existing.png --wid WSTG-CONF-05

やること:
  1. 画像を取り込み、<activity_dir>/artifacts/shot-<WID>[-s<n>]-<日時>.png に保存する。
       --grab … その場で範囲選択してキャプチャ。セッションに合う素直なツールを優先
                （X11=maim/scrot/xfce4-screenshooter、Wayland=grim+slurp、flameshot は後回し）。
                `--list-tools` で使えるツール確認、`--tool <名前>` で明示指定。クリップボード不要。
       既定   … クリップボードの PNG（X11=xclip / Wayland=wl-paste を自動判定）。
       --from … 既存の画像ファイルから取り込む。
  2. record.html が読む evidence.js を作り直す（--wid のスクショはそのカードに <img> で出る）。
  3. 貼り付け用に、保存した相対パスを表示する。

クリップボードが空/画像でないときは、入っている型と --grab の使い方を案内する。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_activity import refresh_record, print_missing_run_yaml  # noqa: E402

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def is_wayland() -> bool:
    return bool(os.environ.get("WAYLAND_DISPLAY")) or \
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def clipboard_png() -> bytes:
    """クリップボードの PNG をバイト列で返す（無ければ空）。"""
    if is_wayland():
        cmd, pkg = ["wl-paste", "--type", "image/png"], "wl-clipboard"
    else:
        cmd, pkg = ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"], "xclip"
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise SystemExit(f"{cmd[0]} が見つかりません。`sudo apt install -y {pkg}` で入れてください。")
    return proc.stdout or b""


def clipboard_types() -> str:
    """クリップボードに入っている型の一覧（診断用。取れなければ空文字）。"""
    cmd = (["wl-paste", "--list-types"] if is_wayland()
           else ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"])
    try:
        return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              text=True).stdout.strip()
    except FileNotFoundError:
        return ""


# 範囲選択キャプチャに使えるツール。セッションに合った素直なものを優先し、
# GUI が出ないことのある flameshot は後回しにする（実測でハングした）。
# 各ツールに必要なバイナリと、dest に保存するための起動方法（file=直接保存 / stdout=標準出力）。
_TOOLS = {
    "grim+slurp":          {"bins": ["grim", "slurp"], "mode": "slurp"},
    "maim":                {"bins": ["maim"], "mode": "file",
                            "argv": lambda d: ["maim", "-s", str(d)]},
    "scrot":               {"bins": ["scrot"], "mode": "file",
                            "argv": lambda d: ["scrot", "-s", str(d)]},
    "xfce4-screenshooter": {"bins": ["xfce4-screenshooter"], "mode": "file",
                            "argv": lambda d: ["xfce4-screenshooter", "-r", "-s", str(d)]},
    "gnome-screenshot":    {"bins": ["gnome-screenshot"], "mode": "file",
                            "argv": lambda d: ["gnome-screenshot", "-a", "-f", str(d)]},
    "spectacle":           {"bins": ["spectacle"], "mode": "file",
                            "argv": lambda d: ["spectacle", "-r", "-b", "-n", "-o", str(d)]},
    "flameshot":           {"bins": ["flameshot"], "mode": "stdout",
                            "argv": lambda d: ["flameshot", "gui", "--raw"]},
}
_ORDER_WAYLAND = ["grim+slurp", "gnome-screenshot", "spectacle", "flameshot"]
_ORDER_X11 = ["maim", "scrot", "xfce4-screenshooter", "gnome-screenshot", "flameshot", "spectacle"]


def available_tools() -> list:
    """このセッションで使える（インストール済みの）キャプチャツールを優先順で返す。"""
    order = _ORDER_WAYLAND if is_wayland() else _ORDER_X11
    return [n for n in order if all(shutil.which(b) for b in _TOOLS[n]["bins"])]


def run_capture(name: str, dest: Path) -> bool:
    """name のツールで範囲選択キャプチャし dest に保存する。True=保存 / False=キャンセル・失敗。"""
    spec = _TOOLS[name]
    if spec["mode"] == "slurp":                       # grim + slurp（Wayland）
        geom = subprocess.run(["slurp"], stdout=subprocess.PIPE, text=True).stdout.strip()
        if not geom:
            return False                              # 選択キャンセル
        return subprocess.run(["grim", "-g", geom, str(dest)]).returncode == 0 and dest.exists()
    if spec["mode"] == "stdout":                      # flameshot --raw（標準出力に PNG）
        proc = subprocess.run(spec["argv"](dest), stdout=subprocess.PIPE)
        if proc.returncode == 0 and proc.stdout.startswith(PNG_MAGIC):
            dest.write_bytes(proc.stdout)
            return True
        return False
    return subprocess.run(spec["argv"](dest)).returncode == 0 and dest.exists()  # 直接保存


def make_name(wid, step, explicit) -> str:
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
    ap.add_argument("--grab", action="store_true", help="その場で範囲選択してキャプチャ（クリップボード不要）")
    ap.add_argument("--tool", help="--grab で使うツールを明示（例: grim+slurp / maim / xfce4-screenshooter）")
    ap.add_argument("--delay", type=int, default=0, metavar="秒",
                    help="--grab の前に待つ秒数。待つ間に対象ウィンドウ（ブラウザ等）を前面に出す")
    ap.add_argument("--list-tools", action="store_true", help="セッションと使えるキャプチャツールを表示して終了")
    ap.add_argument("--from", dest="src", help="クリップボードの代わりに既存の画像ファイルから保存")
    ap.add_argument("--force", action="store_true", help="同名ファイルを上書きする")
    args = ap.parse_args()

    if args.list_tools:
        sess = "wayland" if is_wayland() else "x11"
        avail = available_tools()
        print(f"セッション: {sess}")
        print(f"使えるキャプチャツール（優先順）: {', '.join(avail) if avail else '（なし）'}")
        if not avail:
            hint = "grim slurp" if is_wayland() else "maim"
            print(f"  無い場合: sudo apt install -y {hint}")
        return 0

    activity_dir = Path(args.activity_dir)
    if not (activity_dir / "run.yaml").exists():
        print_missing_run_yaml(activity_dir, "save_shot.py")
        return 2

    art = activity_dir / "artifacts"
    art.mkdir(parents=True, exist_ok=True)
    dest = art / make_name(args.wid, args.step, args.name)
    if dest.exists() and not args.force:
        print(f"既に存在します: {dest}（--force で上書き）", file=sys.stderr)
        return 1

    # 取り込み方法を決める: --grab（キャプチャ）/ --from（既存）/ 既定（クリップボード）
    if args.grab:
        sess = "wayland" if is_wayland() else "x11"
        avail = available_tools()
        chosen = args.tool or (avail[0] if avail else None)
        if args.tool and (args.tool not in _TOOLS
                          or not all(shutil.which(b) for b in _TOOLS[args.tool]["bins"])):
            print(f"指定ツールが使えません: {args.tool}", file=sys.stderr)
            print(f"  使えるツール: {', '.join(avail) if avail else '（なし）'}", file=sys.stderr)
            return 1
        if not chosen:
            print(f"範囲選択キャプチャに使えるツールがありません（セッション: {sess}）。", file=sys.stderr)
            if is_wayland():
                print("  Wayland: `sudo apt install -y grim slurp`", file=sys.stderr)
            else:
                print("  X11: `sudo apt install -y maim`（または scrot / xfce4-screenshooter）", file=sys.stderr)
            return 1
        print(f"[save_shot] セッション: {sess} / 使用ツール: {chosen}", file=sys.stderr)
        print("  画面が暗転したら範囲をドラッグで選択してください（キャンセルすると保存しません）。",
              file=sys.stderr)
        if chosen == "flameshot" and is_wayland():
            print("  ※ Wayland では flameshot の選択画面が出ないことがあります。"
                  "出なければ Ctrl+C で中断し、`--tool grim+slurp`（要 grim slurp）を使ってください。",
                  file=sys.stderr)
        if args.delay > 0:
            print(f"  {args.delay} 秒後にキャプチャします。今のうちに対象ウィンドウ"
                  "（ブラウザ等）を前面に出してください（Alt+Tab）。", file=sys.stderr)
            time.sleep(args.delay)
        if not run_capture(chosen, dest) or not dest.exists():
            print("キャプチャがキャンセル／失敗しました（何も保存していません）。", file=sys.stderr)
            return 1
        data = dest.read_bytes()
    else:
        data = Path(args.src).read_bytes() if args.src else clipboard_png()
        if not data:
            print("クリップボードに画像がありません（または取得に失敗）。", file=sys.stderr)
            types = clipboard_types()
            if types:
                print(f"  いま入っている型: {', '.join(types.split())}", file=sys.stderr)
            print("  → 範囲選択して直接保存するのが確実です: "
                  f"uv run scripts/save_shot.py {activity_dir} "
                  f"{('--wid ' + args.wid + ' ') if args.wid else ''}--grab", file=sys.stderr)
            print("    クリップボード経由なら、スクショ時に『クリップボードにコピー』を選ぶ"
                  "（flameshot gui -c 等）。ファイル保存になっていると入りません。", file=sys.stderr)
            return 1
        if not data.startswith(PNG_MAGIC):
            print("取得したデータが PNG ではありません（クリップボードにテキストしか無い等）。", file=sys.stderr)
            print(f"  範囲選択で撮り直すのが確実: uv run scripts/save_shot.py {activity_dir} "
                  f"{('--wid ' + args.wid + ' ') if args.wid else ''}--grab", file=sys.stderr)
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
