#!/usr/bin/env python3
"""所見（Finding）ファイルの読み書き・一覧・findings.md からの移行。

    uv run scripts/findings.py list                 # 所見の一覧（ID・深刻度・状態・WSTG）
    uv run scripts/findings.py new --title "…" --wstg WSTG-ATHZ-01 [--evidence <フォルダ>/cmd/x.txt]
    uv run scripts/findings.py migrate              # 旧 findings.md（WSTG ごとの本文）を F ファイルへ移す

所見は 1件 = 1ファイル（evidence/_findings/F-001.md）。WSTG-ID とは多対多で、1つの WSTG に
複数の所見を、1つの所見に複数の WSTG・複数アクティビティのエビデンスを紐づけられる。
ファイルは YAML の front matter（メタデータ）＋ Markdown 本文:

    ---
    id: F-003
    title: "管理画面が未認証で到達可能"
    status: draft                 # draft | confirmed | rejected | fixed
    cvss: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N"
    cvss_notes:                   # 指標ごとの判断理由（任意。レビューで効く）
      AV: "インターネットから到達"
    wstg:
      - WSTG-ATHZ-01
    evidence:                     # evidence ルートからの相対パス（Web でエビデンスへリンク）
      - fingerprint-stack-20260920/cmd/WSTG-CONF-05-s2-c1.txt
    author: "alice"
    created: "2026-09-21"
    updated: "2026-09-21T10:00:00+09:00"
    updated_by: "alice"
    ---
    ## 概要 …

深刻度は保存しない。cvss ベクトルから毎回計算する（scripts/cvss31.py。人が選ぶと根拠が残らないため）。
Web（serve_record.py）で保存すると front matter はこのモジュールが書き直す（front matter 内の
コメントは残らないので、補足は本文に書く）。本文は保存した内容のまま。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS.parent
DEFAULT_ROOT = REPO_ROOT / "evidence"
WSTG_TESTS = REPO_ROOT / "matrix" / "wstg_tests.yaml"

sys.path.insert(0, str(SCRIPTS))
import cvss31  # noqa: E402

FINDINGS_DIRNAME = "_findings"
ID_RE = re.compile(r"^F-\d{3,}$")
WID_RE = re.compile(r"^WSTG-[A-Z]+-\d+$")
STATUSES = {
    "draft": "下書き",
    "confirmed": "確定",
    "rejected": "取り下げ",
    "fixed": "解消（再テスト）",
}
# 報告対象として数える状態（ダッシュボード・CSV の集計）
ACTIVE_STATUSES = ("draft", "confirmed")
SEVERITY_ORDER = ["critical", "high", "medium", "low", "none", "unrated"]
SEVERITY_LABEL = {"critical": "Critical", "high": "High", "medium": "Medium",
                  "low": "Low", "none": "情報", "unrated": "未評価"}

BODY_TEMPLATE = """## 概要

（何が起きるかを1〜3文で。生の資格情報・トークンは書かず、エビデンスを参照）

## 再現手順

1.

## 影響

（誰が・何をできてしまうか。CVSS の各指標の選択理由と矛盾しないように）

## 対策案

