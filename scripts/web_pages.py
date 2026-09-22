#!/usr/bin/env python3
"""Web（serve_record.py）のページを組み立てる。サーバ本体からだけ呼ばれる描画モジュール。

    uv run scripts/web_pages.py --root <evidence> --out-dir <tmp>   # 静的に書き出して確認する（任意）

ページ:
    /                    ダッシュボード（WSTG の完了数・所見の深刻度・次にやること・アクティビティ一覧）
    /tasks               指示書＋チェックリスト（自動チェック＋手動チェック）＋エビデンスへのリンク
    /wstg/               WSTG 索引（カテゴリ別・完了状況・実施記録と所見へのリンク）
    /wstg/<WSTG-ID>      1項目の判定・実施記録・所見・カード
    /findings/           所見一覧（深刻度順）
    /findings/<F-ID>     所見の詳細（CVSS 内訳・エビデンスへの深いリンク）
    /findings/new, /findings/<F-ID>/edit   所見の作成・編集フォーム（CVSS は設問形式）
    /findings/attach     エビデンスを所見に添付（新規 or 既存を選ぶ）
    /playbooks/<WSTG-ID> カード（playbooks/*.md）を HTML にしたもの

データの置き場は変えない: 判定は run.yaml、所見は evidence/_findings/、手動チェックは
evidence/_state/checks.yaml、エビデンス本体は cmd/・artifacts/。ここは読むだけ（書くのはサーバ）。
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode

import yaml

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
PLAYBOOKS = REPO_ROOT / "playbooks"
sys.path.insert(0, str(SCRIPTS))

import cvss31  # noqa: E402
import findings as fnd  # noqa: E402
from export_checklist import build_rows, collect_runs  # noqa: E402
from tasks import (  # noqa: E402
    COVERAGE_YAML, CRITERIA_YAML, IMPACT_LABEL, WSTG_TESTS, render_phase_setup, sorted_activities,
)

VERDICTS = ["fail", "todo", "info", "pass", "na"]
VERDICT_LABEL = {"fail": "FAIL", "todo": "未実施", "info": "INFO", "pass": "PASS", "na": "N/A"}
STATE_FILE = Path("_state") / "checks.yaml"
E = html.escape

# CVSS の参考例（新人向け。「そのまま使わず、確認できた事実に合わせて選び直す」前提）
CVSS_EXAMPLES = [
    ("反射型 XSS（リンクを踏ませる）", "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N"),
    ("未認証の SQL インジェクション（DB を読み書き）", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
    ("IDOR（一般ユーザが他人の個人情報を閲覧）", "CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N"),
    ("CSRF（被害者の設定を書き換え）", "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N"),
    ("Cookie に Secure 属性なし（盗聴できる位置が前提）", "CVSS:3.1/AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:N/A:N"),
    ("バージョン情報の露出（それ自体の被害なし）", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"),
]


# --- データ ---------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}


def load_checks(root: Path) -> dict:
    p = Path(root) / STATE_FILE
    try:
        data = _load_yaml(p) or {}
    except yaml.YAMLError:
        data = {}
    return data if isinstance(data, dict) else {}


class Site:
    """1リクエスト分のスナップショット（毎回ファイルから読み直す＝手編集も即反映）。"""

    def __init__(self, root: Path, user: str = "", capture: bool = False):
        self.root = Path(root)
        self.user = user
        self.capture = capture
        self.coverage = _load_yaml(COVERAGE_YAML)
        self.tests = {t["id"]: t for t in _load_yaml(WSTG_TESTS)["tests"]}
        self.criteria = _load_yaml(CRITERIA_YAML) or {}
        self.activities = sorted_activities(self.coverage)
        self.act_by_id = {a["id"]: a for a in self.activities}
        self.runs = collect_runs(self.root) if self.root.exists() else []
        self.findings = fnd.list_all(self.root)
        self.f_by_wstg = fnd.by_wstg(self.findings)
        self.rows = {r["wstg_id"]: r for r in build_rows(self.tests, self.runs, self.root, self.findings)[0]}
        self.checks = load_checks(self.root)
        # WSTG-ID → [(folder, activity_id, verdict, finding, role)]
        self.wstg_runs: dict = {}
        # activity_id → [(folder, run.yaml の中身)]
        self.act_runs: dict = {}
        for d, data in self.runs:
            aid = data.get("activity_id")
            self.act_runs.setdefault(aid, []).append((d, data))
            roles = {c["id"]: c.get("role", "primary")
                     for c in (self.act_by_id.get(aid, {}).get("covers") or [])}
            for c in data.get("covers") or []:
                if isinstance(c, dict) and c.get("id"):
                    self.wstg_runs.setdefault(c["id"], []).append(
                        (d.name, aid, str(c.get("verdict", "todo")).lower(),
                         str(c.get("finding") or ""), roles.get(c["id"], "primary")))

    # 集計
    def active_tests(self) -> list:
        return [w for w, t in self.tests.items() if not t.get("deprecated")]

    def wstg_done(self) -> int:
        return sum(1 for w in self.active_tests() if self.rows[w]["status"] != "todo")

    def act_state(self, aid: str) -> str:
        runs = self.act_runs.get(aid) or []
        if not runs:
            return "todo"
        for _, data in runs:
            covers = [c for c in (data.get("covers") or []) if isinstance(c, dict)]
            if covers and all(str(c.get("verdict", "todo")).lower() != "todo" for c in covers):
                continue
            return "doing"
        return "done"


# --- 共通レイアウト ---------------------------------------------------------

CSS = """
:root{--bg:#fff;--fg:#1a1a1a;--mut:#666;--line:#e2e2e2;--card:#fafafa;--pre:#f4f4f4;
 --cmd:#0b3d2e;--cmdbg:#eaf5ef;--acc:#1565c0;}
@media (prefers-color-scheme:dark){:root{--bg:#16181c;--fg:#e6e6e6;--mut:#9aa0a6;--line:#2c2f36;
 --card:#1d2026;--pre:#111318;--cmd:#8fe3c0;--cmdbg:#12251d;--acc:#7fb2f0;}}
*{box-sizing:border-box}
body{margin:0;padding:16px 16px 80px;background:var(--bg);color:var(--fg);
 font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Noto Sans JP",sans-serif;line-height:1.6;
 max-width:1080px;margin-inline:auto}
a{color:var(--acc)}
nav.nav{display:flex;gap:16px;flex-wrap:wrap;align-items:center;font-size:.9rem;margin:0 0 18px;
 padding-bottom:10px;border-bottom:1px solid var(--line)}
nav.nav a{color:inherit;text-decoration:none} nav.nav a.on{font-weight:700;border-bottom:2px solid var(--acc)}
nav.nav .who{margin-left:auto;color:var(--mut);font-size:.8rem}
h1{font-size:1.4rem;margin:0 0 4px} h2{font-size:1.1rem;margin:28px 0 8px}
h3{font-size:1rem;margin:18px 0 6px}
.meta,.mut{color:var(--mut);font-size:.85rem}
.card{border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:10px 0;background:var(--card)}
a.card{display:block;text-decoration:none;color:inherit} a.card:hover{border-color:var(--mut)}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88rem}
.chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.chip{font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.c-fail{background:#fdeaea;color:#c62828} .c-todo{background:#fff5e6;color:#b26a00}
.c-info{background:#eaf2fd;color:#1565c0} .c-pass{background:#e7f6ec;color:#0a7c33} .c-na{background:#eee;color:#666}
.c-done{background:#e7f6ec;color:#0a7c33} .c-doing{background:#fff5e6;color:#b26a00}
.sev{font-size:.72rem;font-weight:700;padding:2px 8px;border-radius:999px;white-space:nowrap}
.s-critical{background:#6a1b1b;color:#fff}.s-high{background:#c62828;color:#fff}
.s-medium{background:#ef8a00;color:#fff}.s-low{background:#e3c200;color:#222}
.s-none{background:#1565c0;color:#fff}.s-unrated{background:#999;color:#fff}
.st{font-size:.72rem;padding:1px 7px;border-radius:6px;border:1px solid var(--line);color:var(--mut)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin:12px 0}
.tile{border:1px solid var(--line);border-radius:10px;padding:10px 14px;background:var(--card)}
.tile .n{font-size:1.6rem;font-weight:700} .tile .l{font-size:.8rem;color:var(--mut)}
.bar{height:8px;border-radius:4px;background:var(--line);overflow:hidden;margin-top:6px}
.bar>i{display:block;height:100%;background:#0a7c33}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-size:.78rem;color:var(--mut);font-weight:600}
.tbl{overflow-x:auto}
pre{margin:6px 0;padding:10px 12px;border-radius:8px;overflow:auto;background:var(--pre);
 font:.82rem/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
code{font:.85em ui-monospace,Menlo,Consolas,monospace;background:var(--pre);padding:1px 4px;border-radius:4px}
pre code{background:none;padding:0}
.cmdbox{position:relative} .cmdbox pre{background:var(--cmdbg);color:var(--cmd);padding-right:64px}
.copy{position:absolute;top:6px;right:6px;font:inherit;font-size:.72rem;padding:2px 8px;border:1px solid var(--line);
 border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
ul.check{list-style:none;padding-left:0;margin:6px 0} ul.check li{margin:4px 0;display:flex;gap:8px;align-items:baseline}
.ck{display:inline-block;width:1.2em;text-align:center;font-weight:700}
.ck.ok{color:#0a7c33} .ck.ng{color:#b26a00} .ck.man{color:var(--acc)}
.by{font-size:.75rem;color:var(--mut)}
.warn{color:#b26a00} .bad{color:#c62828}
.btn{display:inline-block;font:inherit;font-size:.85rem;padding:5px 14px;border:1px solid var(--line);border-radius:8px;
 background:var(--cmdbg);color:var(--cmd);cursor:pointer;font-weight:700;text-decoration:none}
.btn.sub{background:transparent;color:var(--fg);font-weight:400}
.filters{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}
.filters button{font:inherit;font-size:.8rem;padding:3px 10px;border:1px solid var(--line);border-radius:999px;
 background:transparent;color:var(--fg);cursor:pointer} .filters button.on{background:var(--fg);color:var(--bg)}
.md h2{font-size:1.05rem} .md h3{font-size:.95rem} .md table{margin:8px 0}
details{margin:10px 0} summary{cursor:pointer;color:var(--mut)}
form .field{margin:12px 0} form label.l{display:block;font-size:.8rem;color:var(--mut);margin-bottom:3px}
input[type=text],textarea,select{font:inherit;width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;
 background:var(--bg);color:var(--fg)}
select{width:auto} textarea{resize:vertical} textarea.code{font:.85rem/1.5 ui-monospace,Menlo,Consolas,monospace}
fieldset{border:1px solid var(--line);border-radius:10px;margin:10px 0;padding:8px 14px}
legend{font-weight:700;font-size:.92rem;padding:0 6px}
.opt{display:flex;gap:8px;align-items:baseline;margin:4px 0;font-size:.88rem;cursor:pointer}
.opt small{color:var(--mut)}
.score{position:sticky;top:0;z-index:2;background:var(--bg);border:1px solid var(--line);border-radius:10px;
 padding:10px 14px;margin:10px 0;display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.score .big{font-size:1.5rem;font-weight:700}
.meter{min-width:200px;flex:1} .meter .bar>i{background:var(--acc)}
.ev img{max-width:100%;border:1px solid var(--line);border-radius:8px;margin:4px 0}
.ev iframe{width:100%;min-height:120px;max-height:320px;border:1px solid var(--line);border-radius:8px;background:#fff}
.hint{font-size:.82rem;color:var(--mut);border-left:3px solid var(--line);padding:4px 10px;margin:8px 0}
.empty{color:var(--mut);font-style:italic}
tr.hide{display:none}
td.mono{white-space:nowrap}
"""

COMMON_JS = r"""
function wstgPost(url, obj) {
  return fetch(url, { method: "POST",
    headers: { "Content-Type": "application/json", "X-WSTG-Request": "1" },
    body: JSON.stringify(obj) }).then(function (r) { return r.json(); });
}
document.querySelectorAll(".copy").forEach(function (b) {
  b.addEventListener("click", function () {
    var t = b.parentNode.querySelector("pre").innerText;
    function done() { var o = b.textContent; b.textContent = "✓"; setTimeout(function () { b.textContent = o; }, 1200); }
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(t).then(done); return; }
    var ta = document.createElement("textarea"); ta.value = t; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(); } catch (e) {} ta.remove();
  });
});
document.querySelectorAll("input[data-check]").forEach(function (cb) {
  cb.addEventListener("change", function () {
    cb.disabled = true;
    wstgPost("/api/check", { key: cb.dataset.check, on: cb.checked }).then(function (res) {
      if (!res.ok) { alert("保存できませんでした:\n" + (res.error || "")); cb.checked = !cb.checked; }
      else { var by = cb.parentNode.querySelector(".by"); if (by) by.textContent = res.label || ""; }
      cb.disabled = false;
    }).catch(function () { alert("サーバに接続できません"); cb.checked = !cb.checked; cb.disabled = false; });
  });
});
document.querySelectorAll(".filters").forEach(function (f) {
  var table = document.getElementById(f.dataset.for);
  f.querySelectorAll("button").forEach(function (b) {
    b.addEventListener("click", function () {
      f.querySelectorAll("button").forEach(function (x) { x.classList.toggle("on", x === b); });
      var k = b.dataset.f;
      document.querySelectorAll("#" + f.dataset.for + " tr[data-f]").forEach(function (tr) {
        tr.classList.toggle("hide", k !== "all" && tr.dataset.f.split(" ").indexOf(k) < 0);
      });
    });
  });
});
"""

NAV = [("/", "ダッシュボード", "home"), ("/tasks", "タスク", "tasks"), ("/wstg/", "WSTG 索引", "wstg"),
       ("/findings/", "所見", "findings"), ("/export.csv", "CSV", "csv")]


def page(site: Site, title: str, body: str, active: str = "", script: str = "") -> str:
    nav = "".join(f'<a href="{h}" class="{"on" if k == active else ""}">{E(t)}</a>' for h, t, k in NAV)
    who = f'<span class="who">👤 {E(site.user)}</span>' if site.user else ""
    return (f'<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{E(title)}</title><style>{CSS}</style></head><body>'
            f'<nav class="nav">{nav}{who}</nav>{body}'
            f'<script>{COMMON_JS}{script}</script></body></html>')


def chip_verdict(v: str) -> str:
    return f'<span class="chip c-{E(v)}">{E(VERDICT_LABEL.get(v, v))}</span>'


def chip_sev(f: dict) -> str:
    sc = f" {f['base']}" if f.get("base") is not None else ""
    return f'<span class="sev s-{E(f["severity"])}">{E(f["severity_label"])}{sc}</span>'


def chip_status(f: dict) -> str:
    return f'<span class="st">{E(fnd.STATUSES.get(f["status"], f["status"]))}</span>'


def finding_link(f: dict) -> str:
    return f'{chip_sev(f)} <a href="/findings/{E(f["id"])}">{E(f["id"])} {E(f["title"])}</a>'


def cmdbox(cmd: str) -> str:
    return f'<div class="cmdbox"><pre>{E(cmd)}</pre><button class="copy" type="button">コピー</button></div>'


def record_href(folder: str, wid: str = "", step: str = "") -> str:
    frag = wid + (f"/s{step}" if step else "")
    return f"/{quote(folder)}/record.html" + (f"#{quote(frag, safe='/')}" if frag else "")


EV_RE = re.compile(r"(WSTG-[A-Z]+-\d+)(?:-s(\d+))?")


def evidence_link(rel: str) -> tuple:
    """evidence の相対パス → (record.html の深いリンク, ファイル自体のリンク)。"""
    parts = rel.split("/", 1)
    folder = parts[0]
    name = parts[1].rsplit("/", 1)[-1] if len(parts) > 1 else ""
    m = EV_RE.search(name)
    deep = record_href(folder, m.group(1), m.group(2) or "") if m else record_href(folder)
    raw = "/" + quote(rel) if len(parts) > 1 and parts[1] else ""
    return deep, raw


# --- 最小 Markdown（エスケープしてから整形する。生 HTML は通さない） ------------------

def _inline(text: str) -> str:
    codes: list = []

    def keep(m):
        codes.append(f"<code>{m.group(1)}</code>")
        return f"\x00{len(codes) - 1}\x00"

    t = E(text, quote=False)
    t = re.sub(r"`([^`]+)`", keep, t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)

    def lnk(m):
        label, url = m.group(1), m.group(2)
        if not re.match(r"^(https?://|/|#|[A-Za-z0-9_.-]+\.md$)", url):
            return m.group(0)
        if url.endswith(".md") and re.match(r"^WSTG-[A-Z]+-\d+\.md$", url):
            url = "/playbooks/" + url[:-3]
        return f'<a href="{E(url)}">{label}</a>'

    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", lnk, t)
    t = re.sub(r"(?<![\"'=>])(https?://[^\s<)（）、]+)", r'<a href="\1">\1</a>', t)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], t)


def md(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text or "", flags=re.S)
    out: list = []
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    para: list = []
    lst: list = []   # (tag, [items])

    def flush():
        nonlocal para, lst
        if para:
            out.append("<p>" + _inline(" ".join(para)) + "</p>")
            para = []
        if lst:
            tag = lst[0]
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x)}</li>" for x in lst[1]) + f"</{tag}>")
            lst = []

    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            flush()
            buf = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            out.append(f"<pre><code>{E(chr(10).join(buf))}</code></pre>")
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            flush()
            lv = min(len(m.group(1)) + 1, 5)
            out.append(f"<h{lv}>{_inline(m.group(2))}</h{lv}>")
            i += 1
            continue
        if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1]):
            flush()
            def cells(s):
                return [c.strip() for c in s.strip().strip("|").split("|")]
            head = cells(ln)
            i += 2
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            out.append('<div class="tbl"><table><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</table></div>")
            continue
        m = re.match(r"^\s*(?:[-*]|(\d+)\.)\s+(.*)$", ln)
        if m:
            tag = "ol" if m.group(1) else "ul"
            if para or (lst and lst[0] != tag):
                flush()
            if not lst:
                lst = [tag, []]
            lst[1].append(m.group(2))
            i += 1
            continue
        if not ln.strip():
            flush()
            i += 1
            continue
        if lst and ln.startswith((" ", "\t")):   # リスト項目の継続行
            lst[1][-1] += " " + ln.strip()
            i += 1
            continue
        if lst:
            flush()
        para.append(ln.strip())
        i += 1
    flush()
    return '<div class="md">' + "\n".join(out) + "</div>"


# --- ダッシュボード ---------------------------------------------------------

def next_activity(site: Site):
    for a in site.activities:
        if site.act_state(a["id"]) != "done" and all(
                site.act_state(d) == "done" for d in (a.get("depends_on") or [])):
            return a
    return None


def page_dashboard(site: Site) -> str:
    active = site.active_tests()
    done = site.wstg_done()
    cnt = {v: sum(1 for w in active if site.rows[w]["status"] == v) for v in VERDICTS}
    live = [f for f in site.findings if f["status"] in fnd.ACTIVE_STATUSES]
    drafts = sum(1 for f in site.findings if f["status"] == "draft")
    acts_done = sum(1 for a in site.activities if site.act_state(a["id"]) == "done")
    pct = int(100 * done / len(active)) if active else 0
    tiles = [
        (f"{done}<small>/{len(active)}</small>", "WSTG 判定済み", pct),
        (f"{cnt['fail']}", "FAIL の WSTG", None),
        (f"{len(live)}", "所見（下書き＋確定）", None),
        (f"{drafts}", "下書きの所見（要確定）", None),
        (f"{acts_done}<small>/{len(site.activities)}</small>", "アクティビティ完了",
         int(100 * acts_done / len(site.activities)) if site.activities else 0),
    ]
    tiles_html = "".join(
        f'<div class="tile"><div class="n">{n}</div><div class="l">{E(l)}</div>'
        + (f'<div class="bar"><i style="width:{p}%"></i></div>' if p is not None else "") + "</div>"
        for n, l, p in tiles)
    sev = {s: sum(1 for f in live if f["severity"] == s) for s in fnd.SEVERITY_ORDER}
    sev_html = " ".join(f'<span class="sev s-{s}">{fnd.SEVERITY_LABEL[s]} {sev[s]}</span>'
                        for s in fnd.SEVERITY_ORDER if sev[s]) or '<span class="empty">所見はまだありません</span>'
    chips = " ".join(f'<span class="chip c-{v}">{VERDICT_LABEL[v]} {cnt[v]}</span>' for v in VERDICTS if cnt[v])

    nxt = next_activity(site)
    if nxt:
        nxt_html = (f'<a class="card" href="/tasks#act-{E(nxt["id"])}"><div class="mono">'
                    f'{nxt["order"]}. {E(nxt["id"])}</div><b>{E(nxt.get("title", ""))}</b>'
                    f'<div class="mut">{E(nxt.get("summary", ""))}</div></a>')
    else:
        nxt_html = '<p>すべてのアクティビティが完了しています。<a href="/tasks#finish">仕上げ</a>へ。</p>'

    cards = []
    for d, data in sorted(site.runs, key=lambda x: x[0].name):
        covers = [c for c in (data.get("covers") or []) if isinstance(c, dict)]
        cc = {v: sum(1 for c in covers if str(c.get("verdict", "todo")).lower() == v) for v in VERDICTS}
        ch = "".join(f'<span class="chip c-{v}">{VERDICT_LABEL[v]} {cc[v]}</span>' for v in VERDICTS if cc[v])
        sub = " · ".join(x for x in [str(data.get("target_scope") or ""), str(data.get("date") or ""),
                                     str(data.get("tester") or "")] if x)
        cards.append(f'<a class="card" href="{record_href(d.name)}"><div class="mono">{E(d.name)}</div>'
                     f'<b>{E(str(data.get("title", "")))}</b><div class="mut">{E(sub)}</div>'
                     f'<div class="chips">{ch}</div></a>')
    body = (f'<h1>WSTG 実施状況</h1><div class="meta">WSTG v4.2 · 実施対象 {len(active)} 項目'
            f'（統合済み {len(site.tests) - len(active)} 項目は対象外）</div>'
            f'<div class="tiles">{tiles_html}</div>'
            f'<div class="chips">{chips}</div>'
            f'<h2>所見の深刻度（下書き＋確定）</h2><div class="chips">{sev_html}</div>'
            f'<h2>次にやること</h2>{nxt_html}'
            f'<h2>実施記録（{len(cards)}）</h2>'
            + ("".join(cards) or '<p class="empty">まだありません。<a href="/tasks">タスク</a>の順に始めてください。</p>'))
    return page(site, "WSTG 実施状況", body, "home")


# --- WSTG 索引・詳細 -------------------------------------------------------

def page_wstg_index(site: Site) -> str:
    by_cat: dict = {}
    for wid, t in site.tests.items():
        by_cat.setdefault(t["category"], []).append(wid)
    active = site.active_tests()
    done = site.wstg_done()
    sections = []
    for cat, wids in by_cat.items():
        act = [w for w in wids if w in active]
        cdone = sum(1 for w in act if site.rows[w]["status"] != "todo")
        trs = []
        for wid in wids:
            t = site.tests[wid]
            st = site.rows[wid]["status"]
            fl = site.f_by_wstg.get(wid, [])
            recs = " ".join(
                f'<a href="{record_href(folder, wid)}" title="{E(folder)}">{chip_verdict(v)}</a>'
                for folder, _, v, _, _ in site.wstg_runs.get(wid, []))
            fl_html = "<br>".join(finding_link(f) for f in sorted(fl, key=fnd.sort_key))
            tags = [st] + (["has-f"] if fl else []) + (["open"] if st == "todo" and not t.get("deprecated") else [])
            title = E(t["title"]) + (' <span class="mut">（統合済み）</span>' if t.get("deprecated") else "")
            trs.append(f'<tr data-f="{" ".join(tags)}"><td class="mono"><a href="/wstg/{wid}">{wid}</a></td>'
                       f"<td>{title}</td><td>{chip_verdict(st)}</td><td>{recs}</td><td>{fl_html}</td></tr>")
        pct = int(100 * cdone / len(act)) if act else 100
        sections.append(
            f'<h2>{E(cat)} <span class="mut">{cdone}/{len(act)}</span></h2>'
            f'<div class="bar"><i style="width:{pct}%"></i></div>'
            f'<div class="tbl"><table><tr><th>ID</th><th>テスト</th><th>集約</th><th>実施記録（クリックで該当タブ）</th>'
            f"<th>所見</th></tr>{''.join(trs)}</table></div>")
    filters = ('<div class="filters" data-for="wstg-all">'
               '<button data-f="all" class="on">すべて</button><button data-f="open">未実施</button>'
               '<button data-f="fail">FAIL</button><button data-f="has-f">所見あり</button>'
               '<button data-f="pass">PASS</button></div>')
    body = (f'<h1>WSTG 索引</h1><div class="meta">判定済み {done}/{len(active)} · 集約は '
            f'fail &gt; 未実施 &gt; info &gt; pass &gt; n/a の優先度（複数アクティビティで最も注意すべきもの）</div>'
            f'{filters}<div id="wstg-all">{"".join(sections)}</div>')
    # フィルタは表をまたいで効かせる（id 付きの外側 div 配下の tr を対象にする）
    return page(site, "WSTG 索引", body, "wstg")


def page_wstg_detail(site: Site, wid: str):
    t = site.tests.get(wid)
    if not t:
        return None
    row = site.rows[wid]
    crit = site.criteria.get(wid, {}) or {}
    parts = [f'<div class="meta"><a href="/wstg/">WSTG 索引</a> › {E(t["category"])}</div>',
             f'<h1><span class="mono">{wid}</span> {E(t["title"])}</h1>',
             f'<div class="chips">{chip_verdict(row["status"])}'
             + (f' <span class="mut">v4.2 で「{E(str(t.get("merged_into", "")))}」に統合（単独では実施しない）</span>'
                if t.get("deprecated") else "") + "</div>"]
    if crit:
        parts.append("<h2>判定基準</h2>")
        for k, label in (("purpose", "目的"), ("pass", "pass"), ("fail", "fail")):
            if crit.get(k):
                parts.append(f"<p><b>{label}</b>: {_inline(str(crit[k]))}</p>")

    parts.append("<h2>実施記録</h2>")
    runs = site.wstg_runs.get(wid, [])
    if runs:
        trs = "".join(
            f'<tr><td class="mono"><a href="{record_href(folder, wid)}">{E(folder)}</a></td><td>{chip_verdict(v)}</td>'
            f"<td>{E(role)}</td><td>{E(fnd_line)}</td></tr>"
            for folder, _, v, fnd_line, role in runs)
        parts.append(f'<div class="tbl"><table><tr><th>アクティビティ</th><th>判定</th><th>役割</th>'
                     f"<th>判定理由</th></tr>{trs}</table></div>")
    planned = [(a, c) for a in site.activities for c in a.get("covers", []) if c["id"] == wid]
    ran = {aid for _, aid, _, _, _ in runs}
    todo_acts = [(a, c) for a, c in planned if a["id"] not in ran]
    if todo_acts:
        parts.append('<p class="mut">未着手のアクティビティ: ' + ", ".join(
            f'<a href="/tasks#act-{E(a["id"])}">{E(a["id"])}</a>（{E(c.get("role", "primary"))}）'
            for a, c in todo_acts) + "</p>")
    if not runs and not todo_acts:
        parts.append('<p class="empty">この項目をカバーするアクティビティはありません。</p>')

    fl = sorted(site.f_by_wstg.get(wid, []), key=fnd.sort_key)
    new_q = urlencode({"wid": wid})
    parts.append(f'<h2>所見（{len(fl)}）</h2>')
    if fl:
        parts.append("<ul>" + "".join(f"<li>{finding_link(f)} {chip_status(f)}</li>" for f in fl) + "</ul>")
    confirmed = [f for f in fl if f["status"] == "confirmed"]
    if confirmed and not any(v == "fail" for _, _, v, _, _ in runs):
        parts.append('<p class="warn">⚠ 確定した所見があるのに、どのアクティビティでも fail になっていません。'
                     "判定を見直してください。</p>")
    parts.append(f'<p><a class="btn" href="/findings/new?{new_q}">＋ この WSTG の所見を作成</a></p>')

    pb = PLAYBOOKS / f"{wid}.md"
    if pb.exists():
        parts.append(f'<details><summary>カード（playbooks/{wid}.md）を開く</summary>'
                     f'{md(pb.read_text(encoding="utf-8"))}</details>')
    return page(site, f"{wid} — {t['title']}", "".join(parts), "wstg")


def page_playbook(site: Site, wid: str):
    pb = PLAYBOOKS / f"{wid}.md"
    if not re.match(r"^WSTG-[A-Z]+-\d+$", wid) or not pb.exists():
        return None
    body = (f'<div class="meta"><a href="/wstg/{wid}">{wid} の実施状況へ</a></div>'
            + md(pb.read_text(encoding="utf-8")))
    return page(site, f"カード {wid}", body, "wstg")


# --- 所見 ------------------------------------------------------------------

def page_findings(site: Site, status: str = "", wid: str = "") -> str:
    fs = site.findings
    if status:
        fs = [f for f in fs if f["status"] == status]
    if wid:
        fs = [f for f in fs if wid in f["wstg"]]
    fs = sorted(fs, key=fnd.sort_key)
    stat_links = " ".join(
        f'<a class="chip" href="/findings/?{urlencode({"status": k})}"'
        f'{" style=font-weight:900" if k == status else ""}>{E(v)} '
        f'{sum(1 for f in site.findings if f["status"] == k)}</a>'
        for k, v in fnd.STATUSES.items())
    trs = "".join(
        f'<tr><td class="mono"><a href="/findings/{E(f["id"])}">{E(f["id"])}</a></td><td>{chip_sev(f)}</td>'
        f'<td><a href="/findings/{E(f["id"])}">{E(f["title"])}</a></td><td>{chip_status(f)}</td>'
        f'<td class="mono">{"<br>".join(f"<a href=/wstg/{E(w)}>{E(w)}</a>" for w in f["wstg"])}</td>'
        f'<td>{len(f["evidence"])}</td><td class="mut">{E(f["updated"][:10])} {E(f["updated_by"])}</td></tr>'
        for f in fs)
    body = (f'<h1>所見</h1><div class="meta">深刻度は CVSS v3.1 のベクトルから自動計算（Critical ≥9.0 / High ≥7.0 / '
            f'Medium ≥4.0 / Low ≥0.1 / 情報 0.0）。未評価はベクトル未入力。</div>'
            f'<div class="chips"><a class="chip" href="/findings/">すべて {len(site.findings)}</a> {stat_links}'
            + (f' <span class="mut">WSTG 絞り込み: {E(wid)}</span>' if wid else "") + "</div>"
            f'<p><a class="btn" href="/findings/new">＋ 所見を作成</a></p>'
            + (f'<div class="tbl"><table><tr><th>ID</th><th>深刻度</th><th>タイトル</th><th>状態</th><th>WSTG</th>'
               f"<th>証跡</th><th>更新</th></tr>{trs}</table></div>" if fs
               else '<p class="empty">該当する所見はありません。record.html の『＋ 所見を作成』'
                    "『📎 所見に添付』からも作れます。</p>"))
    return page(site, "所見", body, "findings")


def _meter(label: str, val: float, mx: float) -> str:
    pct = int(100 * min(val, mx) / mx) if mx else 0
    return (f'<div class="meter"><div class="mut">{E(label)} <b>{val}</b> / {mx}</div>'
            f'<div class="bar"><i style="width:{pct}%"></i></div></div>')


def _evidence_block(rel: str, preview: bool = True) -> str:
    deep, raw = evidence_link(rel)
    links = f'<a href="{deep}">実施記録で見る</a>' + (f' · <a href="{raw}">ファイル</a>' if raw else "")
    pv = ""
    if preview and raw:
        low = rel.lower()
        if low.endswith((".png", ".jpg", ".jpeg", ".gif")):
            pv = f'<img src="{raw}" loading="lazy" alt="{E(rel)}">'
        elif low.endswith((".txt", ".md", ".json", ".xml", ".csv", ".log")):
            pv = f'<iframe src="{raw}" loading="lazy"></iframe>'
    return f'<div class="ev card"><div class="mono">{E(rel)}</div><div>{links}</div>{pv}</div>'


def page_finding(site: Site, fid: str):
    f = next((x for x in site.findings if x["id"] == fid), None)
    if not f:
        return None
    sc = f["score"]
    parts = [f'<div class="meta"><a href="/findings/">所見</a> › {E(fid)}</div>',
             f'<h1>{E(fid)} {E(f["title"])}</h1>',
             f'<div class="chips">{chip_sev(f)} {chip_status(f)} <span class="mut">作成 {E(f["author"])} '
             f'{E(f["created"])} · 更新 {E(f["updated_by"])} {E(f["updated"])}</span></div>',
             f'<p><a class="btn" href="/findings/{E(fid)}/edit">✎ 編集</a></p>']
    parts.append("<h2>深刻度の根拠（CVSS v3.1）</h2>")
    if sc:
        parts.append(f'<div class="score"><div><div class="big">{sc["base"]}</div>{chip_sev(f)}</div>'
                     + _meter("起こりやすさ（悪用のしやすさ）", sc["exploitability"], cvss31.EXPL_MAX)
                     + _meter("影響", sc["impact"], cvss31.IMPACT_MAX)
                     + f'<div class="mono">{E(sc["vector"])}</div></div>')
        trs = []
        for m in cvss31.METRICS:
            val = sc["metrics"][m["key"]]
            opt = next(o for o in m["options"] if o[0] == val)
            note = f.get("cvss_notes", {}).get(m["key"], "")
            trs.append(f'<tr><td>{E(m["group"])}</td><td>{E(m["name"])}（{m["key"]}）</td>'
                       f'<td><b>{E(opt[1])}</b><br><span class="mut">{E(opt[2])}</span></td>'
                       f'<td>{E(note) if note else "<span class=mut>—</span>"}</td></tr>')
        parts.append('<div class="tbl"><table><tr><th>区分</th><th>指標</th><th>選択</th><th>判断理由</th></tr>'
                     + "".join(trs) + "</table></div>")
    else:
        parts.append('<p class="warn">未評価です。『編集』で CVSS の設問に答えてください'
                     "（深刻度は設問の答えから自動で決まります）。</p>")
    parts.append("<h2>関係する WSTG</h2><ul>" + "".join(
        f'<li><a href="/wstg/{E(w)}" class="mono">{E(w)}</a> {E(site.tests.get(w, {}).get("title", ""))}</li>'
        for w in f["wstg"]) + "</ul>")
    parts.append(f'<h2>エビデンス（{len(f["evidence"])}）</h2>')
    parts.append("".join(_evidence_block(e) for e in f["evidence"])
                 or '<p class="empty">未添付。record.html の各出力・スクショの『📎 所見に添付』で追加できます。</p>')
    parts.append("<h2>本文</h2>" + md(f["body"]))
    return page(site, f"{fid} {f['title']}", "".join(parts), "findings")


def page_attach(site: Site, wid: str, ev: str) -> str:
    try:
        ev_n = fnd.normalize_evidence(site.root, ev) if ev else ""
        err = ""
    except fnd.FindingError as exc:
        ev_n, err = "", str(exc)
    if err:
        return page(site, "所見に添付", f'<h1>所見に添付</h1><p class="bad">{E(err)}</p>', "findings")
    new_q = urlencode({"wid": wid, "ev": ev_n})
    same = [f for f in site.findings if wid in f["wstg"]]
    other = [f for f in site.findings if wid not in f["wstg"]]

    def rows(fs):
        return "".join(
            f'<tr><td>{finding_link(f)} {chip_status(f)}</td>'
            f'<td><button class="btn sub" data-attach="{E(f["id"])}">これに追加</button></td></tr>'
            for f in sorted(fs, key=fnd.sort_key))

    body = (f'<h1>エビデンスを所見に添付</h1>'
            f'<div class="meta">WSTG: <span class="mono">{E(wid) or "—"}</span></div>'
            + _evidence_block(ev_n) +
            f'<p><a class="btn" href="/findings/new?{new_q}">＋ 新しい所見を作る</a></p>'
            f'<h2>既存の所見に追加（同じ WSTG）</h2>'
            + (f'<div class="tbl"><table>{rows(same)}</table></div>' if same else '<p class="empty">なし</p>')
            + (f'<details><summary>ほかの所見（{len(other)}）</summary><div class="tbl"><table>{rows(other)}'
               f"</table></div></details>" if other else ""))
    script = ("document.querySelectorAll('[data-attach]').forEach(function(b){b.addEventListener('click',function(){"
              "b.disabled=true;wstgPost('/api/finding/attach',{id:b.dataset.attach,ev:" + json.dumps(ev_n)
              + ",wid:" + json.dumps(wid) + "}).then(function(r){if(r.ok){location.href='/findings/'+b.dataset.attach;}"
              "else{alert('追加できませんでした:\\n'+(r.error||''));b.disabled=false;}});});});")
    return page(site, "所見に添付", body, "findings", script)


FORM_JS = r"""
(function () {
  var form = document.getElementById("ff");
  var keys = JSON.parse(form.dataset.keys);
  function vector() {
    var parts = [];
    for (var i = 0; i < keys.length; i++) {
      var c = form.querySelector('input[name="m-' + keys[i] + '"]:checked');
      if (!c) return "";
      parts.push(keys[i] + ":" + c.value);
    }
    return "CVSS:3.1/" + parts.join("/");
  }
  function setVector(v) {
    (v || "").replace(/^CVSS:3\.1\//, "").split("/").forEach(function (p) {
      var kv = p.split(":"); var r = form.querySelector('input[name="m-' + kv[0] + '"][value="' + kv[1] + '"]');
      if (r) r.checked = true;
    });
    update();
  }
  var out = document.getElementById("score");
  function update() {
    var v = vector();
    var missing = keys.filter(function (k) { return !form.querySelector('input[name="m-' + k + '"]:checked'); });
    if (!v) { out.innerHTML = '<span class="warn">未評価 — あと ' + missing.length + ' 問（' + missing.join(", ")
      + '）。深刻度は答えから自動で決まります</span>'; return; }
    fetch("/api/cvss?vector=" + encodeURIComponent(v)).then(function (r) { return r.json(); }).then(function (r) {
      if (!r.ok) { out.textContent = r.error; return; }
      var s = r.score;
      function meter(label, val, mx) { return '<div class="meter"><div class="mut">' + label + ' <b>' + val + '</b> / '
        + mx + '</div><div class="bar"><i style="width:' + Math.round(100 * Math.min(val, mx) / mx) + '%"></i></div></div>'; }
      out.innerHTML = '<div><div class="big">' + s.base + '</div><span class="sev s-' + s.severity + '">'
        + s.severity_label + '</span></div>' + meter("起こりやすさ（悪用のしやすさ）", s.exploitability, r.expl_max)
        + meter("影響", s.impact, r.impact_max) + '<div class="mono">' + s.vector + '</div>';
    });
  }
  form.addEventListener("change", function (ev) { if (ev.target.name && ev.target.name.indexOf("m-") === 0) update(); });
  document.querySelectorAll("[data-example]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (vector() && !confirm("今の選択を例で置き換えますか？（あとで事実に合わせて選び直してください）")) return;
      setVector(b.dataset.example);
    });
  });
  document.getElementById("paste-vec").addEventListener("change", function (ev) { setVector(ev.target.value.trim()); });
  document.getElementById("clear-vec").addEventListener("click", function () {
    form.querySelectorAll('input[type=radio]').forEach(function (r) { r.checked = false; }); update(); });
  update();
  function lines(name) { return form.elements[name].value.split("\n").map(function (s) { return s.trim(); })
    .filter(Boolean); }
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var notes = {};
    keys.forEach(function (k) { var n = form.elements["n-" + k]; if (n && n.value.trim()) notes[k] = n.value.trim(); });
    var btn = form.querySelector("button[type=submit]"); btn.disabled = true;
    wstgPost("/api/finding/save", {
      id: form.dataset.id || null, rev: form.dataset.rev || null,
      title: form.elements.title.value, status: form.elements.status.value,
      cvss: vector(), cvss_notes: notes, wstg: lines("wstg"), evidence: lines("evidence"),
      body: form.elements.body.value
    }).then(function (r) {
      if (r.ok) { location.href = "/findings/" + r.id; return; }
      alert("保存できませんでした:\n" + (r.error || "")); btn.disabled = false;
    }).catch(function () { alert("サーバに接続できません"); btn.disabled = false; });
  });
})();
"""


def page_finding_form(site: Site, fid: str = "", wid: str = "", ev: str = ""):
    if fid:
        f = next((x for x in site.findings if x["id"] == fid), None)
        if not f:
            return None
    else:
        f = {"id": "", "rev": "", "title": "", "status": "draft", "cvss": "", "cvss_notes": {},
             "wstg": [wid] if wid else [], "evidence": [ev] if ev else [], "body": fnd.BODY_TEMPLATE}
    cur = cvss31.try_score(f["cvss"])
    chosen = cur["metrics"] if cur else {}
    status_opts = "".join(f'<option value="{k}"{" selected" if k == f["status"] else ""}>{E(v)}</option>'
                          for k, v in fnd.STATUSES.items())
    wstg_list = "".join(f'<option value="{w}">{E(t["title"])}</option>' for w, t in site.tests.items())
    groups = []
    for g in ("起こりやすさ", "影響"):
        fs = []
        for m in cvss31.METRICS:
            if m["group"] != g:
                continue
            opts = "".join(
                f'<label class="opt"><input type="radio" name="m-{m["key"]}" value="{v}"'
                f'{" checked" if chosen.get(m["key"]) == v else ""}><span><b>{E(lab)}</b> '
                f"<small>{E(desc)}</small></span></label>"
                for v, lab, desc in m["options"])
            note = E(f["cvss_notes"].get(m["key"], ""))
            fs.append(f'<fieldset><legend>{E(m["name"])}（{m["key"]}）— {E(m["q"])}</legend>{opts}'
                      f'<input type="text" name="n-{m["key"]}" value="{note}" '
                      f'placeholder="判断理由（例: 未ログインで再現。任意だがレビューで効く）"></fieldset>')
        groups.append(f"<h3>{g}</h3>" + "".join(fs))
    examples = "".join(
        f'<button type="button" class="btn sub" data-example="{E(v)}">{E(lab)}（{cvss31.score(v)["base"]}）</button> '
        for lab, v in CVSS_EXAMPLES)
    title = f"{fid} を編集" if fid else "所見を作成"
    body = (f'<div class="meta"><a href="/findings/">所見</a> › {E(title)}</div><h1>{E(title)}</h1>'
            f'<form id="ff" data-id="{E(f["id"])}" data-rev="{E(f["rev"])}" '
            f'data-keys="{E(json.dumps(cvss31.KEYS))}">'
            f'<div class="field"><label class="l">タイトル（1行の見出し。CSV にも載る。生値は書かない）</label>'
            f'<input type="text" name="title" value="{E(f["title"])}" required></div>'
            f'<div class="field"><label class="l">状態</label><select name="status">{status_opts}</select>'
            f' <span class="mut">下書き＝要レビュー / 確定＝報告対象 / 取り下げ＝誤検知 / 解消＝再テストで直った</span></div>'
            f'<div class="field"><label class="l">関係する WSTG-ID（1行に1つ。1つの所見に複数可）</label>'
            f'<textarea name="wstg" rows="2" class="code" list="wl">{E(chr(10).join(f["wstg"]))}</textarea>'
            f'<datalist id="wl">{wstg_list}</datalist></div>'
            f'<div class="field"><label class="l">エビデンス（evidence からの相対パス。1行に1つ。'
            f'record.html の『📎 所見に添付』でも足せる）</label>'
            f'<textarea name="evidence" rows="3" class="code">{E(chr(10).join(f["evidence"]))}</textarea></div>'
            f'<h2>深刻度（CVSS v3.1 の設問に答える）</h2>'
            f'<div class="hint">深刻度（Critical/High/Medium/Low/情報）は選びません。下の 8 問に答えると CVSS v3.1 で'
            f'自動計算されます。上の4問が<b>起こりやすさ</b>（悪用のしやすさ）、下の4問が<b>影響</b>です。'
            f'「最悪ならこうなるかも」ではなく<b>検査で確認できた事実</b>で選び、迷ったら判断理由に書いて'
            f'レビューで相談してください。</div>'
            f'<div class="score" id="score"></div>'
            f'<details><summary>参考例から始める / ベクトルを貼る</summary><p class="mut">例は出発点です。'
            f'当てはめたら、事実に合わない設問を選び直してください。</p><p>{examples}</p>'
            f'<input type="text" id="paste-vec" placeholder="CVSS:3.1/AV:N/AC:L/... を貼ると設問に反映">'
            f' <button type="button" class="btn sub" id="clear-vec">選択をクリア</button></details>'
            + "".join(groups) +
            f'<h2>本文</h2><div class="field"><textarea name="body" rows="18" class="code">{E(f["body"])}</textarea></div>'
            f'<p><button type="submit" class="btn">保存</button> '
            f'<a class="btn sub" href="{"/findings/" + E(fid) if fid else "/findings/"}">キャンセル</a></p></form>')
    return page(site, title, body, "findings", FORM_JS)


# --- タスク（指示書＋チェックリスト） ------------------------------------------

def _check_label(site: Site, key: str) -> str:
    c = site.checks.get(key)
    if not isinstance(c, dict):
        return ""
    return f'{c.get("by", "")} {str(c.get("at", ""))[:16].replace("T", " ")}'


def manual_check(site: Site, key: str, text: str) -> str:
    on = isinstance(site.checks.get(key), dict)
    return (f'<li><input type="checkbox" data-check="{E(key)}"{" checked" if on else ""}>'
            f'<span>{text} <span class="by">{E(_check_label(site, key))}</span></span></li>')


def auto_check(ok: bool, text: str, warn: bool = False) -> str:
    mark = '<span class="ck ok">✓</span>' if ok else f'<span class="ck {"ng" if warn else ""}">・</span>'
    return f"<li>{mark}<span>{text}</span></li>"


def _manual_filled(path: Path) -> bool:
    """手動手順のひな型（# 行だけ）から書き足されているか。"""
    try:
        return any(ln.strip() and not ln.startswith("#") for ln in path.read_text(encoding="utf-8").split("\n"))
    except OSError:
        return False


def folder_status(site: Site, folder: Path) -> dict:
    """1つの実施フォルダの自動チェック（コマンド・手動・判定・所見）。"""
    from new_activity import build_evidence, resolve_activity
    out = {"cmd": [0, 0], "manual": [0, 0], "verdict": [0, 0], "drafts": 0, "unrated": 0, "error": ""}
    try:
        activity, tests, criteria, target, act_dir = resolve_activity(folder)
        data = build_evidence(activity, tests, criteria, target, folder, act_dir)
    except SystemExit as exc:
        out["error"] = str(exc)
        return out
    for it in data["items"]:
        out["verdict"][1] += 1
        out["verdict"][0] += it["verdict"] != "todo"
        for st in it["steps"]:
            for r in st["runs"]:
                if r["role"] == "manual":
                    out["manual"][1] += 1
                    out["manual"][0] += _manual_filled(folder / r["output_path"])
                elif r["role"] != "check":
                    out["cmd"][1] += 1
                    out["cmd"][0] += bool(r["has_output"])
    wids = {it["wid"] for it in data["items"]}
    rel = folder.name + "/"
    for f in site.findings:
        mine = any(e.startswith(rel) for e in f["evidence"]) or bool(wids & set(f["wstg"]))
        if mine and f["status"] in fnd.ACTIVE_STATUSES:
            out["drafts"] += f["status"] == "draft"
            out["unrated"] += f["severity"] == "unrated"
    return out


def _frac(pair) -> str:
    return f"{pair[0]}/{pair[1]}"


def page_tasks(site: Site) -> str:
    by_phase: dict = {}
    for a in site.activities:
        by_phase.setdefault(a["phase"], []).append(a)
    phases = site.coverage.get("phases", {})
    S = {"todo": ("未着手", "c-todo"), "doing": ("実施中", "c-doing"), "done": ("完了", "c-done")}
    out = ['<h1>実施タスク</h1><div class="meta">上から順に進める。<span class="ck ok">✓</span> は実施状況から'
           '自動でチェックされる（run.yaml・cmd/・所見を見ている）。☐ は人が押す（誰がいつ押したかが残る）。'
           'コマンドは Kali の端末でリポジトリ直下から実行する。</div>']
    out.append('<h2 id="phase0">フェーズ0 — 準備（1回だけ）</h2><ul class="check">')
    out.append(manual_check(site, "p0:agree", "対象・時間帯・禁止事項・連絡先を合意した（影響度「高」の項目は特に）"))
    out.append(manual_check(site, "p0:accounts", "ロールごとのテストアカウントを入手した"))
    out.append(manual_check(site, "p0:env", "Python 環境を用意し、ツールの自己診断が通った"))
    out.append("</ul>" + cmdbox("uv sync\n./scripts/selftest.sh"))
    out.append('<ul class="check">' + manual_check(
        site, "p0:proxy", "（プロキシ配下なら）外向き疎通を確認した。通らなければ README「プロキシ配下での準備」")
        + "</ul>" + cmdbox("env | grep -i proxy\ncurl -sI https://crt.sh | head -1"))
    out.append('<p class="mut">Kali のツールは各フェーズ冒頭の「準備」にまとめてある（まず <code>sudo apt update</code>）。'
               '複数サイトを回すときは各アクティビティで <code>--target &lt;site&gt;</code> を付ける。</p>')

    for ph, acts in by_phase.items():
        info = phases.get(ph, {})
        pdone = sum(1 for a in acts if site.act_state(a["id"]) == "done")
        out.append(f'<h2 id="phase{ph}">フェーズ{ph} — {E(info.get("name", ""))} '
                   f'<span class="mut">{pdone}/{len(acts)}</span></h2>')
        if info.get("goal"):
            out.append(f'<p>{E(info["goal"])}</p>')
        setup = render_phase_setup(acts, site.criteria)
        if setup:
            out.append(f'<details><summary>準備（このフェーズで使う Kali ツール）</summary>{md(chr(10).join(setup))}'
                       "</details>")
        for a in acts:
            out.append(_task_card(site, a, S))

    live = [f for f in site.findings if f["status"] in fnd.ACTIVE_STATUSES]
    active = site.active_tests()
    out.append('<h2 id="finish">仕上げ</h2><ul class="check">')
    out.append(auto_check(site.wstg_done() == len(active),
                          f'全 WSTG を判定した（{site.wstg_done()}/{len(active)}。<a href="/wstg/">WSTG 索引</a>の「未実施」で残りを確認）'))
    out.append(auto_check(not any(f["status"] == "draft" for f in site.findings),
                          f'下書きの所見がない（{sum(1 for f in site.findings if f["status"] == "draft")} 件。'
                          '<a href="/findings/?status=draft">下書き一覧</a>）'))
    out.append(auto_check(not any(f["severity"] == "unrated" for f in live),
                          f'所見がすべて CVSS 評価済み（未評価 {sum(1 for f in live if f["severity"] == "unrated")} 件）'))
    out.append(manual_check(site, "fin:review", "fail の項目と確定所見をリーダーがレビューした"))
    out.append(manual_check(site, "fin:report", '報告書を作成した（一覧は <a href="/export.csv">CSV</a> で取り出せる）'))
    out.append("</ul>")
    return page(site, "実施タスク", "".join(out), "tasks")


def _task_card(site: Site, a: dict, S: dict) -> str:
    aid = a["id"]
    state = site.act_state(aid)
    label, cls = S[state]
    deps = a.get("depends_on") or []
    dep_html = ", ".join(
        f'<a href="#act-{E(d)}">{E(d)}</a>{"" if site.act_state(d) == "done" else "<span class=warn>（未完）</span>"}'
        for d in deps) or "なし"
    cards = " ".join(f'<a class="mono" href="/wstg/{c["id"]}">{c["id"]}</a>'
                     + ("" if c.get("role", "primary") == "primary" else '<span class="mut">(補)</span>')
                     for c in a.get("covers", []))
    h = [f'<div class="card" id="act-{E(aid)}">',
         f'<h3>{a["order"]}. <span class="mono">{E(aid)}</span> — {E(a.get("title", ""))} '
         f'<span class="chip {cls}">{label}</span></h3>',
         f'<div>{E(a.get("summary", ""))}</div>',
         f'<div class="mut">影響度: {E(IMPACT_LABEL.get(a.get("impact", "low"), a.get("impact", "low")))} · '
         f'前提: {dep_html} · ツール: {E(", ".join(a.get("tools", [])))}</div>',
         f'<div class="mut">WSTG: {cards}</div>']
    runs = site.act_runs.get(aid) or []
    if not runs:
        h.append('<ul class="check">' + auto_check(False, "フォルダ一式を作る（複数サイトは <code>--target &lt;site&gt;</code>）")
                 + "</ul>" + cmdbox(f"uv run scripts/new_activity.py {aid}"))
        h.append('<p class="mut">作ると、この下に実行コマンドと自動チェックが出る。</p>')
    for d, data in runs:
        st = folder_status(site, d)
        rel = f"evidence/{d.name}"
        h.append(f'<div class="card"><div><a class="mono" href="{record_href(d.name)}">📂 {E(d.name)}</a> '
                 f'<span class="mut">{E(str(data.get("target_scope") or ""))} {E(str(data.get("date") or ""))}'
                 f' {E(str(data.get("tester") or ""))}</span></div>')
        if st["error"]:
            h.append(f'<p class="bad">{E(st["error"])}</p></div>')
            continue
        c, m, v = st["cmd"], st["manual"], st["verdict"]
        h.append('<ul class="check">')
        h.append(auto_check(True, "フォルダ一式を作った"))
        if c[1]:
            h.append(auto_check(c[0] == c[1], f"コマンド手順を実行した（出力あり {_frac(c)}）", c[0] < c[1]))
        if m[1]:
            h.append(auto_check(m[0] == m[1], f'手動手順の観察を書いた（{_frac(m)}。record.html の『✎ 結果を貼る/編集』'
                                              "か artifacts/manual-*.txt）", m[0] < m[1]))
        h.append(auto_check(v[0] == v[1], f'WSTG ごとの判定を記入した（{_frac(v)}。<a href="{record_href(d.name)}">'
                                          "record.html</a> の各タブで verdict と判定理由）", v[0] < v[1]))
        h.append(auto_check(st["drafts"] == 0 and st["unrated"] == 0,
                            f'関係する所見が確定・CVSS 評価済み（下書き {st["drafts"]} / 未評価 {st["unrated"]}）',
                            bool(st["drafts"] or st["unrated"])))
        h.append(manual_check(site, f"act:{d.name}:review", "リーダーが記録と判定を確認した"))
        h.append("</ul>")
        if c[1]:
            h.append(cmdbox(f"uv run scripts/run_activity.py {rel}"))
            h.append(f'<details><summary>単発で実行する / CLI でスクショ</summary>'
                     + cmdbox(f"uv run scripts/run_cmd.py {rel} -- <コマンド>")
                     + cmdbox(f"uv run scripts/save_shot.py {rel} --wid <WSTG-ID> --step <n> --grab --delay 3")
                     + "</details>")
        h.append("</div>")
    if runs:
        h.append(f'<details><summary>別の対象・日付でもう1回実施する</summary>'
                 + cmdbox(f"uv run scripts/new_activity.py {aid} --target <site>") + "</details>")
    h.append("</div>")
    return "".join(h)


# --- 単体確認用 -------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="evidence ルート（確認用。一時ディレクトリを推奨）")
    ap.add_argument("--out-dir", required=True, help="HTML を書き出す先")
    args = ap.parse_args()
    site = Site(Path(args.root))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    pages = {"index.html": page_dashboard(site), "tasks.html": page_tasks(site),
             "wstg.html": page_wstg_index(site), "findings.html": page_findings(site)}
    for name, text in pages.items():
        (out / name).write_text(text, encoding="utf-8")
    print(f"{len(pages)} ページを {out} に書き出しました（リンクはサーバ前提なので、確認は serve_record.py で）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
