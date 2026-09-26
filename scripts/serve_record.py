#!/usr/bin/env python3
"""evidence/ 全体を1つのサーバで配信する Web（ダッシュボード・タスク・WSTG 索引・所見・実施記録）。

    uv run scripts/serve_record.py                 # evidence/ を配信（http://127.0.0.1:8765/）
    uv run scripts/serve_record.py --open          # ダッシュボードをブラウザで開く
    uv run scripts/serve_record.py evidence/<act>  # そのアクティビティの record.html を開く
    uv run scripts/serve_record.py --behind-proxy --owners alice,bob
                                                   # チーム共有（nginx の後ろ。templates/nginx/ 参照）

ページ（描画は scripts/web_pages.py）:
    /  /tasks  /wstg/  /wstg/<ID>  /findings/  /findings/<F-ID>  /playbooks/<ID>  /export.csv
    /<フォルダ>/record.html   各アクティビティの実施記録（撮影・画像追加・判定の編集・所見への添付）

書き込み API（POST。すべて独自ヘッダ X-WSTG-Request: 1 が必須＝CSRF 対策）:
    /api/check                    タスクの手動チェック（evidence/_state/checks.yaml）
    /api/finding/save, /attach    所見の作成・更新・エビデンス添付（evidence/_findings/）
    /<フォルダ>/api/save           run.yaml の verdict / finding（判定理由）をテキスト部分置換
    /<フォルダ>/api/save_output    cmd/・artifacts/ 直下の .txt に貼る（別環境で取った結果）
    /<フォルダ>/api/edit_cmd       手順のコマンドを編集（run.yaml の cmd_overrides。空で既定に戻す）
    /<フォルダ>/api/upload_shot    ブラウザから貼った画像を artifacts/shot-*.png に保存
    /<フォルダ>/api/delete_shot    artifacts/shot-*.png を削除
    /<フォルダ>/api/capture        サーバ機のデスクトップを撮影（--behind-proxy では無効）

常に 127.0.0.1 で待ち受ける。チームで共有するときは同じ機械の nginx から proxy し、
nginx 側で TLS と認証（Basic 認証等）をかける。--behind-proxy のときは nginx が渡す
X-Remote-User を編集者名として記録し、サーバ機のデスクトップを撮る capture を無効にする。

利用者の権限（--behind-proxy のとき）:
    owner    --owners に名前がある利用者（WSTG を実施する人）。書き込み API・編集フォームを使える
    閲覧専用  それ以外の認証済み利用者（結果を見るだけの人）。書き込み API は 403、編集ボタンは出ない
    --owners を省くと全員が閲覧専用になる（書ける人を明示しない限り誰も書けない）。
    ローカルモード（--behind-proxy なし）は常に owner。
書き込みは1プロセス内のロックで直列化し、所見は読み込み時の版（rev）と違えば保存を拒否する。
"""

from __future__ import annotations

import argparse
import base64
import getpass
import ipaddress
import json
import re
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import yaml

SCRIPTS = Path(__file__).resolve().parent
SAVE_SHOT = SCRIPTS / "save_shot.py"
WID_RE = re.compile(r"^WSTG-[A-Z]+-\d+$")
SHOT_RE = re.compile(r"^shot-.*\.png$")
CHECK_KEY_RE = re.compile(r"^[A-Za-z0-9:._-]{1,160}$")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_BODY = 20 * 1024 * 1024
WRITE_LOCK = threading.RLock()   # 書き込み（と record の再生成）を直列化する
READONLY_MSG = ("閲覧専用ユーザなので編集できません。編集が必要なら、"
                "サーバの管理者に serve_record.py の --owners へ追加してもらってください。")

sys.path.insert(0, str(SCRIPTS))
import cvss31  # noqa: E402
import findings as fnd  # noqa: E402
import web_pages  # noqa: E402
from export_checklist import build_rows, collect_runs, to_csv  # noqa: E402
from new_activity import (  # noqa: E402
    refresh_record, update_cover, VALID_VERDICTS, set_cmd_override, OVERRIDE_KEY_RE,
)
from save_shot import make_name  # noqa: E402


