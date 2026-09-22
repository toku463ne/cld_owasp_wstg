#!/usr/bin/env python3
"""record.html をローカル配信し、手順ごとの『スクショを撮る』ボタンを有効にする。

    uv run scripts/serve_record.py <activity_dir>            # http://127.0.0.1:8765/record.html
    uv run scripts/serve_record.py <activity_dir> --port 9000 --open

file:// の record.html はブラウザの制約でシェルを実行できない（＝ボタンで撮れない）。
このサーバ経由で開くと、record.html の各手順の『📷 この手順のスクショを撮る』が
POST /api/capture でサーバ側の save_shot.py（--grab）を叩き、そのフォルダの artifacts/ に
保存→evidence.js を更新→ページがリロードして該当手順の直下に画像が出る。

安全のため 127.0.0.1 のみで待ち受ける（撮影 API を外部に晒さない）。GET は activity_dir の
ファイル配信（record.html / evidence.js / cmd/ / artifacts/。http なので Chrome でも iframe/img が
確実に表示される）。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SAVE_SHOT = SCRIPTS / "save_shot.py"
WID_RE = re.compile(r"^WSTG-[A-Z]+-\d+$")


class RecordHandler(SimpleHTTPRequestHandler):
    activity_dir: Path = Path(".")     # build_server が差し替える

    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        # record.html / evidence.js は毎回最新を読ませる（撮影後のリロードで反映）
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/api/capture":
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(200, {"ok": False, "error": "リクエストが不正です"})
            return

        wid = str(data.get("wid", ""))
        if not WID_RE.match(wid):
            self._json(200, {"ok": False, "error": f"WSTG-ID の形式が不正です: {wid}"})
            return
        argv = [sys.executable, str(SAVE_SHOT), str(self.activity_dir),
                "--wid", wid, "--grab", "--force"]
        step = data.get("step")
        if isinstance(step, int) or (isinstance(step, str) and str(step).isdigit()):
            argv += ["--step", str(int(step))]
        try:
            delay = max(0, min(60, int(data.get("delay", 0) or 0)))
        except (TypeError, ValueError):
            delay = 0
        argv += ["--delay", str(delay)]

        # 撮影（範囲選択）はユーザ操作待ちで長くなり得る。ThreadingHTTPServer なので
        # 他リクエストは止まらない。上限は選択待ちを見込んで長めに。
        try:
            proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self._json(200, {"ok": False, "error": "タイムアウト（範囲選択がされませんでした）"})
            return
        if proc.returncode == 0:
            self._json(200, {"ok": True, "out": proc.stdout.strip()})
        else:
            self._json(200, {"ok": False,
                             "error": (proc.stderr or proc.stdout).strip()[:800]})

    def log_message(self, fmt, *args):   # ログは静かめに（POST とエラーだけ）
        if self.command == "POST" or (args and str(args[0]).startswith(("4", "5"))):
            super().log_message(fmt, *args)


def build_server(activity_dir: Path, host: str = "127.0.0.1", port: int = 8765):
    """テスト・本体共用。activity_dir を配信する httpd を返す（serve は呼び側）。"""
    handler = partial(RecordHandler, directory=str(activity_dir))
    RecordHandler.activity_dir = activity_dir
    return ThreadingHTTPServer((host, port), handler)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("activity_dir", help="evidence/<activity_id>[-<target>]-<yyyymmdd>")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1", help="既定は 127.0.0.1（外部に晒さない）")
    ap.add_argument("--open", action="store_true", help="既定ブラウザで record.html を開く")
    args = ap.parse_args()

    activity_dir = Path(args.activity_dir)
    if not (activity_dir / "record.html").exists():
        print(f"record.html がありません: {activity_dir}", file=sys.stderr)
        print("  uv run scripts/new_activity.py <activity_id> か gen_record.py で先に作成してください。",
              file=sys.stderr)
        return 2

    try:
        httpd = build_server(activity_dir, args.host, args.port)
    except OSError as exc:
        print(f"ポート {args.port} を開けません: {exc}", file=sys.stderr)
        print("  --port で別のポートを指定してください。", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}/record.html"
    print(f"[serve_record] 配信中: {url}")
    print(f"  対象: {activity_dir}")
    print("  各手順の『📷 この手順のスクショを撮る』でキャプチャできます。停止は Ctrl+C。")
    if args.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve_record] 停止しました。")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
