#!/usr/bin/env python3
"""evidence/ 全体を1つのサーバで配信し、全アクティビティを1ページ（索引）から辿る。

    uv run scripts/serve_record.py                 # evidence/ を配信（索引 http://127.0.0.1:8765/）
    uv run scripts/serve_record.py --open          # 索引をブラウザで開く
    uv run scripts/serve_record.py evidence/<act>  # そのアクティビティを開く（親フォルダを配信）

トップ（/）に、run.yaml を持つアクティビティ一覧（タイトル・対象・日付・判定サマリ）を出す。
各アクティビティは /<フォルダ>/record.html で開く。撮影・削除ボタンは URL のフォルダから
対象を判別するので、統一サーバのままどのアクティビティでも効く。

安全のため 127.0.0.1 のみで待ち受ける（撮影 API を外部に晒さない）。GET は配信ルート配下の
ファイル（record.html / evidence.js / cmd/ / artifacts/）。record.html / evidence.js は出す前に
最新化するので、findings.md や run.yaml を手編集してもリロードで反映される。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import webbrowser
from collections import Counter
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent
SAVE_SHOT = SCRIPTS / "save_shot.py"
WID_RE = re.compile(r"^WSTG-[A-Z]+-\d+$")
SHOT_RE = re.compile(r"^shot-.*\.png$")

sys.path.insert(0, str(SCRIPTS))
from new_activity import (  # noqa: E402
    refresh_record, resolve_activity, update_cover, update_findings, VALID_VERDICTS,
)

VERDICTS = ["fail", "todo", "info", "pass", "na"]
INDEX_CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#e2e2e2;--card:#fafafa;}
@media (prefers-color-scheme:dark){:root{--bg:#16181c;--fg:#e6e6e6;--mut:#9aa0a6;--line:#2c2f36;--card:#1d2026;}}
*{box-sizing:border-box}body{margin:0;padding:24px 16px 80px;background:var(--bg);color:var(--fg);
 font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans JP",sans-serif;line-height:1.6;
 max-width:960px;margin-inline:auto}
h1{font-size:1.4rem;margin:0 0 4px}.meta{color:var(--mut);font-size:.85rem;margin-bottom:18px}
a.card{display:block;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:10px;
 padding:12px 16px;margin:10px 0;background:var(--card)}
a.card:hover{border-color:var(--mut)}
.folder{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.9rem}
.title{font-weight:700;margin:2px 0}
.sub{color:var(--mut);font-size:.82rem}
.chips{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap}
.chip{font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:999px;border:1px solid var(--line)}
.c-fail{background:#fdeaea;color:#c62828} .c-todo{background:#fff5e6;color:#b26a00}
.c-info{background:#eaf2fd;color:#1565c0} .c-pass{background:#e7f6ec;color:#0a7c33} .c-na{background:#eee;color:#666}
.empty{color:var(--mut);font-style:italic}
"""