class RecordHandler(SimpleHTTPRequestHandler):
    root: Path = Path(".")        # build_server が差し替える（配信ルート＝evidence 相当）
    behind_proxy: bool = False    # nginx 経由（X-Remote-User を信用・capture 無効）
    owners: frozenset = frozenset()   # --behind-proxy で書き込める利用者（それ以外は閲覧専用）

    # --- 共通 ---
    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _html(self, text: str | None) -> None:
        if text is None:
            self._html_error(404, "見つかりません")
            return
        self._send(200, text.encode("utf-8"), "text/html; charset=utf-8")

    def _html_error(self, code: int, msg: str) -> None:
        body = (f'<!DOCTYPE html><meta charset="utf-8"><title>{code}</title>'
                f'<p>{msg}</p><p><a href="/">ダッシュボードへ</a></p>').encode("utf-8")
        self._send(code, body, "text/html; charset=utf-8")

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        super().end_headers()

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY:
                return None
            return json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def user(self) -> str:
        """編集者名。nginx 経由なら X-Remote-User（Basic 認証のユーザ）、直アクセスなら OS のユーザ。"""
        if self.behind_proxy:
            return clean_user(self.headers.get("X-Remote-User") or "") or "unknown"
        try:
            return getpass.getuser()
        except (KeyError, OSError):
            return "local"

    def can_edit(self) -> bool:
        """書き込めるか。ローカルモードは常に可、共有モードは --owners に名前がある利用者だけ。"""
        return not self.behind_proxy or self.user() in self.owners

    def site(self) -> web_pages.Site:
        return web_pages.Site(self.root, self.user() if self.behind_proxy else "", self.capture_enabled(),
                              self.can_edit())

    def capture_enabled(self) -> bool:
        return not self.behind_proxy

    def _activity(self, route: str):
        """URL 先頭セグメント（/<フォルダ>/...）から run.yaml を持つ活動フォルダを引く。"""
        seg = unquote(route.strip("/").split("/", 1)[0])
        if not seg or seg.startswith((".", "_")):
            return None
        act = (self.root / seg).resolve()
        if act.parent != self.root.resolve() or not (act / "run.yaml").exists():
            return None
        return act

    # --- GET ---
    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        route = unquote(url.path)
        qs = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if self._get_page(route, qs):
                return
        except Exception as exc:  # noqa: BLE001 — ページ描画の失敗は 500 で見せる（サーバは落とさない）
            self.log_error("ページ描画に失敗: %s", exc)
            self._html_error(500, f"ページを作れませんでした: {type(exc).__name__}: {exc}")
            return
        if any(p.startswith(".") for p in route.split("/") if p):
            self._html_error(404, "見つかりません")
            return
        if route.endswith(("/record.html", "/evidence.js")):
            act = self._activity(route)
            if act is not None:
                try:
                    with WRITE_LOCK:
                        refresh_record(act)      # run.yaml・所見の手編集をリロードで反映
                except SystemExit:
                    pass
        super().do_GET()

    def _get_page(self, route: str, qs: dict) -> bool:
        """アプリのページなら描画して True。静的ファイルは False（呼び側が配信）。"""
        if route in ("/", "/index.html"):
            self._html(web_pages.page_dashboard(self.site()))
        elif route == "/tasks":
            self._html(web_pages.page_tasks(self.site()))
        elif route in ("/wstg", "/wstg/"):
            self._html(web_pages.page_wstg_index(self.site()))
        elif m := re.match(r"^/wstg/(WSTG-[A-Z]+-\d+)$", route):
            self._html(web_pages.page_wstg_detail(self.site(), m.group(1)))
        elif m := re.match(r"^/playbooks/(WSTG-[A-Z]+-\d+)(?:\.md)?$", route):
            self._html(web_pages.page_playbook(self.site(), m.group(1)))
        elif route in ("/findings", "/findings/"):
            self._html(web_pages.page_findings(self.site(), qs.get("status", ""), qs.get("wid", "")))
        elif route in ("/findings/new", "/findings/attach") or re.match(r"^/findings/F-\d{3,}/edit$", route):
            if not self.can_edit():
                self._html_error(403, READONLY_MSG)
                return True
            return self._get_form(route, qs)
        elif m := re.match(r"^/findings/(F-\d{3,})$", route):
            self._html(web_pages.page_finding(self.site(), m.group(1)))
        elif route == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        elif route == "/export.csv":
            self._export_csv()
        elif route == "/api/info":
            self._json(200, {"capture": self.capture_enabled(),
                             "user": self.user() if self.behind_proxy else "",
                             "editable": self.can_edit()})
        elif route == "/api/cvss":
            try:
                self._json(200, {"ok": True, "score": cvss31.score(qs.get("vector", "")),
                                 "expl_max": cvss31.EXPL_MAX, "impact_max": cvss31.IMPACT_MAX})
            except cvss31.CvssError as exc:
                self._json(200, {"ok": False, "error": str(exc)})
        else:
            return False
        return True

    def _get_form(self, route: str, qs: dict) -> bool:
        """所見の作成・編集・添付フォーム（owner だけ。呼び側で権限を確認済み）。"""
        if route == "/findings/new":
            self._html(web_pages.page_finding_form(self.site(), "", qs.get("wid", ""), qs.get("ev", "")))
        elif route == "/findings/attach":
            self._html(web_pages.page_attach(self.site(), qs.get("wid", ""), qs.get("ev", "")))
        elif m := re.match(r"^/findings/(F-\d{3,})/edit$", route):
            self._html(web_pages.page_finding_form(self.site(), m.group(1)))
        return True

    def _export_csv(self) -> None:
        tests = {t["id"]: t for t in yaml.safe_load(web_pages.WSTG_TESTS.read_text(encoding="utf-8"))["tests"]}
        rows, _ = build_rows(tests, collect_runs(self.root), self.root, fnd.list_all(self.root))
        body = to_csv(rows).encode("utf-8-sig")
        name = f"checklist_export-{datetime.now():%Y%m%d}.csv"
        self._send(200, body, "text/csv; charset=utf-8",
                   {"Content-Disposition": f'attachment; filename="{name}"'})

    # --- POST ---
    def _csrf_ok(self) -> bool:
        """ブラウザの他サイトからの書き込みを弾く（独自ヘッダ＋Origin の一致）。"""
        if self.headers.get("X-WSTG-Request") != "1":
            return False
        origin = self.headers.get("Origin")
        if origin and urlparse(origin).netloc != self.headers.get("Host", ""):
            return False
        return True

    def do_POST(self) -> None:  # noqa: N802
        route = unquote(urlparse(self.path).path)
        if not self._csrf_ok():
            self._json(403, {"ok": False, "error": "不正なリクエストです（X-WSTG-Request ヘッダ / Origin）"})
            return
        if not self.can_edit():
            self._json(403, {"ok": False, "error": READONLY_MSG})
            return
        data = self._read_json()
        if data is None or not isinstance(data, dict):
            self._json(400, {"ok": False, "error": "リクエストが不正です（JSON・20MB 以内）"})
            return
        with WRITE_LOCK:
            try:
                self._dispatch_post(route, data)
            except OSError as exc:
                self._json(200, {"ok": False, "error": str(exc)})

    def _dispatch_post(self, route: str, data: dict) -> None:
        if route == "/api/check":
            self._check(data)
            return
        if route == "/api/finding/save":
            self._finding_save(data)
            return
        if route == "/api/finding/attach":
            self._finding_attach(data)
            return
        act = self._activity(route)
        if act is None:
            self._json(404, {"ok": False, "error": "対象アクティビティが見つかりません"})
            return
        handlers = {"/api/capture": self._capture, "/api/delete_shot": self._delete_shot,
                    "/api/save": self._save, "/api/save_output": self._save_output,
                    "/api/edit_cmd": self._edit_cmd, "/api/upload_shot": self._upload_shot}
        for suffix, fn in handlers.items():
            if route.endswith(suffix):
                fn(act, data)
                return
        self._json(404, {"ok": False, "error": "not found"})

    # --- 手動チェック・所見 ---
    def _check(self, data: dict) -> None:
        key = str(data.get("key", ""))
        if not CHECK_KEY_RE.match(key):
            self._json(200, {"ok": False, "error": f"キーが不正です: {key}"})
            return
        path = self.root / web_pages.STATE_FILE
        checks = web_pages.load_checks(self.root)
        label = ""
        if data.get("on"):
            now = datetime.now().astimezone().isoformat(timespec="seconds")
            checks[key] = {"by": self.user(), "at": now}
            label = f"{self.user()} {now[:16].replace('T', ' ')}"
        else:
            checks.pop(key, None)
        path.parent.mkdir(parents=True, exist_ok=True)
        # 機械だけが書く状態ファイル（run.yaml と違い手記録のコメントは無い）なので丸ごと書き出す
        path.write_text("# 自動生成: Web のタスクページの手動チェック（誰がいつ押したか）\n"
                        + yaml.safe_dump(checks, allow_unicode=True, sort_keys=True), encoding="utf-8")
        self._json(200, {"ok": True, "label": label})

    def _tests(self) -> dict:
        return {t["id"]: t for t in yaml.safe_load(web_pages.WSTG_TESTS.read_text(encoding="utf-8"))["tests"]}

    def _finding_save(self, data: dict) -> None:
        fid = data.get("id") or ""
        try:
            fields = fnd.validate(self.root, data, self._tests())
            if fid:
                if not fnd.ID_RE.match(str(fid)):
                    raise fnd.FindingError(f"所見 ID が不正です: {fid}")
                fnd.save(self.root, str(fid), fields, self.user(), data.get("rev") or None)
            else:
                fid = fnd.create(self.root, fields, self.user())
        except fnd.FindingError as exc:
            self._json(200, {"ok": False, "error": str(exc)})
            return
        except fnd.Conflict:
            self._json(409, {"ok": False, "error": "ほかの人が先にこの所見を更新しました。"
                                                   "内容を控えてからページを開き直し、反映し直してください。"})
            return
        self._json(200, {"ok": True, "id": fid})

    def _finding_attach(self, data: dict) -> None:
        fid, ev, wid = str(data.get("id", "")), str(data.get("ev", "")), str(data.get("wid", ""))
        try:
            fnd.attach(self.root, fid, ev, wid if WID_RE.match(wid) else None, self.user())
        except fnd.FindingError as exc:
            self._json(200, {"ok": False, "error": str(exc)})
            return
        except fnd.Conflict:
            self._json(409, {"ok": False, "error": "同時に更新されました。もう一度押してください。"})
            return
        self._json(200, {"ok": True, "id": fid})

    # --- アクティビティ単位 ---
    def _edit_cmd(self, act: Path, data: dict) -> None:
        """手順のコマンドを編集する（run.yaml の cmd_overrides に保存）。空なら既定（criteria）に戻す。

        cmd/<WSTG-ID>-s<n>-c<k>.txt に対応する main コマンドだけ編集できる。保存後は cmd 行が
        変わるので、次の run_target（--skip-done でも）で「コマンドが変わった」として再実行される。
        """
        key = str(data.get("key", ""))
        cmd = data.get("cmd", "")
        if not OVERRIDE_KEY_RE.match(key):
            self._json(200, {"ok": False, "error": f"手順キーが不正です: {key}"})
            return
        if not isinstance(cmd, str) or len(cmd) > 100_000 or "\n" in cmd:
            self._json(200, {"ok": False, "error": "コマンドが不正です（1行・10万字以内）"})
            return
        set_cmd_override(act, key, cmd.strip())
        refresh_record(act)
        self._json(200, {"ok": True})

    def _save_output(self, act: Path, data: dict) -> None:
        """コマンド出力/手動観察のファイル（cmd/・artifacts/ 直下の .txt）に本文を書き込む。

        会社で network error になったコマンドを自宅で実行して結果を貼る、等の用途。
        書けるのは cmd/・artifacts/ 直下の .txt だけ（run.yaml・スクショ等は不可）。
        """
        rel = str(data.get("path", ""))
        content = data.get("content")
        if not isinstance(content, str) or len(content) > 10_000_000:
            self._json(200, {"ok": False, "error": "content が不正です（文字列・10MB 以内）"})
            return
        target = (act / rel).resolve()
        allowed = {(act / "cmd").resolve(), (act / "artifacts").resolve()}
        if target.parent not in allowed or target.suffix.lower() != ".txt":
            self._json(200, {"ok": False, "error": f"編集できるのは cmd/・artifacts/ 直下の .txt だけです: {rel}"})
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        refresh_record(act)
        self._json(200, {"ok": True})

    def _save(self, act: Path, data: dict) -> None:
        """run.yaml の verdict / finding（判定理由）を、テキスト部分置換で更新する。"""
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
        if verdict is not None or finding is not None:
            ok = update_cover(act / "run.yaml", wid, verdict, (str(finding) if finding is not None else None))
            if not ok:
                self._json(200, {"ok": False, "error": f"run.yaml に {wid} の covers がありません"})
                return
        refresh_record(act)
        self._json(200, {"ok": True})

    def _upload_shot(self, act: Path, data: dict) -> None:
        """ブラウザから送られた PNG（base64）を artifacts/shot-<WID>[-s<n>]-<日時>.png に保存する。"""
        wid = str(data.get("wid", ""))
        if not WID_RE.match(wid):
            self._json(200, {"ok": False, "error": f"WSTG-ID の形式が不正です: {wid}"})
            return
        step = data.get("step")
        step = int(step) if isinstance(step, int) or (isinstance(step, str) and step.isdigit()) else None
        try:
            png = base64.b64decode(str(data.get("data", "")), validate=True)
        except (ValueError, TypeError):
            self._json(200, {"ok": False, "error": "画像データが不正です"})
            return
        if not png.startswith(PNG_MAGIC):
            self._json(200, {"ok": False, "error": "PNG ではありません（ブラウザ側で PNG に変換して送ります）"})
            return
        art = act / "artifacts"
        art.mkdir(parents=True, exist_ok=True)
        dest = art / make_name(wid, step, None)
        n = 1
        while dest.exists():
            dest = art / make_name(wid, step, None).replace(".png", f"-{n}.png")
            n += 1
        dest.write_bytes(png)
        refresh_record(act)
        self._json(200, {"ok": True, "path": f"artifacts/{dest.name}"})

    def _delete_shot(self, act: Path, data: dict) -> None:
        rel = str(data.get("path", ""))
        base = (act / "artifacts").resolve()
        target = (act / rel).resolve()
        if target.parent != base or not SHOT_RE.match(target.name):
            self._json(200, {"ok": False, "error": f"削除できるのは artifacts/shot-*.png だけです: {rel}"})
            return
        if not target.exists():
            self._json(200, {"ok": False, "error": f"見つかりません: {rel}"})
            return
        target.unlink()
        refresh_record(act)
        self._json(200, {"ok": True, "deleted": rel})

    def _capture(self, act: Path, data: dict) -> None:
        if not self.capture_enabled():
            self._json(200, {"ok": False, "error": "共有モード（--behind-proxy）ではサーバ機の画面は撮れません。"
                                                   "手元で撮って『画像を貼り付け』を使ってください。"})
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
        # 撮影は待ち時間があるのでロックを外して実行する（その間も他の人が保存できるように）
        WRITE_LOCK.release()
        try:
            proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, timeout=180)
        except subprocess.TimeoutExpired:
            self._json(200, {"ok": False, "error": "タイムアウト（範囲選択がされませんでした）"})
            return
        finally:
            WRITE_LOCK.acquire()
        if proc.returncode == 0:
            self._json(200, {"ok": True, "out": proc.stdout.strip()})
        else:
            self._json(200, {"ok": False, "error": (proc.stderr or proc.stdout).strip()[:800]})

    def log_message(self, fmt, *args):
        if self.command == "POST" or (args and str(args[0]).startswith(("4", "5"))):
            super().log_message(fmt, *args)


