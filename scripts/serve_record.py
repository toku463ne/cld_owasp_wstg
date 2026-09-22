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
SHOT_RE = re.compile(r"^shot-.*\.png$")

sys.path.insert(0, str(SCRIPTS))
from new_activity import refresh_record, print_missing_run_yaml  # noqa: E402


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

    def do_GET(self) -> None:  # noqa: N802
        # record.html / evidence.js を出す前に最新化する。findings.md や run.yaml を
        # 手で編集しても、ブラウザのリロードだけで反映される。
        route = self.path.split("?", 1)[0]
        if route in ("/", "/record.html", "/evidence.js"):
            try:
                refresh_record(self.activity_dir)
            except SystemExit:
                pass
        super().do_GET()

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def do_POST(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        if route == "/api/capture":
            self._capture()
        elif route == "/api/delete_shot":
            self._delete_shot()
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def _delete_shot(self) -> None:
        data = self._read_json()
        if data is None:
            self._json(200, {"ok": False, "error": "リクエストが不正です"})
            return
        rel = str(data.get("path", ""))
        base = (self.activity_dir / "artifacts").resolve()
        target = (self.activity_dir / rel).resolve()
        # artifacts/ 直下の shot-*.png のみ削除可（パストラバーサル・任意ファイル削除を防ぐ）
        if target.parent != base or not SHOT_RE.match(target.name):
            self._json(200, {"ok": False, "error": f"削除できるのは artifacts/shot-*.png だけです: {rel}"})
            return
        if not target.exists():
            self._json(200, {"ok": False, "error": f"見つかりません: {rel}"})
            return
        try:
            target.unlink()
            refresh_record(self.activity_dir)   # evidence.js を作り直して表示から外す
        except OSError as exc:
            self._json(200, {"ok": False, "error": str(exc)})
            return
        self._json(200, {"ok": True, "deleted": rel})

    def _capture(self) -> None:
        data = self._read_json()
        if data is None:
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
    if not (activity_dir / "run.yaml").exists():
        print_missing_run_yaml(activity_dir, "serve_record.py")
        return 2

    # 起動時に record.html / evidence.js を最新化する（git pull 後にテンプレートが
    # 変わっても、既存フォルダの record.html を作り直さないと反映されないため）。
    try:
        refresh_record(activity_dir)
        print("[serve_record] record.html / evidence.js を最新化しました。")
    except SystemExit as exc:
        print(f"[serve_record] 最新化をスキップ: {exc}", file=sys.stderr)

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