-
"""

# 旧 findings.md のプレースホルダ（移行時に「未記入」とみなす）
OLD_FINDINGS_PLACEHOLDER = "（ここに詳細な所見を書く。無ければ空のままでよい。生値は書かず evidence を参照）"


class FindingError(ValueError):
    """入力の検証エラー（利用者に見せる文言）。"""


class Conflict(Exception):
    """他の人が先に更新した（楽観ロックの不一致）。"""


# --- ファイル形式 ---------------------------------------------------------

def findings_dir(root: Path) -> Path:
    return Path(root) / FINDINGS_DIRNAME


def parse_text(text: str) -> tuple:
    """(meta, body) に分解する。front matter が無ければ meta は空。"""
    text = text.replace("\r\n", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            meta = yaml.safe_load(text[4:end]) or {}
            return (meta if isinstance(meta, dict) else {}), text[end + 5:].lstrip("\n")
    return {}, text


def _q(val) -> str:
    """YAML のダブルクォート文字列（JSON 文字列は YAML として有効）。"""
    return json.dumps("" if val is None else str(val), ensure_ascii=False)


def render_text(meta: dict, body: str) -> str:
    """front matter を決まった順序で書き出す（差分が読みやすいように）。"""
    lines = ["---", f"id: {meta['id']}", f"title: {_q(meta.get('title'))}",
             f"status: {meta.get('status', 'draft')}", f"cvss: {_q(meta.get('cvss'))}"]
    notes = {k: v for k, v in (meta.get("cvss_notes") or {}).items() if str(v).strip()}
    if notes:
        lines.append("cvss_notes:")
        lines += [f"  {k}: {_q(notes[k])}" for k in cvss31.KEYS if k in notes]
    else:
        lines.append("cvss_notes: {}")
    for key in ("wstg", "evidence"):
        vals = meta.get(key) or []
        if vals:
            lines.append(f"{key}:")
            lines += [f"  - {_q(v) if key == 'evidence' else v}" for v in vals]
        else:
            lines.append(f"{key}: []")
    for key in ("author", "created", "updated", "updated_by"):
        lines.append(f"{key}: {_q(meta.get(key))}")
    lines.append("---")
    body = (body or "").replace("\r\n", "\n").strip("\n")
    return "\n".join(lines) + "\n" + body + "\n"


def rev_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def enrich(meta: dict) -> dict:
    """表示用の派生値（深刻度・起こりやすさ・影響）を足す。"""
    r = cvss31.try_score(meta.get("cvss", ""))
    meta["score"] = r
    meta["severity"] = r["severity"] if r else "unrated"
    meta["severity_label"] = SEVERITY_LABEL[meta["severity"]]
    meta["base"] = r["base"] if r else None
    return meta


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    meta, body = parse_text(text)
    meta = dict(meta)
    meta.setdefault("id", path.stem)
    meta["id"] = str(meta["id"])
    meta["title"] = str(meta.get("title") or "")
    meta["status"] = str(meta.get("status") or "draft")
    meta["cvss"] = str(meta.get("cvss") or "")
    meta["cvss_notes"] = {str(k): str(v) for k, v in (meta.get("cvss_notes") or {}).items()}
    meta["wstg"] = [str(x) for x in (meta.get("wstg") or [])]
    meta["evidence"] = [str(x) for x in (meta.get("evidence") or [])]
    for key in ("author", "created", "updated", "updated_by"):
        meta[key] = "" if meta.get(key) is None else str(meta.get(key))
    meta["body"] = body
    meta["rev"] = rev_of(text)
    meta["path"] = path
    return enrich(meta)


def list_all(root: Path) -> list:
    """全所見（ID 順）。読めないファイルは警告して飛ばす。"""
    d = findings_dir(root)
    out = []
    if not d.exists():
        return out
    for p in sorted(d.glob("F-*.md"), key=lambda p: _id_num(p.stem)):
        if not ID_RE.match(p.stem):
            continue
        try:
            out.append(load(p))
        except (OSError, yaml.YAMLError) as exc:
            print(f"[警告] {p} を読めません: {exc}", file=sys.stderr)
    return out


def _id_num(fid: str) -> int:
    m = re.search(r"(\d+)$", fid)
    return int(m.group(1)) if m else 0


def get(root: Path, fid: str):
    if not ID_RE.match(fid):
        return None
    p = findings_dir(root) / f"{fid}.md"
    return load(p) if p.exists() else None


def by_wstg(findings: list) -> dict:
    """WSTG-ID → 所見のリスト。"""
    out: dict = {}
    for f in findings:
        for w in f["wstg"]:
            out.setdefault(w, []).append(f)
    return out


def sort_key(f: dict):
    """深刻度の高い順 → スコア → ID。"""
    return (SEVERITY_ORDER.index(f["severity"]), -(f["base"] or 0), _id_num(f["id"]))


# --- 検証・保存 -----------------------------------------------------------

def _now() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def normalize_evidence(root: Path, rel: str) -> str:
    """evidence ルートからの相対パスに正規化し、実在と範囲を確かめる。"""
    rel = str(rel).strip().replace("\\", "/")
    if rel.startswith("evidence/"):
        rel = rel[len("evidence/"):]
    rel = rel.lstrip("/")
    if not rel:
        raise FindingError("エビデンスのパスが空です")
    base = Path(root).resolve()
    target = (base / rel).resolve()
    try:
        parts = target.relative_to(base).parts
    except ValueError:
        raise FindingError(f"evidence の外は指定できません: {rel}") from None
    if not parts or parts[0].startswith(("_", ".")):
        raise FindingError(f"アクティビティのフォルダ配下を指定してください: {rel}")
    if not (base / parts[0] / "run.yaml").exists():
        raise FindingError(f"アクティビティのフォルダではありません: {parts[0]}")
    if not target.exists():
        raise FindingError(f"ファイルがありません: {rel}")
    out = "/".join(parts)
    return out + "/" if target.is_dir() else out


def validate(root: Path, data: dict, tests: dict) -> dict:
    """Web / CLI から来た入力を検証して meta の一部にする。"""
    title = " ".join(str(data.get("title", "")).split())
    if not title:
        raise FindingError("タイトルを入れてください（1行の見出し）")
    if len(title) > 200:
        raise FindingError("タイトルは 200 文字以内にしてください")
    status = str(data.get("status") or "draft")
    if status not in STATUSES:
        raise FindingError(f"状態が不正です: {status}")
    vector = str(data.get("cvss") or "").strip()
    if vector:
        try:
            vector = cvss31.score(vector)["vector"]
        except cvss31.CvssError as exc:
            raise FindingError(f"CVSS: {exc}") from None
    notes_in = data.get("cvss_notes") or {}
    if not isinstance(notes_in, dict):
        raise FindingError("cvss_notes の形式が不正です")
    notes = {}
    for k, v in notes_in.items():
        if k not in cvss31.KEYS:
            raise FindingError(f"cvss_notes に未知の指標: {k}")
        v = " ".join(str(v).split())
        if len(v) > 1000:
            raise FindingError(f"{k} の判断理由が長すぎます（1000 文字以内）")
        if v:
            notes[k] = v
    wstg = []
    for w in data.get("wstg") or []:
        w = str(w).strip().upper()
        if not w:
            continue
        if not WID_RE.match(w) or (tests and w not in tests):
            raise FindingError(f"未知の WSTG-ID: {w}")
        if w not in wstg:
            wstg.append(w)
    if not wstg:
        raise FindingError("関係する WSTG-ID を1つ以上入れてください")
    evidence = []
    for e in data.get("evidence") or []:
        if not str(e).strip():
            continue
        n = normalize_evidence(root, e)
        if n not in evidence:
            evidence.append(n)
    body = str(data.get("body") or "")
    if len(body) > 200_000:
        raise FindingError("本文が長すぎます（200KB 以内）")
    return {"title": title, "status": status, "cvss": vector, "cvss_notes": notes,
            "wstg": wstg, "evidence": evidence, "body": body}


def next_id(root: Path) -> str:
    d = findings_dir(root)
    nums = [_id_num(p.stem) for p in d.glob("F-*.md")] if d.exists() else []
    return f"F-{(max(nums) + 1 if nums else 1):03d}"


def create(root: Path, fields: dict, user: str) -> str:
    """新しい所見を作る（ID は空き番号を O_EXCL で確保）。ID を返す。"""
    d = findings_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    now = _now()
    meta = {**fields, "author": user, "created": now[:10], "updated": now, "updated_by": user}
    for _ in range(50):
        fid = next_id(root)
        meta["id"] = fid
        try:
            fd = os.open(d / f"{fid}.md", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            continue
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(render_text(meta, fields.get("body", "")))
        return fid
    raise FindingError("所見 ID を確保できませんでした。もう一度保存してください。")


def save(root: Path, fid: str, fields: dict, user: str, rev: str | None) -> None:
    """既存の所見を上書きする。rev が現在の内容と違えば Conflict（他の人の更新を潰さない）。"""
    cur = get(root, fid)
    if cur is None:
        raise FindingError(f"所見がありません: {fid}")
    if rev is not None and rev != cur["rev"]:
        raise Conflict(fid)
    meta = {**fields, "id": fid, "author": cur["author"], "created": cur["created"],
            "updated": _now(), "updated_by": user}
    cur["path"].write_text(render_text(meta, fields.get("body", "")), encoding="utf-8")


def attach(root: Path, fid: str, evidence: str, wid: str | None, user: str) -> None:
    """既存の所見にエビデンス（と WSTG-ID）を足す。"""
    cur = get(root, fid)
    if cur is None:
        raise FindingError(f"所見がありません: {fid}")
    ev = normalize_evidence(root, evidence) if evidence else None
    fields = {k: cur[k] for k in ("title", "status", "cvss", "cvss_notes", "wstg", "evidence", "body")}
    if ev and ev not in fields["evidence"]:
        fields["evidence"] = fields["evidence"] + [ev]
    if wid and WID_RE.match(wid) and wid not in fields["wstg"]:
        fields["wstg"] = fields["wstg"] + [wid]
    save(root, fid, fields, user, cur["rev"])


# --- 旧 findings.md からの移行 ---------------------------------------------

def parse_old_findings(text: str) -> dict:
    """旧 findings.md を WSTG-ID ごとの本文に分解する（見出し `## WSTG-XXX ...`）。"""
    out: dict = {}
    cur, buf = None, []
    for line in text.split("\n"):
        m = re.match(r"^##\s+(WSTG-[A-Z]+-\d+)\b", line)
        if m:
            if cur:
                out[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
            continue
        if cur is not None:
            buf.append(line)
    if cur:
        out[cur] = "\n".join(buf).strip()
    return {k: v for k, v in out.items() if v and v != OLD_FINDINGS_PLACEHOLDER}


def migrate(root: Path, dry_run: bool = False) -> list:
    """各アクティビティの findings.md（記入のある WSTG セクション）を F ファイル（draft）にする。

    移行済みの findings.md は findings.md.migrated に改名して残す（消さない）。
    タイトルは run.yaml の covers の finding（1行目）、無ければ「<WSTG-ID> の所見（移行）」。
    """
    made = []
    for fmd in sorted(Path(root).glob("*/findings.md")):
        act = fmd.parent
        sections = parse_old_findings(fmd.read_text(encoding="utf-8"))
        try:
            run = yaml.safe_load((act / "run.yaml").read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            run = {}
        covers = {c.get("id"): c for c in (run.get("covers") or []) if isinstance(c, dict)}
        for wid, text in sections.items():
            head = str(covers.get(wid, {}).get("finding") or "").strip().split("\n")[0].strip()
            title = head or f"{wid} の所見（findings.md から移行）"
            fields = {"title": title[:200], "status": "draft", "cvss": "", "cvss_notes": {},
                      "wstg": [wid], "evidence": [act.name + "/"],
                      "body": f"<!-- {act.name}/findings.md から移行 -->\n\n{text}\n"}
            made.append((act.name, wid, title))
            if not dry_run:
                create(root, fields, str(run.get("tester") or "migrate"))
        if not dry_run:
            fmd.rename(fmd.with_name("findings.md.migrated"))
    return made


# --- CLI ------------------------------------------------------------------

def _load_tests() -> dict:
    if not WSTG_TESTS.exists():
        return {}
    return {t["id"]: t for t in yaml.safe_load(WSTG_TESTS.read_text(encoding="utf-8"))["tests"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="evidence ルート（既定: evidence/）")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="所見の一覧")
    p_new = sub.add_parser("new", help="所見を作る（本文は Web かエディタで書く）")
    p_new.add_argument("--title", required=True)
    p_new.add_argument("--wstg", action="append", required=True, help="複数可")
    p_new.add_argument("--evidence", action="append", default=[], help="evidence ルートからの相対パス。複数可")
    p_new.add_argument("--cvss", default="", help="CVSS:3.1/... のベクトル（後から Web で選んでもよい）")
    p_new.add_argument("--user", default=os.environ.get("USER", "cli"))
    p_mig = sub.add_parser("migrate", help="旧 findings.md を F ファイルへ移行する")
    p_mig.add_argument("--dry-run", action="store_true", help="作る予定だけ表示する")
    args = ap.parse_args()
    root = Path(args.root)

    if args.cmd == "new":
        try:
            fields = validate(root, {"title": args.title, "wstg": args.wstg, "evidence": args.evidence,
                                     "cvss": args.cvss, "body": BODY_TEMPLATE}, _load_tests())
            fid = create(root, fields, args.user)
        except FindingError as exc:
            print(f"作れませんでした: {exc}", file=sys.stderr)
            return 2
        print(f"作成: {findings_dir(root) / (fid + '.md')}")
        print("  本文と CVSS は Web（uv run scripts/serve_record.py → 所見）で書くのが楽です。")
        return 0

    if args.cmd == "migrate":
        if not root.exists():
            print(f"{root} がありません。--root を確認してください。", file=sys.stderr)
            return 2
        made = migrate(root, args.dry_run)
        verb = "作成予定" if args.dry_run else "作成"
        for act, wid, title in made:
            print(f"  {verb}: {act} / {wid} — {title}")
        print(f"{len(made)} 件{'（dry-run）' if args.dry_run else ''}。"
              + ("" if args.dry_run else " 移行済みの findings.md は findings.md.migrated に改名しました。"
                 " 状態は draft なので、Web の所見ページで CVSS を選んで確定してください。"))
        return 0

    # list（既定）
    fs = list_all(root)
    if not fs:
        print("所見はまだありません。Web の record.html から『＋ 所見』で作れます。")
        return 0
    for f in sorted(fs, key=sort_key):
        sc = f"{f['base']:>4}" if f["base"] is not None else "  - "
        print(f"{f['id']}  {sc} {f['severity_label']:<8s} {STATUSES.get(f['status'], f['status']):<10s}"
              f" {','.join(f['wstg']):<28s} {f['title']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