def clean_user(name: str) -> str:
    """利用者名を記録・照合用に正規化する（X-Remote-User と --owners の両方に同じ規則を使う）。"""
    return re.sub(r"[^\w.@-]", "", name.strip())[:64]


def parse_owners(values) -> frozenset:
    """--owners（カンマ区切り・複数回可）を利用者名の集合にする。"""
    return frozenset(u for v in values or [] for u in (clean_user(x) for x in v.split(",")) if u)


def build_server(root: Path, host: str = "127.0.0.1", port: int = 8765, behind_proxy: bool = False,
                 owners=frozenset()):
    """root（evidence 相当）を配信する httpd を返す（serve は呼び側）。テスト・本体共用。"""
    RecordHandler.root = root.resolve()
    RecordHandler.behind_proxy = behind_proxy
    RecordHandler.owners = frozenset(owners)
    handler = partial(RecordHandler, directory=str(root))
    return ThreadingHTTPServer((host, port), handler)


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return host == "localhost"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", default=str(SCRIPTS.parent / "evidence"),
                    help="配信する evidence ルート、または単一の活動フォルダ（既定: evidence/）")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1",
                    help="待受アドレス。既定 127.0.0.1 のまま使い、共有は nginx 経由にする")
    ap.add_argument("--behind-proxy", action="store_true",
                    help="nginx の後ろで動かす（X-Remote-User を編集者名に使い、サーバ画面の撮影を無効化）")
    ap.add_argument("--owners", action="append", metavar="USER[,USER...]",
                    help="--behind-proxy で編集できる利用者（nginx の認証ユーザ名。カンマ区切り・複数回可）。"
                         "ほかの利用者は閲覧専用。省くと全員が閲覧専用")
    ap.add_argument("--open", action="store_true", help="ブラウザで開く（活動指定ならその record.html）")
    args = ap.parse_args()

    owners = parse_owners(args.owners)
    if owners and not args.behind_proxy:
        print("--owners は --behind-proxy と一緒に使います（ローカルモードは常に編集できます）。", file=sys.stderr)
        return 2

    if not _is_loopback(args.host):
        print(f"--host {args.host} は使えません。認証なしで evidence が外から見えてしまいます。", file=sys.stderr)
        print("  127.0.0.1 のまま起動し、nginx（TLS＋認証）から proxy してください: templates/nginx/wstg.conf",
              file=sys.stderr)
        return 2

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
        httpd = build_server(root, args.host, args.port, args.behind_proxy, owners)
    except OSError as exc:
        print(f"ポート {args.port} を開けません: {exc}", file=sys.stderr)
        print("  --port で別のポートを指定してください。", file=sys.stderr)
        return 1

    base = f"http://{args.host}:{args.port}"
    print(f"[serve_record] 配信中: {base}/   （ダッシュボード）")
    print(f"  ルート: {root}")
    if args.behind_proxy:
        print("  共有モード: nginx 経由でアクセスする（編集者名は X-Remote-User。サーバ画面の撮影は無効）。")
        if owners:
            print(f"  編集できる利用者（owner）: {', '.join(sorted(owners))}。ほかの利用者は閲覧専用。")
        else:
            print("  --owners の指定がないので全員が閲覧専用です。実施者は --owners alice,bob のように指定してください。")
    else:
        print("  ローカルモード: この機械のブラウザから使う。チーム共有は --behind-proxy と nginx で。")
    print("  停止は Ctrl+C。")
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