def build_index_html(root: Path) -> bytes:
    """配信ルート直下の、run.yaml を持つアクティビティ一覧ページを組む。"""
    acts = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        rp = d / "run.yaml"
        if not rp.exists():
            continue
        try:
            y = yaml.safe_load(rp.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            y = {}
        covers = y.get("covers") or []
        cnt = Counter(str(c.get("verdict", "todo")) for c in covers)
        acts.append({"folder": d.name, "title": str(y.get("title", "")),
                     "target": str(y.get("target_scope", "") or ""),
                     "date": str(y.get("date", "") or ""), "cnt": cnt, "n": len(covers)})

    rows = []
    for a in acts:
        chips = "".join(
            f'<span class="chip c-{v}">{v} {a["cnt"][v]}</span>'
            for v in VERDICTS if a["cnt"].get(v))
        sub = " · ".join(x for x in [a["target"] and ("対象 " + a["target"]),
                                     a["date"] and ("date " + a["date"]),
                                     f'{a["n"]} 項目'] if x)
        rows.append(
            f'<a class="card" href="{html.escape(a["folder"])}/record.html">'
            f'<div class="folder">{html.escape(a["folder"])}</div>'
            f'<div class="title">{html.escape(a["title"])}</div>'
            f'<div class="sub">{html.escape(sub)}</div>'
            f'<div class="chips">{chips}</div></a>')
    body = "\n".join(rows) or '<p class="empty">run.yaml を持つアクティビティがありません。' \
        'uv run scripts/new_activity.py &lt;activity_id&gt; で作成してください。</p>'
    doc = (f'<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">'
           f'<meta name="viewport" content="width=device-width, initial-scale=1">'
           f'<title>実施記録 索引</title><style>{INDEX_CSS}</style></head><body>'
           f'<h1>実施記録 — 索引</h1>'
           f'<div class="meta">{html.escape(root.as_posix())} · {len(acts)} アクティビティ</div>'
           f'{body}</body></html>')
    return doc.encode("utf-8")


class RecordHandler(SimpleHTTPRequestHandler):
    root: Path = Path(".")     # build_server が差し替える（配信ルート＝evidence 相当）

    # --- 共通 ---
    def _json(self, code: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def _activity(self, route: str):
        """URL 先頭セグメント（/<フォルダ>/...）から run.yaml を持つ活動フォルダを引く。"""
        seg = route.strip("/").split("/", 1)[0]
        if not seg:
            return None
        act = (self.root / seg).resolve()
        if act.parent != self.root.resolve() or not (act / "run.yaml").exists():
            return None
        return act

    # --- GET ---
    def do_GET(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        if route in ("/", "/index.html"):
            self._send_html(build_index_html(self.root))
            return
        if route.endswith(("/record.html", "/evidence.js")):
            act = self._activity(route)
            if act is not None:
                try:
                    refresh_record(act)          # findings.md / run.yaml の手編集をリロードで反映
                except SystemExit:
                    pass
        super().do_GET()

    # --- POST ---
    def do_POST(self) -> None:  # noqa: N802
        route = self.path.split("?", 1)[0]
        act = self._activity(route)
        if act is None:
            self._json(404, {"ok": False, "error": "対象アクティビティが見つかりません"})
            return
        if route.endswith("/api/capture"):
            self._capture(act)
        elif route.endswith("/api/delete_shot"):
            self._delete_shot(act)
        elif route.endswith("/api/save"):
            self._save(act)
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def _save(self, act: Path) -> None:
        """run.yaml の verdict/finding と findings.md の本文を、テキスト部分置換で更新する。"""
        data = self._read_json()
        if data is None:
            self._json(200, {"ok": False, "error": "リクエストが不正です"})
            return
        wid = str(data.get("wid", ""))
        if not WID_RE.match(wid):
            self._json(200, {"ok": False, "error": f"WSTG-ID の形式が不正です: {wid}"})
            return
        verdict = data.get("verdict")
        if verdict is not None:
            verdict = str(verdict)
            if verdict not in VALID_VERDICTS:
                self._json(200, {"ok": False, "error": f"verdict が不正です: {verdict}"})
                return
        finding = data.get("finding")
        writeup = data.get("writeup")
        try:
            if verdict is not None or finding is not None:
                ok = update_cover(act / "run.yaml", wid, verdict,
                                  (str(finding) if finding is not None else None))
                if not ok:
                    self._json(200, {"ok": False, "error": f"run.yaml に {wid} の covers がありません"})
                    return
            if writeup is not None:
                _, tests, _, _, _ = resolve_activity(act)
                update_findings(act / "findings.md", tests, wid, str(writeup))
            refresh_record(act)
        except OSError as exc:
            self._json(200, {"ok": False, "error": str(exc)})
            return
        self._json(200, {"ok": True})

    def _delete_shot(self, act: Path) -> None:
        data = self._read_json()
        if data is None:
            self._json(200, {"ok": False, "error": "リクエストが不正です"})
            return
        rel = str(data.get("path", ""))
        base = (act / "artifacts").resolve()
        target = (act / rel).resolve()
        if target.parent != base or not SHOT_RE.match(target.name):
            self._json(200, {"ok": False, "error": f"削除できるのは artifacts/shot-*.png だけです: {rel}"})
            return
        if not target.exists():
            self._json(200, {"ok": False, "error": f"見つかりません: {rel}"})
            return
        try:
            target.unlink()
            refresh_record(act)
        except OSError as exc:
            self._json(200, {"ok": False, "error": str(exc)})
            return
        self._json(200, {"ok": True, "deleted": rel})

    def _capture(self, act: Path) -> None:
        data = self._read_json()
        if data is None:
            self._json(200, {"ok": False, "error": "リクエストが不正です"})
            return
        wid = str(data.get("wid", ""))
        if not WID_RE.match(wid):
            self._json(200, {"ok": False, "error": f"WSTG-ID の形式が不正です: {wid}"})
            return
        argv = [sys.executable, str(SAVE_SHOT), str(act), "--wid", wid, "--grab", "--force"]
        step = data.get("step")
        if isinstance(step, int) or (isinstance(step, str) and str(step).isdigit()):
            argv += ["--step", str(int(step))]
        try:
            delay = max(0, min(60, int(data.get("delay", 0) or 0)))
        except (TypeError, ValueError):
            delay = 0
        argv += ["--delay", str(delay)]
        try:
            proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self._json(200, {"ok": False, "error": "タイムアウト（範囲選択がされませんでした）"})
            return
        if proc.returncode == 0:
            self._json(200, {"ok": True, "out": proc.stdout.strip()})
        else:
            self._json(200, {"ok": False, "error": (proc.stderr or proc.stdout).strip()[:800]})

    def log_message(self, fmt, *args):
        if self.command == "POST" or (args and str(args[0]).startswith(("4", "5"))):
            super().log_message(fmt, *args)


def build_server(root: Path, host: str = "127.0.0.1", port: int = 8765):
    """root（evidence 相当）を配信する httpd を返す（serve は呼び側）。テスト・本体共用。"""
    RecordHandler.root = root.resolve()
    handler = partial(RecordHandler, directory=str(root))
    return ThreadingHTTPServer((host, port), handler)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=str(SCRIPTS.parent / "evidence"),
                    help="配信する evidence ルート、または単一の活動フォルダ（既定: evidence/）")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1", help="既定は 127.0.0.1（外部に晒さない）")
    ap.add_argument("--open", action="store_true", help="ブラウザで開く（活動指定ならその record.html）")
    args = ap.parse_args()

    given = Path(args.path)
    open_path = "/"
    if (given / "run.yaml").exists():          # 活動フォルダを渡された → 親を配信し、それを開く
        root, open_path = given.parent, f"/{given.name}/record.html"
    else:
        root = given
    if not root.exists():
        print(f"配信フォルダがありません: {root}", file=sys.stderr)
        print("  uv run scripts/new_activity.py <activity_id> で先に作成してください。", file=sys.stderr)
        return 2

    try:
        httpd = build_server(root, args.host, args.port)
    except OSError as exc:
        print(f"ポート {args.port} を開けません: {exc}", file=sys.stderr)
        print("  --port で別のポートを指定してください。", file=sys.stderr)
        return 1

    base = f"http://{args.host}:{args.port}"
    print(f"[serve_record] 配信中: {base}/   （索引）")
    print(f"  ルート: {root}")
    print("  索引から各アクティビティの record.html を開く。撮影/削除ボタンも各ページで有効。停止は Ctrl+C。")
    if args.open:
        webbrowser.open(base + open_path)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve_record] 停止しました。")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
