#!/usr/bin/env bash
# スクリプト群のスモークテスト。修正したら必ずこれを通してからコミットする。
#
#   ./scripts/selftest.sh
#
# 実 evidence/ には一切触らない。すべて一時ディレクトリ内で完結する。
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT
cd "${REPO_ROOT}"

# uv があれば uv run、無ければ system python3（会社PC 用のフォールバック）
if command -v uv >/dev/null 2>&1; then
  PY=(uv run --quiet python)
else
  PY=(python3)
fi
ok() { printf '  ok   %s\n' "$1"; }
ng() { printf '  NG   %s\n' "$1"; exit 1; }

echo "[1/8] 生成物が最新か（原文がある場合のみ）"
if compgen -G "docs/owasp/*" > /dev/null; then
  "${PY[@]}" scripts/build_wstg_index.py --check >/dev/null && ok "matrix/wstg_tests.yaml" \
    || ng "wstg_tests.yaml が古い: uv run scripts/build_wstg_index.py"
else
  echo "  skip WSTG 原文なし（./scripts/fetch_wstg.sh）"
fi
"${PY[@]}" scripts/build_coverage.py --check >/dev/null && ok "matrix/coverage.{yaml,md}" \
  || ng "coverage が古い: uv run scripts/build_coverage.py"

echo "[2/8] coverage.yaml と criteria.yaml の整合"
"${PY[@]}" - <<'PYEOF' || ng "matrix/*.yaml の整合が取れていない"
import sys, yaml
tests = {t["id"]: t for t in yaml.safe_load(open("matrix/wstg_tests.yaml"))["tests"]}
cov = yaml.safe_load(open("matrix/coverage.yaml"))
crit = yaml.safe_load(open("matrix/criteria.yaml"))
active = {i for i, t in tests.items() if not t.get("deprecated")}
bad = []
for a in cov["activities"]:
    for c in a["covers"]:
        if c["id"] not in tests:
            bad.append(f"{a['id']}: 未知の ID {c['id']}")
        if c.get("role", "primary") not in ("primary", "secondary"):
            bad.append(f"{a['id']}/{c['id']}: 不正な role")
bad += [f"criteria に未知の ID: {i}" for i in set(crit) - set(tests)]
missing = sorted(active - set(crit))
for b in bad:
    print("   ", b)
if missing:
    print(f"    判定基準が未記入: {len(missing)} 件 — {', '.join(missing[:5])} ...")
sys.exit(1 if bad else 0)
PYEOF
ok "coverage / criteria の ID がすべて実在"

echo "[3/8] new_activity.py（一時ディレクトリへ）"
"${PY[@]}" scripts/new_activity.py burp-crawl-authn --root "${TMP}/ev" --date 20260101 >/dev/null
DIR="${TMP}/ev/burp-crawl-authn-20260101"
[ -f "${DIR}/run.yaml" ] && [ -d "${DIR}/cmd" ] && [ -d "${DIR}/artifacts" ] || ng "雛形が作られない"
"${PY[@]}" -c "
import yaml,sys
d=yaml.safe_load(open('${DIR}/run.yaml'))
assert d['activity_id']=='burp-crawl-authn', d['activity_id']
assert [c['id'] for c in d['covers']], 'covers が空'
assert all(c['verdict']=='todo' for c in d['covers'])
" || ng "run.yaml のプリフィルが壊れている"
ok "run.yaml + cmd/ + artifacts/"

# .md 成果物の雛形（検索用フォーマット）が outputs から生成されるか
"${PY[@]}" scripts/new_activity.py recon-osint --root "${TMP}/ev" --date 20260101 >/dev/null
DORK="${TMP}/ev/recon-osint-20260101/artifacts/dorking-hits.md"
[ -f "${DORK}" ] || ng "outputs の .md 成果物の雛形が作られない（templates/artifacts/）"
grep -q "WSTG-INFO-01" "${DORK}" && grep -q "| dork |" "${DORK}" \
  || ng "成果物の雛形に WSTG-ID/検索用の見出しが埋まっていない"
ok ".md 成果物の雛形生成（templates/artifacts/）"

# --target 命名 + record.html / evidence.js 生成（表示は evidence.js から読む）
# evidence.js の commands を検索するヘルパ（JSON を読み、全手順のコマンドを平らにする）
cat > "${TMP}/ejs_has.py" <<'HELP'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
cmds = [r["cmd"] for it in d["items"] for st in it["steps"] for r in st["runs"] if r.get("cmd")]
sys.exit(0 if any(sys.argv[2] in c for c in cmds) else 1)
HELP
ejs_has () { "${PY[@]}" "${TMP}/ejs_has.py" "$1" "$2"; }

"${PY[@]}" scripts/new_activity.py recon-osint --target ex.test --root "${TMP}/ev" --date 20260101 >/dev/null
TDIR="${TMP}/ev/recon-osint-ex.test-20260101"
EJS="${TDIR}/evidence.js"
[ -f "${TDIR}/record.html" ] && [ -f "${EJS}" ] || ng "record.html / evidence.js が作られない"
grep -q "OUTDIR" "${EJS}" && ng "evidence.js に OUTDIR プレースホルダが残っている" || true
# コマンドが target 置換され、出力先が activity の artifacts/ に置換されていること
ejs_has "${EJS}" "whois ex.test" || ng "コマンドが target 置換されていない（whois）"
ejs_has "${EJS}" "mv theharvester.xml theharvester.json ${TDIR}/artifacts/" \
  || ng "theHarvester の出力を artifacts/ へ移す手順になっていない"
ejs_has "${EJS}" "-o ${TDIR}/artifacts/subfinder.txt" \
  || ng "複数コマンドの出力先が artifacts/ に置換されていない（subfinder）"
ejs_has "${EJS}" "head -c 400 ${TDIR}/artifacts/crtsh.json" \
  || ng "ファイル出力コマンドに確認コマンド（サイズ・先頭）が付いていない"
ejs_has "${EJS}" "wc -l ${TDIR}/artifacts/subfinder.txt" \
  || ng "テキスト出力コマンドに行数確認が付いていない"
ejs_has "${EJS}" "artifacts/ex.test" && ng "target 名を出力ファイルと誤認している" || true
# for/while ループ・OUTDIR に書く grep 後処理も実行コマンドとして拾うこと（CONF-10）
ejs_has "${EJS}" "while read -r h; do echo" || ng "for/while ループがコマンドとして拾われていない"
ejs_has "${EJS}" "wc -l ${TDIR}/artifacts/cname-check.txt" || ng "ループの tee 出力先に確認コマンドが付いていない"
ejs_has "${EJS}" "grep -iaE" || ng "OUTDIR に書く grep 後処理コマンドが拾われていない"
ejs_has "${EJS}" "tee ${TDIR}/artifacts/takeover-candidates.md" || ng "grep の tee 出力先が置換されていない"
# `-o a.txt; curl ...` の区切り `;` をパスに含めないこと（`wc -l a.txt;;` は構文エラー）
"${PY[@]}" scripts/new_activity.py metafiles-crawl --target ex.test --root "${TMP}/ev" --date 20260101 >/dev/null
MDIR="${TMP}/ev/metafiles-crawl-ex.test-20260101"
ejs_has "${MDIR}/evidence.js" "wc -l ${MDIR}/artifacts/robots.txt; head -5 ${MDIR}/artifacts/robots.txt" \
  || ng "コマンド末尾の ; が出力パスに混ざり確認コマンドが壊れる（robots.txt）"
ejs_has "${MDIR}/evidence.js" "head -c 400 ${MDIR}/artifacts/sitemap.xml" \
  || ng "コマンド末尾の ; が出力パスに混ざり確認コマンドが壊れる（sitemap.xml）"
# 手動手順は observe を書く .txt ひな型が作られること（dork は手動）
[ -f "${TDIR}/artifacts/manual-WSTG-INFO-01-s5.txt" ] || ng "手動手順の .txt ひな型が作られない"
# 手順の枠（desc）は簡単な説明で、生コマンドを含まないこと（コマンドは runs に分離）
"${PY[@]}" - "${EJS}" <<'DESC'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
for it in d["items"]:
    for st in it["steps"]:
        assert "$ " not in st["desc"] and "whois " not in st["desc"], ("desc に生コマンド: " + st["desc"])
        for r in st["runs"]:
            assert "output_path" in r, r
DESC
# record.html の JS 内の \n が実改行に化けていないこと（RECORD_HTML は raw 文字列）
grep -qF 'fr.src = r.output_path' "${TDIR}/record.html" \
  || ng "record.html がエビデンスを iframe 参照で表示していない"
grep -qF 'r.output && r.output' "${TDIR}/record.html" \
  && ng "record.html にエビデンス本体が埋め込まれている（参照でなく複製）" || true
ok "record.html / evidence.js 生成（target/OUTDIR 置換・手動ひな型）"

# 負荷・レート制限・ロック・DoS を招きうる手順の強調注釈（criteria.yaml の load_notes）
"${PY[@]}" scripts/new_activity.py account-enum-probe --root "${TMP}/ev" --date 20260101 >/dev/null
AEP="${TMP}/ev/account-enum-probe-20260101"
"${PY[@]}" - "${AEP}/evidence.js" <<'LOAD'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
notes = {(it["wid"], st["idx"]): st.get("load_note", "") for it in d["items"] for st in it["steps"]}
# ATHN-03 手順1（意図的ロック）に注釈があり、同じ項目の手順2には無いこと
assert notes.get(("WSTG-ATHN-03", 1)), ("ATHN-03 s1 に load_note が付いていない", notes.get(("WSTG-ATHN-03", 1)))
assert "テストアカウント" in notes[("WSTG-ATHN-03", 1)], notes[("WSTG-ATHN-03", 1)]
assert not notes.get(("WSTG-ATHN-03", 2)), "注釈の無い手順にまで load_note が付いている"
LOAD
[ $? -eq 0 ] || ng "load_note が evidence.js に反映されていない"
grep -qF 'st.load_note' "${AEP}/record.html" && grep -qF 'loadwarn' "${AEP}/record.html" \
  || ng "record.html が load_note を強調表示しない"
# カード側にも「負荷・レート制限」セクションと手順注釈が出ること
if compgen -G "docs/owasp/*" > /dev/null; then
  grep -qF "負荷・レート制限・想定外への注意" playbooks/WSTG-ATHN-03.md \
    && grep -qF "負荷注意（手順1）" playbooks/WSTG-ATHN-03.md \
    || ng "カードに負荷注意が出ていない: uv run scripts/gen_playbooks.py"
fi
ok "負荷・レート制限・ロック・DoS の強調注釈（load_notes → record.html / カード）"

# 判定理由（run.yaml の複数行 finding）と所見（evidence/_findings/F-*.md）
[ -f "${TDIR}/findings.md" ] && ng "旧 findings.md が作られている（所見は evidence/_findings/ に移行済み）" || true
"${PY[@]}" - "${TDIR}" <<'AB'
import sys, re, subprocess
from pathlib import Path
d = Path(sys.argv[1])
# INFO-01 に複数行 finding（ブロック）を入れる
rp = d / "run.yaml"; t = rp.read_text().split("\n")
i = next(k for k, l in enumerate(t) if re.match(r"^\s*-\s*id:\s*WSTG-INFO-01(\s|$|#)", l))
for k in range(i, i + 7):
    if t[k].strip().startswith("finding:"):
        t[k] = "    finding: |\n      1行目の見出し。\n      2行目。"
        break
rp.write_text("\n".join(t))
# 所見を CLI で作る（1所見に2つの WSTG・エビデンス付き）。traversal・未知 ID は拒否
root = d.parent
new = [sys.executable, "scripts/findings.py", "--root", str(root), "new", "--title", "所見テストA",
       "--wstg", "WSTG-INFO-01", "--wstg", "WSTG-CONF-10",
       "--evidence", f"{d.name}/artifacts/manual-WSTG-INFO-01-s5.txt",
       "--cvss", "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"]
subprocess.run(new, check=True, stdout=subprocess.DEVNULL)
for bad in (["--evidence", "../../etc/passwd"], ["--wstg", "WSTG-NOPE-99"]):
    r = subprocess.run(new[:5] + ["--title", "x", "--wstg", "WSTG-INFO-01"] + bad,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    assert r.returncode != 0, ("不正な所見を作れてしまう", bad)
f = (root / "_findings" / "F-001.md").read_text()
assert "WSTG-CONF-10" in f and "manual-WSTG-INFO-01-s5.txt" in f, f
subprocess.run([sys.executable, "scripts/gen_record.py", str(d)], check=True, stdout=subprocess.DEVNULL)
import json
ev = json.loads((d / "evidence.js").read_text().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
it = next(x for x in ev["items"] if x["wid"] == "WSTG-INFO-01")
assert "\n" in it["finding"], ("複数行 finding が反映されない", it["finding"])
assert [x["id"] for x in it["findings"]] == ["F-001"], ("所見が record に紐づかない", it["findings"])
assert it["findings"][0]["severity"] == "high" and it["findings"][0]["base"] == 7.5, it["findings"][0]
it2 = next(x for x in ev["items"] if x["wid"] == "WSTG-CONF-10")
assert [x["id"] for x in it2["findings"]] == ["F-001"], "1所見→複数 WSTG の紐づけが効かない"
# 旧 findings.md の移行: 記入のあるセクションだけ F ファイル（draft）になり、元は .migrated に残る
(d / "findings.md").write_text("# 所見メモ\n\n## WSTG-INFO-01 — x\n\n旧本文テスト\n\n## WSTG-CONF-10 — y\n\n"
                               "（ここに詳細な所見を書く。無ければ空のままでよい。生値は書かず evidence を参照）\n")
subprocess.run([sys.executable, "scripts/findings.py", "--root", str(root), "migrate"], check=True,
               stdout=subprocess.DEVNULL)
assert not (d / "findings.md").exists() and (d / "findings.md.migrated").exists(), "移行後の改名がされない"
f2 = (root / "_findings" / "F-002.md").read_text()
assert "旧本文テスト" in f2 and "status: draft" in f2 and "1行目の見出し。" in f2, f2
assert not (root / "_findings" / "F-003.md").exists(), "未記入のセクションまで移行している"
AB
[ $? -eq 0 ] || ng "所見（F ファイル）/ 複数行 finding / 移行 が想定通りでない"
grep -qF 'findingsBox(it)' "${TDIR}/record.html" || ng "record.html が所見を表示しない"
grep -qF 'location.hash' "${TDIR}/record.html" || ng "record.html が深いリンク（#WSTG-ID/s<n>）に対応していない"
# CVSS v3.1 の計算が仕様どおり（既知ベクトル）
"${PY[@]}" - <<'CV' || ng "CVSS v3.1 の計算が仕様とずれている"
import sys; sys.path.insert(0, "scripts")
import cvss31
cases = {"AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H": 9.8, "AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N": 6.1,
         "AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N": 6.5, "AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H": 7.8,
         "AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H": 10.0, "AV:N/AC:H/PR:H/UI:R/S:U/C:L/I:N/A:N": 2.0,
         "AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N": 0.0, "AV:N/AC:L/PR:H/UI:R/S:C/C:L/I:L/A:N": 4.8}
for v, want in cases.items():
    got = cvss31.score("CVSS:3.1/" + v)["base"]
    assert got == want, (v, got, want)
assert cvss31.score("CVSS:3.1/" + "AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")["severity"] == "none"
for bad in ("", "CVSS:3.0/AV:N", "CVSS:3.1/AV:X/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", "CVSS:3.1/AV:N"):
    try:
        cvss31.score(bad); raise SystemExit(f"不正なベクトルを通した: {bad}")
    except cvss31.CvssError:
        pass
CV
# CSV は複数行 finding を1行に畳み、所見は [F-ID 深刻度 スコア] タイトル で載る
"${PY[@]}" scripts/export_checklist.py --root "${TMP}/ev" --out "${TMP}/ab.csv" >/dev/null
"${PY[@]}" -c "
import csv
r=[x for x in csv.DictReader(open('${TMP}/ab.csv',encoding='utf-8-sig')) if x['wstg_id']=='WSTG-INFO-01'][0]
assert '\n' not in r['finding_summary'] and '見出し' in r['finding_summary'], r['finding_summary']
assert '[F-001 High 7.5] 所見テストA' in r['finding_summary'], r['finding_summary']
" || ng "CSV が複数行 finding を1行に畳めていない / 所見が載らない"
ok "所見 F ファイル（多対多・CVSS 自動深刻度・移行）＋複数行 finding（CSV は1行）"

# save_shot.py: クリップボード画像の代わりに --from で保存し、record.html に <img> 参照で出る
"${PY[@]}" - "${TMP}/dummy.png" <<'MKPNG'
import struct, zlib, sys
def chunk(t, d):
    c = t + d
    return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
       + chunk(b"IEND", b""))
open(sys.argv[1], "wb").write(png)
MKPNG
"${PY[@]}" scripts/save_shot.py "${TDIR}" --wid WSTG-INFO-01 --from "${TMP}/dummy.png" >/dev/null
ls "${TDIR}/artifacts/" | grep -q "^shot-WSTG-INFO-01-" || ng "save_shot が artifacts/ にスクショを保存しない"
"${PY[@]}" - "${TDIR}/evidence.js" <<'IMG'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
it = next(x for x in d["items"] if x["wid"] == "WSTG-INFO-01")
assert it["images"] and it["images"][0].startswith("artifacts/shot-WSTG-INFO-01-"), it["images"]
IMG
grep -qF 'im.className = "shot"' "${TDIR}/record.html" || ng "record.html がスクショを <img> 参照で表示しない"
# PNG でないデータは弾くこと
printf 'not a png' > "${TMP}/nope.txt"
"${PY[@]}" scripts/save_shot.py "${TDIR}" --wid WSTG-INFO-01 --from "${TMP}/nope.txt" >/dev/null 2>&1 \
  && ng "PNG でないデータを保存してしまう" || true
ok "save_shot: 画像を artifacts/ に保存し record.html に <img> 参照（非PNGは拒否）"

# serve_record.py: evidence ルートを統一配信（ページ群・record・書き込み API・CSRF・共有モード）
"${PY[@]}" - "${TMP}/ev" "recon-osint-ex.test-20260101" "${TMP}/dummy.png" <<'SRV'
import sys, threading, json, base64, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, "scripts")
import serve_record
root, folder, png = sys.argv[1], sys.argv[2], sys.argv[3]
httpd = serve_record.build_server(Path(root), "127.0.0.1", 0)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
B = f"http://127.0.0.1:{port}"
def get(path, hdr=None):
    r = urllib.request.urlopen(urllib.request.Request(B + path, headers=hdr or {}), timeout=30)
    return r.status, r.read().decode("utf-8", "replace")
def post(path, obj, hdr=None):
    h = {"Content-Type": "application/json", "X-WSTG-Request": "1"}
    h.update(hdr or {})
    h = {k: v for k, v in h.items() if v is not None}
    req = urllib.request.Request(B + path, data=json.dumps(obj).encode(), headers=h, method="POST")
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        return {"status": e.code, **json.load(e)}
def fpost(route, obj):
    return post(f"/{folder}{route}", obj)
try:
    # ページ群（ダッシュボード・タスク・WSTG 索引/詳細・所見・カード・CSV）
    s, idx = get("/")
    assert "WSTG 実施状況" in idx and folder in idx, "ダッシュボードにアクティビティが出ない"
    s, t = get("/tasks")
    assert f"evidence/{folder}" in t and 'data-check="p0:agree"' in t, "タスクに実行コマンド/手動チェックが出ない"
    s, w = get("/wstg/")
    assert f"/{folder}/record.html#WSTG-INFO-01" in w and "F-001" in w, "WSTG 索引から記録・所見へリンクしない"
    s, wd = get("/wstg/WSTG-INFO-01")
    assert "所見テストA" in wd, "WSTG 詳細に所見が出ない"
    s, fp = get("/findings/F-001")
    assert "7.5" in fp and f"/{folder}/record.html#WSTG-INFO-01/s5" in fp, "所見からエビデンスへの深いリンクがない"
    assert get("/findings/new?wid=WSTG-INFO-01")[0] == 200 and get("/findings/F-001/edit")[0] == 200
    assert get("/playbooks/WSTG-INFO-01")[0] == 200
    s, csv_text = get("/export.csv")
    assert csv_text.lstrip("﻿").startswith("wstg_id,category,title,status"), "CSV の列契約が崩れた"
    assert json.loads(get("/api/cvss?vector=CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H")[1])["score"]["base"] == 9.8
    for bad in ("/findings/F-999", "/wstg/WSTG-NOPE-01", "/.git/config"):
        try:
            get(bad); raise SystemExit(f"404 にならない: {bad}")
        except urllib.error.HTTPError as e:
            assert e.code == 404, (bad, e.code)
    r = urllib.request.urlopen(f"{B}/{folder}/record.html", timeout=5)
    assert r.status == 200 and b"WSTG_EVIDENCE" in r.read(), "record.html を配信していない"
    # CSRF: 独自ヘッダなし・Origin 不一致の書き込みは 403
    assert post("/api/check", {"key": "p0:agree", "on": True}, {"X-WSTG-Request": None})["status"] == 403
    assert post("/api/check", {"key": "p0:agree", "on": True}, {"Origin": "http://evil.example"})["status"] == 403
    assert post("/api/check", {"key": "p0:agree", "on": True}, {"Origin": B})["ok"] is True
    assert "p0:agree" in (Path(root) / "_state" / "checks.yaml").read_text()
    assert post("/api/check", {"key": "bad key!", "on": True})["ok"] is False
    # capture: 不正 wid を弾く・撮影ツールが無い環境なので ok:false（＝API 経路は生きている）
    assert fpost("/api/capture", {"wid": "nope", "step": 1, "delay": 0})["ok"] is False, "不正 wid を弾かない"
    # upload_shot: ブラウザから貼った PNG を artifacts/shot-* に保存。PNG 以外は拒否
    data = base64.b64encode(Path(png).read_bytes()).decode()
    up = fpost("/api/upload_shot", {"wid": "WSTG-INFO-01", "step": 5, "data": data})
    assert up["ok"] and up["path"].startswith("artifacts/shot-WSTG-INFO-01-s5-"), up
    assert fpost("/api/upload_shot", {"wid": "WSTG-INFO-01", "data": base64.b64encode(b"GIF89a").decode()})["ok"] is False
    # delete_shot: traversal/非shot は拒否、shot は消せる
    assert fpost("/api/delete_shot", {"path": "../../etc/passwd"})["ok"] is False, "traversal を許した"
    assert fpost("/api/delete_shot", {"path": "run.yaml"})["ok"] is False, "shot 以外を消せてしまう"
    assert fpost("/api/delete_shot", {"path": up["path"]})["ok"] is True, "shot を削除できない"
    assert not (Path(root) / folder / up["path"]).exists(), "shot が消えていない"
    # /api/save: verdict/finding（判定理由）を run.yaml にテキスト部分置換で保存
    import yaml as _yaml
    assert fpost("/api/save", {"wid": "WSTG-INFO-01", "verdict": "bad"})["ok"] is False, "不正 verdict を通した"
    assert fpost("/api/save", {"wid": "WSTG-INFO-01", "verdict": "fail", "finding": "見出しA\n見出しB"})["ok"]
    y = _yaml.safe_load((Path(root) / folder / "run.yaml").read_text())
    cov = {x["id"]: x for x in y["covers"]}
    assert cov["WSTG-INFO-01"]["verdict"] == "fail" and "\n" in cov["WSTG-INFO-01"]["finding"], cov["WSTG-INFO-01"]
    assert cov["WSTG-CONF-10"]["verdict"] == "todo", "他ブロックが壊れた"
    # /api/save_output: cmd/・artifacts/ 直下の .txt のみ
    assert fpost("/api/save_output", {"path": "cmd/WSTG-INFO-01-s1-c1.txt", "content": "貼った結果X"})["ok"] is True
    assert (Path(root) / folder / "cmd" / "WSTG-INFO-01-s1-c1.txt").read_text() == "貼った結果X"
    assert fpost("/api/save_output", {"path": "../../etc/x.txt", "content": "x"})["ok"] is False, "traversal を許した"
    assert fpost("/api/save_output", {"path": "run.yaml", "content": "x"})["ok"] is False, "run.yaml を書けてしまう"
    assert fpost("/api/save_output", {"path": "cmd/x.png", "content": "x"})["ok"] is False, ".txt 以外を書けてしまう"
    # 所見 API: 作成（CVSS から深刻度）・添付・楽観ロック（古い rev は 409）
    ev = f"{folder}/cmd/WSTG-INFO-01-s1-c1.txt"
    r = post("/api/finding/save", {"title": "Web 作成", "status": "draft", "wstg": ["WSTG-INFO-01"],
                                   "evidence": [ev], "cvss": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N",
                                   "cvss_notes": {"UI": "リンクを踏ませる"}, "body": "本文"})
    assert r["ok"], r
    fid = r["id"]
    assert post("/api/finding/save", {"title": "x", "wstg": [], "body": ""})["ok"] is False, "WSTG なしで作れる"
    assert post("/api/finding/save", {"title": "x", "wstg": ["WSTG-INFO-01"], "cvss": "CVSS:3.1/AV:N"})["ok"] is False
    assert post("/api/finding/attach", {"id": fid, "ev": "../../etc/passwd", "wid": ""})["ok"] is False
    assert post("/api/finding/attach", {"id": fid, "ev": f"{folder}/artifacts/manual-WSTG-INFO-01-s5.txt",
                                        "wid": "WSTG-CONF-10"})["ok"]
    import findings as _f
    cur = _f.get(Path(root), fid)
    assert cur["severity"] == "medium" and cur["base"] == 6.1 and len(cur["evidence"]) == 2, cur
    assert cur["wstg"] == ["WSTG-INFO-01", "WSTG-CONF-10"], cur["wstg"]
    stale = post("/api/finding/save", {"id": fid, "rev": "0000", "title": "上書き", "wstg": ["WSTG-INFO-01"]})
    assert stale.get("status") == 409, ("古い版の上書きを通した", stale)
    ok = post("/api/finding/save", {"id": fid, "rev": cur["rev"], "title": "上書き", "status": "confirmed",
                                    "wstg": ["WSTG-INFO-01"], "cvss": cur["cvss"], "body": "b"})
    assert ok["ok"] and _f.get(Path(root), fid)["status"] == "confirmed", ok
finally:
    httpd.shutdown(); httpd.server_close()

# 共有モード（nginx の後ろ）: 編集者名は X-Remote-User、サーバ画面の撮影は無効
httpd = serve_record.build_server(Path(root), "127.0.0.1", 0, behind_proxy=True)
port = httpd.server_address[1]
B = f"http://127.0.0.1:{port}"
threading.Thread(target=httpd.serve_forever, daemon=True).start()
try:
    info = json.loads(get("/api/info", {"X-Remote-User": "alice"})[1])
    assert info == {"capture": False, "user": "alice"}, info
    r = fpost("/api/capture", {"wid": "WSTG-INFO-01", "step": 1, "delay": 0})
    assert r["ok"] is False and "共有モード" in r["error"], r
    r = post("/api/finding/save", {"title": "共有で作成", "wstg": ["WSTG-INFO-01"], "body": ""},
             {"X-Remote-User": "alice"})
    assert r["ok"] and _f.get(Path(root), r["id"])["author"] == "alice", r
finally:
    httpd.shutdown(); httpd.server_close()
SRV
[ $? -eq 0 ] || ng "serve_record の配信 / API が想定通りでない"
ok "serve_record: ページ群（索引・WSTG・所見・タスク・CSV）＋書き込み API＋CSRF＋共有モード"
timeout 10 "${PY[@]}" scripts/serve_record.py "${TMP}/ev" --host 0.0.0.0 --port 0 >/dev/null 2>&1 \
  && ng "serve_record が 127.0.0.1 以外での待受を許した（共有は nginx 経由だけ）" || true
ok "serve_record は 127.0.0.1 以外での待受を拒否"

# fingerprint-stack: NVD 照合が curl/jq、受動観測が curl、確認コマンドは重複しないこと
"${PY[@]}" scripts/new_activity.py fingerprint-stack --target ex.test --root "${TMP}/ev" --date 20260101 >/dev/null
FDIR="${TMP}/ev/fingerprint-stack-ex.test-20260101"
FEJS="${FDIR}/evidence.js"
"${PY[@]}" - "${FEJS}" "${FDIR}" <<'DEDUP'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
fdir = sys.argv[2]
cmds = [r["cmd"] for it in d["items"] for st in it["steps"] for r in st["runs"] if r.get("cmd")]
need = f"wc -l {fdir}/artifacts/nvd-cve.tsv"
assert sum(1 for c in cmds if need in c) == 1, "確認コマンドが重複している"
assert any('curl -s -m 30 "https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=$cpe' in c for c in cmds), "CVE 照合が curl（検出した CPE で引く）になっていない"
assert any("keywordSearch=$kw" in c and "jq -r" in c for c in cmds), "CPE 照合が検出した製品名で引く curl/jq になっていない"
assert any(f"curl -sD {fdir}/artifacts/headers.txt -o /dev/null https://ex.test/" in c for c in cmds), "ヘッダ取得が curl になっていない"
DEDUP
ok "NVD 照合(curl/jq)・受動観測(curl)・確認コマンド重複なし（evidence.js）"

# run_activity.py: dry-run で実行コマンドを提示、実行でエビデンス生成＋run.yaml追記＋evidence.js更新
"${PY[@]}" scripts/new_activity.py fingerprint-stack --target 127.0.0.1:9 --root "${TMP}/ev" --date 20260101 >/dev/null
RDIR="${TMP}/ev/fingerprint-stack-127.0.0.1-9-20260101"
"${PY[@]}" scripts/run_activity.py "${RDIR}" --only WSTG-INFO-02:1 --dry-run > "${TMP}/dry.txt"
grep -q '\$ curl -sI https://127.0.0.1:9/' "${TMP}/dry.txt" || ng "run_activity --dry-run が実行コマンドを出さない"
# 実行（閉じたポート＝オフラインで即失敗。ネットワークに出ない）
"${PY[@]}" scripts/run_activity.py "${RDIR}" --only WSTG-INFO-02:1 --timeout 8 >/dev/null 2>&1 || true
[ -s "${RDIR}/cmd/WSTG-INFO-02-s1-c1.txt" ] || ng "run_activity がコマンド別エビデンスファイルを作らない"
"${PY[@]}" -c "
import yaml
c=yaml.safe_load(open('${RDIR}/run.yaml'))['commands']
assert any(x['output']=='cmd/WSTG-INFO-02-s1-c1.txt' for x in c), 'commands: に追記されない'
" || ng "run_activity が run.yaml の commands: に追記しない"
"${PY[@]}" -c "
import json
d=json.loads(open('${RDIR}/evidence.js').read().split('window.WSTG_EVIDENCE = ',1)[1].rstrip(';\n'))
r=d['items'][0]['steps'][0]['runs'][0]
assert r['has_output'] and r['output_path']=='cmd/WSTG-INFO-02-s1-c1.txt', r
assert 'output' not in r, ('中身を埋め込んでいる（参照のはず）: ' + str(r))
" || ng "run_activity 後に evidence.js が出力ファイルを参照しない"
ok "run_activity: dry-run 提示・実行でエビデンス/commands/evidence.js を更新"

# パスを間違えても（--target を付けた活動を target 抜きで叩く等）近いフォルダを提案すること
"${PY[@]}" scripts/run_activity.py "${TMP}/ev/recon-osint-19990101" > "${TMP}/miss.txt" 2>&1 || true
grep -q "recon-osint-ex.test-20260101" "${TMP}/miss.txt" \
  || ng "存在しないパスで近い名前の既存フォルダを提案しない"
ok "run.yaml が無いパスは近い既存フォルダを提案する"

# 判定は run.yaml の covers に直接記入 → gen_record.py で record.html に反映（エビデンスは失わない）
"${PY[@]}" - "${RDIR}" <<'VERDICT'
import sys, re
from pathlib import Path
rp = Path(sys.argv[1]) / "run.yaml"; lines = rp.read_text(encoding="utf-8").split("\n")
i = next(k for k,l in enumerate(lines) if re.match(r"^\s*-\s*id:\s*WSTG-INFO-02(\s|$|#)", l))
for k in range(i, i+6):
    if lines[k].strip().startswith("verdict:"): lines[k] = re.sub(r"verdict:\s*\S+", "verdict: fail", lines[k])
    if lines[k].strip().startswith("finding:"): lines[k] = '    finding: "要約のみ"'
rp.write_text("\n".join(lines), encoding="utf-8")
VERDICT
"${PY[@]}" scripts/gen_record.py "${RDIR}" >/dev/null
[ -s "${RDIR}/cmd/WSTG-INFO-02-s1-c1.txt" ] || ng "gen_record 後にエビデンスファイルが消えた"
"${PY[@]}" -c "
import json
d=json.loads(open('${RDIR}/evidence.js').read().split('window.WSTG_EVIDENCE = ',1)[1].rstrip(';\n'))
it=d['items'][0]
assert it['verdict']=='fail' and it['finding']=='要約のみ', it
assert it['steps'][0]['runs'][0]['has_output'], '収集済みの出力が参照されていない'
" || ng "gen_record が run.yaml の判定を反映しない / 参照が壊れた"
ok "判定は run.yaml 直記入 → gen_record で反映（再生成でエビデンスを失わない）"

echo "[4/8] run_cmd.py（実行・保存・追記）"
"${PY[@]}" scripts/run_cmd.py "${DIR}" --slug selftest -- printf 'selftest\n' >/dev/null
[ -s "${DIR}/cmd/selftest.txt" ] || ng "cmd/ に出力が残らない"
"${PY[@]}" -c "
import yaml
c=yaml.safe_load(open('${DIR}/run.yaml'))['commands']
assert len(c)==1 and c[0]['exit_code']==0 and c[0]['output']=='cmd/selftest.txt', c
" || ng "commands: への追記が壊れている"
"${PY[@]}" scripts/run_cmd.py "${DIR}" -- nosuchcommand_selftest >/dev/null 2>&1 || true
"${PY[@]}" -c "
import yaml
c=yaml.safe_load(open('${DIR}/run.yaml'))['commands']
assert len(c)==2 and c[1]['exit_code']==127, c
" || ng "コマンド未検出時に記録されない"
ok "cmd/ 保存 + commands: 追記（正常系・異常系）"

# run_target.py: 一括作成（既存はスキップ）と、実行の再開/停止ロジック
"${PY[@]}" scripts/run_target.py --target rt.test --root "${TMP}/rt" --no-run >/dev/null \
  || ng "run_target --no-run が失敗した"
# target_kind: domain（recon-osint 等）は一括対象外
NACT=$("${PY[@]}" -c "import yaml;print(sum(a.get('target_kind')!='domain' for a in yaml.safe_load(open('matrix/coverage.yaml'))['activities']))")
NDIR=$(ls -d "${TMP}/rt"/*/ 2>/dev/null | wc -l)
[ "${NDIR}" = "${NACT}" ] || ng "run_target が一括対象のアクティビティ分のフォルダを作らない（${NDIR}/${NACT}）"
ls -d "${TMP}/rt"/recon-osint-* >/dev/null 2>&1 && ng "run_target が target_kind: domain の recon-osint を一括で作った"
# 2回目は作り直さない（作成 0）
"${PY[@]}" scripts/run_target.py --target rt.test --root "${TMP}/rt" --no-run 2>&1 \
  | grep -q "作成 0 / 既存 ${NACT}" || ng "run_target 再実行で既存フォルダを作り直している"
# --reuse-latest: 日付違いの既存フォルダを使い回す（新しい日付のフォルダを作らない）
"${PY[@]}" scripts/run_target.py --target rt.test --root "${TMP}/rt" --no-run --reuse-latest \
  --date 29991231 2>&1 | grep -q "作成 0 / 既存 ${NACT}" \
  || ng "run_target --reuse-latest が日付違いの既存フォルダを使わない"
ls -d "${TMP}/rt"/*-29991231 >/dev/null 2>&1 && ng "run_target --reuse-latest が新しい日付のフォルダを作った"
# execute_steps の skip_done / stop_on_error（ネットワークを使わない echo で検証）
# --only なら domain のものも個別に作れる
"${PY[@]}" scripts/run_target.py --target rt.test --root "${TMP}/rt2" --no-run --only recon-osint >/dev/null \
  || ng "run_target --only recon-osint が失敗した"
RTD=$(ls -d "${TMP}/rt2"/recon-osint-* 2>/dev/null | head -1)
[ -n "${RTD}" ] || ng "run_target --only recon-osint でフォルダが作られない"
"${PY[@]}" - "${RTD}" <<'RT' || ng "execute_steps の再開/停止が期待通りでない"
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
from run_activity import execute_steps
d = Path(sys.argv[1]); ry = d / "run.yaml"
def st(i, cmd, out): return {"wid":"T","idx":i,"desc":"t","runs":[{"cmd":cmd,"output":out,"role":"primary"}]}
todo = [st(1,"echo ok","cmd/rt-s1.txt"), st(2,"exit 5","cmd/rt-s2.txt"), st(3,"echo z","cmd/rt-s3.txt")]
def sm(r): return {k: r[k] for k in ("ran","failed","skipped","aborted")}
s = execute_steps(ry, d, todo, timeout=None, skip_done=True, stop_on_error=True)
assert sm(s) == {"ran":2,"failed":1,"skipped":0,"aborted":True}, s          # s2 で停止、s3 は走らない
assert not (d/"cmd/rt-s3.txt").exists(), "stop_on_error なのに後続が走った"
s2 = execute_steps(ry, d, todo, timeout=None, skip_done=True, stop_on_error=True)
assert sm(s2) == {"ran":1,"failed":1,"skipped":1,"aborted":True}, s2        # s1 は成功済みでスキップ
s3 = execute_steps(ry, d, todo, timeout=None, skip_done=True, stop_on_error=False)
assert s3["skipped"]==1 and s3["aborted"] is False and (d/"cmd/rt-s3.txt").exists(), s3  # keep-going
# 手順を直して同じ出力パスのコマンドが変わったら、前回成功でも再実行する（古いエビデンスで飛ばさない）
todo[0] = st(1,"echo changed","cmd/rt-s1.txt")
s4 = execute_steps(ry, d, todo[:1], timeout=None, skip_done=True, stop_on_error=True)
assert sm(s4) == {"ran":1,"failed":0,"skipped":0,"aborted":False}, s4
s5 = execute_steps(ry, d, todo[:1], timeout=None, skip_done=True, stop_on_error=True)
assert s5["skipped"]==1 and s5["ran"]==0, s5
# 入力待ち（exit 75）は非0終了に数えず止めない。その手順の残りは飛ばし、次回も再実行される
pend = [{"wid":"T","idx":7,"desc":"t","runs":[{"cmd":"test -s nope || exit 75","output":"cmd/rt-s7-c1.txt","role":"main"},
                                              {"cmd":"echo after","output":"cmd/rt-s7-c2.txt","role":"main"}]},
        st(8,"echo next","cmd/rt-s8.txt")]
s6 = execute_steps(ry, d, pend, timeout=None, skip_done=True, stop_on_error=True)
assert s6["pending"]==1 and s6["failed"]==0 and s6["aborted"] is False and len(s6["waiting"])==1, s6
assert not (d/"cmd/rt-s7-c2.txt").exists() and (d/"cmd/rt-s8.txt").exists(), "入力待ちの後の扱いが違う"
s7 = execute_steps(ry, d, pend, timeout=None, skip_done=True, stop_on_error=True)
assert s7["pending"]==1 and s7["skipped"]==1, s7   # 入力待ちは成功扱いでスキップしない
# 入力待ちは同じファイルを使う後続の手順にも連鎖し（実行しない）、入力を置けば続きが走る。
# 参照する artifacts/ のファイルが前回の出力より新しければ成功済みでも再実行する（make と同じ）
import os, time
A = f"{d}/artifacts"
chain = [st(11, f"test -s {A}/in.txt || exit 75; cat {A}/in.txt", "cmd/ch-s11.txt"),
         st(12, f"grep x {A}/in.txt > {A}/out.txt || [ $? -eq 1 ]", "cmd/ch-s12.txt"),
         st(13, f"cat {A}/out.txt", "cmd/ch-s13.txt"),
         st(14, "echo indep", "cmd/ch-s14.txt")]
c1 = execute_steps(ry, d, chain, timeout=None, skip_done=True, stop_on_error=True)
assert c1["pending"]==3 and c1["ran"]==2 and c1["failed"]==0 and not c1["aborted"], c1
assert "exit_code: 75" in (d/"cmd/ch-s12.txt").read_text() and not (d/"artifacts/out.txt").exists()
(d/"artifacts/in.txt").write_text("x\n")
c2 = execute_steps(ry, d, chain, timeout=None, skip_done=True, stop_on_error=True)
assert c2["pending"]==0 and c2["ran"]==3 and c2["skipped"]==1 and c2["failed"]==0, c2
c3 = execute_steps(ry, d, chain, timeout=None, skip_done=True, stop_on_error=True)
assert c3["ran"]==0 and c3["skipped"]==4, c3
t = time.time() + 60; os.utime(d/"artifacts/in.txt", (t, t))     # 入力を差し替えた
c4 = execute_steps(ry, d, chain, timeout=None, skip_done=True, stop_on_error=True)
assert c4["ran"]==3 and c4["skipped"]==1, c4                      # in.txt→out.txt を使う3つが再実行
# 手動→コマンド（人の作業で置く入力を読む手順）は一括では走らせず、--only で明示したときだけ走る。
# まだ実行していない手動→コマンドが参照するファイルを読む後続は入力待ち。実行が済めば走る
from run_activity import select_steps, manual_run_steps
mr = {"wid":"T","idx":21,"desc":"m","kind":"cmd","manual_run":True,
      "runs":[{"cmd":f"test -s {A}/mi.txt || exit 75; cat {A}/mi.txt > {A}/mo.txt","output":"cmd/mr-s21.txt","role":"main"}]}
dep = dict(st(22, f"cat {A}/mo.txt", "cmd/mr-s22.txt"), kind="cmd")
assert select_steps([mr, dep], None) == [dep] and manual_run_steps([mr, dep]) == [mr]
assert select_steps([mr, dep], "T:21") == [mr]
m1 = execute_steps(ry, d, [dep], timeout=None, skip_done=True, stop_on_error=True, manual=[mr])
assert m1["pending"]==1 and m1["ran"]==0 and not (d/"cmd/mr-s21.txt").exists(), m1   # 手動は走らない
(d/"artifacts/mi.txt").write_text("m\n")                           # 人の作業
m2 = execute_steps(ry, d, [mr], timeout=None, skip_done=True, stop_on_error=True)  # --only 相当
assert m2["ran"]==1 and m2["failed"]==0 and (d/"artifacts/mo.txt").exists(), m2
m3 = execute_steps(ry, d, [dep], timeout=None, skip_done=True, stop_on_error=True, manual=[mr])
assert m3["pending"]==0 and m3["ran"]==1 and m3["failed"]==0, m3
RT
# 実行されるコマンドに日本語のプレースホルダ（<JSフォルダ> 等）が残っていない
# （bash はリダイレクトと解釈して失敗する）。入力置き場 OUTDIR/<name>/ は実行前に作られる
"${PY[@]}" - "${RTD}" <<'PH' || ng "コマンドにプレースホルダ（日本語の <…> やワードリストの仮名）が残っている、または入力置き場が作られない"
import re, sys; sys.path.insert(0, "scripts")
from pathlib import Path
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
from run_activity import run_command
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
bad = [(s["wid"], s["idx"], m) for a in cov["activities"]
       for s in iter_steps(a, cr, "t.test", "X") if s["kind"] == "cmd"
       for r in s["runs"] for m in re.findall(r"<[^<>]*[^\x00-\x7f][^<>]*>", r["cmd"])]
assert not bad, bad
# ワードリストを取るツール（ffuf 等）の -w が `wordlist` のような仮名のままだと、リポジトリ直下の
# 存在しないファイルを探して ffuf がヘルプを吐いて止まる。絶対パスか ${環境変数:-既定} にする
wl = [(s["wid"], s["idx"], m) for a in cov["activities"]
      for s in iter_steps(a, cr, "t.test", "X") if s["kind"] == "cmd"
      for r in s["runs"] if re.match(r"(ffuf|gobuster|wfuzz|dirsearch|hydra)\b", r["cmd"])
      for m in re.findall(r"\s-[wPL]\s+([^\s\"'$/][^\s]*)", r["cmd"])]
assert not wl, wl
d = Path(sys.argv[1])
st = {"wid": "T", "idx": 9, "desc": "t", "runs": []}
e = run_command({"cmd": f"test -d {d}/artifacts/jsin/", "output": "cmd/ph.txt", "role": "primary"}, st, d, None)
assert e["exit_code"] == 0 and (d / "artifacts/jsin").is_dir(), e
PH
# 末尾が裸の grep（パイプ・リダイレクトなし）のコマンドは「一致なし」を exit 1 で返し一括を止める。
# ヘッダ無し等は判定材料であって失敗ではないので `|| [ $? -eq 1 ]` で吸収する（exit 2 は止める）
# 同様に `grep -q A && echo 危険` で終わるコマンドは「該当なし」（＝良い結果）で exit 1 になるので
# `if grep -q A; then echo 危険; fi` の形にする
"${PY[@]}" - <<'GREP' || ng "末尾が grep / && echo のコマンドに「一致なし」の吸収（|| [ \$? -eq 1 ] か if）が無い"
import re, sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
bad = sorted({(s["wid"], s["idx"]) for a in cov["activities"]
              for s in iter_steps(a, cr, "t.test", "X") if s["kind"] == "cmd"
              for r in s["runs"]
              if re.search(r"(^|&&|;|\{)\s*grep\s[^|>;&]*$", r["cmd"].strip())
              or re.search(r"&&\s*(echo|printf)\b[^;|&]*$", r["cmd"].strip())})
assert not bad, bad
GREP
# nmap はプロキシを通らず、プロキシ配下では全ポート filtered のまま exit 0 で終わる（何も取れていないのに
# 成功扱いになる）。コマンド手順では nmap を使わず curl 等のプロキシを通るツールで代替する（README 参照）
"${PY[@]}" - <<'NMAP' || ng "コマンド手順に nmap がある（プロキシを通らず、filtered でも成功扱いになる）"
import re, sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
bad = sorted({(s["wid"], s["idx"]) for a in cov["activities"]
              for s in iter_steps(a, cr, "t.test", "X") if s["kind"] == "cmd"
              for r in s["runs"] if re.search(r"(^|[;&|{]\s*)(sudo\s+(-E\s+)?)?nmap\b", r["cmd"])})
assert not bad, bad
NMAP
# 確認コマンドは表示のため。本体が意図して出力を作らずに正常終了したとき（照合対象なし等）に
# 確認が失敗して一括を止めない（出力が無ければその旨を出して exit 0）
"${PY[@]}" - "${TMP}" <<'VCHK' || ng "出力ファイルが無いと確認コマンドが非0終了して一括処理を止める"
import subprocess, sys; sys.path.insert(0, "scripts")
from new_activity import verify_commands
d = f"{sys.argv[1]}/vchk"
for c in verify_commands(f"curl -o {d}/artifacts/a.json u | tee {d}/artifacts/b.txt", d):
    p = subprocess.run(["bash", "-c", c], capture_output=True, text=True)
    assert p.returncode == 0 and "出力なし" in p.stdout, (c, p.returncode, p.stdout, p.stderr)
VCHK
# 手順のコマンドを record.html から編集できる（run.yaml の cmd_overrides に保存）。編集すると
# コマンドが変わるので --skip-done でも再実行され、確認コマンドも編集後のコマンドから作り直される
"${PY[@]}" - "${TMP}" <<'OVR' || ng "コマンド編集（cmd_overrides）が iter_steps に反映されない／run.yaml の部分編集が壊れる"
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
import new_activity as na
from run_activity import is_done
d = Path(sys.argv[1]) / "ovr"; (d / "cmd").mkdir(parents=True, exist_ok=True)
(d / "run.yaml").write_text("# keep\nactivity_id: fingerprint-stack\ntarget_scope: t.example.com\n", encoding="utf-8")
a, t, c, tg, ad = na.resolve_activity(d)
def main1():
    for s in na.iter_steps(a, c, tg, ad, na.load_overrides(d)):
        if s["wid"] == "WSTG-INFO-02" and s["idx"] == 1:
            return [r["cmd"] for r in s["runs"] if r["role"] == "main"][0]
base = main1()
na.set_cmd_override(d, "WSTG-INFO-02-s1-c1", "curl -sI https://t.example.com/edited")
assert main1() == "curl -sI https://t.example.com/edited" and base != main1()
assert (d / "run.yaml").read_text().startswith("# keep")   # 先頭コメントが残る
# 実行済み（既定コマンドで exit 0）でも、編集後は再実行対象になる
r0 = [x for s in na.iter_steps(a, c, tg, ad) if s["wid"] == "WSTG-INFO-02" and s["idx"] == 1 for x in s["runs"] if x["role"] == "main"][0]
(d / r0["output"]).write_text(f"$ {r0['cmd']}\n# {'-'*68}\n# exit_code: 0  duration_sec: 0.1\n", encoding="utf-8")
r1 = [x for s in na.iter_steps(a, c, tg, ad, na.load_overrides(d)) if s["wid"] == "WSTG-INFO-02" and s["idx"] == 1 for x in s["runs"] if x["role"] == "main"][0]
assert is_done(d, r1) is False
na.set_cmd_override(d, "WSTG-INFO-02-s1-c1", "")   # 空で既定に戻る
assert main1() == base and "cmd_overrides" not in (d / "run.yaml").read_text()
OVR
# ツール未導入（command not found = exit 127）は一括を止めず飛ばし、導入方法を出す
"${PY[@]}" - "${TMP}" <<'TOOL' || ng "ツール未導入（exit 127）で一括処理が止まる／飛ばした記録が残らない"
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
from run_activity import execute_steps
d = Path(sys.argv[1]) / "toolmiss"; (d / "cmd").mkdir(parents=True, exist_ok=True)
(d / "run.yaml").write_text("activity_id: x\ncommands:\n", encoding="utf-8")
def st(i, cmd, out):
    return {"wid": "T", "idx": i, "desc": "t", "kind": "cmd",
            "runs": [{"cmd": cmd, "output": out, "role": "main"}]}
todo = [st(1, "echo ok", "cmd/s1.txt"), st(2, "sqlmap -u x --batch", "cmd/s2.txt"), st(3, "echo after", "cmd/s3.txt")]
r = execute_steps(d / "run.yaml", d, todo, timeout=None, skip_done=True, stop_on_error=True)
assert not r["aborted"] and (d / "cmd/s3.txt").exists(), r          # 止まらず続きが走る
assert r["tool_missing"] == [("T", 2, "sqlmap", "sudo apt install -y sqlmap")], r["tool_missing"]
assert "exit_code: 127" in (d / "cmd/s2.txt").read_text()          # 未成功として記録（導入後に再実行される）
TOOL
# 前提となるエビデンス（別の WSTG・アクティビティの成果物）を手順から導き、WSTG ページに取得状況と取得元へのリンクを出す
"${PY[@]}" - "${TMP}" <<'PREQ' || ng "前提となるエビデンスの導出か WSTG ページの表示が想定と違う"
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, prerequisites
P = prerequisites(load_yaml(COVERAGE_YAML)["activities"], load_yaml(CRITERIA_YAML))
got = {(w, e["file"], e["producers"][0][:3]) for w, l in P.items() for e in l}
for need in [("WSTG-INFO-08", "whatweb.json", ("fingerprint-stack", "WSTG-INFO-02", 2)),
             ("WSTG-CONF-01", "nmap-allports.txt", ("enum-apps", "WSTG-INFO-04", 5)),
             ("WSTG-CONF-01", "ports-http.txt", ("enum-apps", "WSTG-INFO-04", 1)),
             ("WSTG-CONF-11", "site.har", ("fingerprint-stack", "WSTG-INFO-08", 4))]:
    assert need in got, (need, sorted(got))
assert "WSTG-INFO-02" not in P   # 自分の手順が作るもの・人が置く入力は前提に入れない
import web_pages as W
root = Path(sys.argv[1]) / "preq-empty"; root.mkdir(exist_ok=True)
h = W.page_wstg_detail(W.Site(root), "WSTG-CONF-01")
assert "前提となるエビデンス" in h and "nmap-allports.txt" in h and "/tasks#act-enum-apps" in h, h[:300]
# ファイルの前提が無い WSTG も節を出し、「なし」とアクティビティ単位の前提（depends_on）を示す
h = W.page_wstg_detail(W.Site(root), "WSTG-ATHN-01")
assert "ファイルの前提なし" in h and "/tasks#act-burp-crawl-authn" in h and "未着手" in h, h[:300]
PREQ
# 人の作業で置く入力を読む手順（入力ガード `|| exit 75`）は手動→コマンドとして一括では走らない
"${PY[@]}" - <<'MRUN' || ng "入力ガードを持つ手順が一括実行の対象に入っている（手動→コマンドにする）"
import sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
from run_activity import select_steps
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
bad, n = [], 0
for a in cov["activities"]:
    steps = iter_steps(a, cr, "t.test", "X")
    n += sum(1 for s in steps if s.get("manual_run"))
    bad += [(a["id"], s["wid"], s["idx"]) for s in select_steps(steps, None)
            if any("exit 75" in r["cmd"] for r in s["runs"])]
assert not bad and n >= 7, (bad, n)
MRUN
# 「取得できたかの確認」はその手順が書いたファイルだけを見る（読むだけの入力の中身を出しても確認にならない）
"${PY[@]}" - <<'OUTP' || ng "確認コマンドが読むだけの入力ファイルを対象にしている（書き込み先だけにする）"
import sys; sys.path.insert(0, "scripts")
from new_activity import output_paths
c = ("test -s A/artifacts/in.txt || exit 75; grep x A/artifacts/in.txt 2>/dev/null | sort -u | tee A/artifacts/out.txt; "
     "curl -b A/artifacts/ck.txt -sD A/artifacts/h.txt -o A/artifacts/b.html u; whatweb --log-json=A/artifacts/w.json u; "
     "cmd | tee -a A/artifacts/log.tsv; mv x.xml x.json A/artifacts/")
got = [p.split("/")[-1] for p in output_paths(c, "A")]
assert got == ["out.txt", "h.txt", "b.html", "w.json", "log.tsv", "x.xml", "x.json"], got
OUTP
# 手順は「簡潔な説明: `コマンド`。読み方を1文」。record.html・カードの見出し（コマンドを抜いた説明）が
# 長すぎないこと（上限 300 字。目安 150 字。解説は note へ）と、OUTDIR を使うコマンドが実行コマンドとして
# 拾われていること（先頭語が CLI_BINARIES に無いと「手動」扱いになり、コマンド行が説明に丸ごと出る）
"${PY[@]}" - <<'DESC' || ng "手順の説明が長すぎる（300字超。解説は note へ）、OUTDIR を使うコマンドが実行コマンドとして拾われていない、またはコマンド手順にブラウザ作業が混ざる"
import re, sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
steps = {(s["wid"], s["idx"]): s for a in cov["activities"] for s in iter_steps(a, cr, "t.test", "X")}
long_ = sorted((k, len(s["desc"])) for k, s in steps.items() if len(s["desc"]) > 300)
raw = sorted(k for k, s in steps.items() if re.search(r"`[^`]*X/artifacts/[^`]*`", s["desc"]))
assert not long_ and not raw, {"300字超": long_, "コマンドが説明に残る": raw}
# ブラウザ・Burp の作業はコマンド手順に混ぜず、前の独立した手動手順に具体的に書く
mixed = sorted(k for k, s in steps.items() if s["kind"] == "cmd"
               and re.search(r"ブラウザ|Burp|DevTools|開発者ツール|Wappalyzer|ZAP", s["desc"]))
assert not mixed, {"コマンド手順にブラウザ作業が混ざる（手動手順に分ける）": mixed}
DESC
# NVD 照合（cpes/2.0 の keywordSearch・cves/2.0 の virtualMatchString）を例示の固定値
# （apache http server 2.4.49 等）で自動実行しない。前の手順で検出した製品・CPE を変数で渡す
"${PY[@]}" - <<'NVD' || ng "NVD 照合のコマンドが例示の固定値で引いている（検出結果を変数で渡す）"
import re, sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
bad = sorted({(s["wid"], s["idx"]) for a in cov["activities"]
              for s in iter_steps(a, cr, "t.test", "X") if s["kind"] == "cmd"
              for r in s["runs"] if re.search(r"(keywordSearch|virtualMatchString|cpeName)=[^$]", r["cmd"])})
assert not bad, bad
NVD
# 人が artifacts/ に置く入力（それより前のコマンドが書かないファイル）を読むコマンドは、
# `test -s OUTDIR/<入力> || exit 75` で「入力待ち」を返すこと（無いまま走ると一括が止まるか、
# 空の入力で成功扱いになって入力を置いた後もスキップされる）。入力待ちのコマンドが参照する
# ファイルを読む後続は run_activity が連鎖で入力待ちにするので、ガードは要らない
"${PY[@]}" - <<'INPUT' || ng "人が置く入力を読むコマンドに入力待ちガード（|| exit 75）が無い"
import re, sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
W = (r"(?:>>?|\btee(?:\s+-a)?|-o|-sD|-D|-oN|-oA|-oX|-oG|-c|-w|-O|--output|--outputpath|--logfile"
     r"|--json_out|--log-json=|--dump-header)\s*['\"]?X/artifacts/([A-Za-z0-9_-][A-Za-z0-9._-]*)")
bad = []
for a in cov["activities"]:
    known = set()
    for s in iter_steps(a, cr, "t.test", "X"):
        if s["kind"] != "cmd":
            continue
        for r in s["runs"]:
            c = r["cmd"]
            refs = set(re.findall(r"X/artifacts/([A-Za-z0-9_-][A-Za-z0-9._-]*)", c))
            outs = set(re.findall(W, c))
            for names in re.findall(r"\b(?:mv|cp)\s+([^;&|]*?)\s+X/artifacts/(?:\s|$)", c):
                outs |= {n for n in names.split() if not n.startswith("-")}  # `mv a b OUTDIR/` の形
            known |= outs
            if refs - outs - known and "exit 75" not in c:
                bad.append((a["id"], s["wid"], s["idx"], sorted(refs - known)))
            known |= refs
assert not bad, bad
INPUT
# 一括では secondary の手順を primary 側に任せ、同じ重いコマンド（nikto 等）を1回しか走らせない
"${PY[@]}" - <<'DUP' || ng "run_target が同じ WSTG-ID のコマンドを複数アクティビティで重複実行する"
import re, sys; sys.path.insert(0, "scripts")
from new_activity import COVERAGE_YAML, CRITERIA_YAML, load_yaml, iter_steps
from run_activity import select_steps
from run_target import primary_owners, split_delegated
cov, cr = load_yaml(COVERAGE_YAML), load_yaml(CRITERIA_YAML)
acts = [a for a in cov["activities"] if a.get("target_kind") != "domain"]
own = primary_owners(acts)
nikto = [a["id"] for a in acts
         for s in split_delegated(select_steps(iter_steps(a, cr, "t.test", "X"), None), own)[0]
         for r in s["runs"] if r["cmd"].startswith("nikto")]
assert nikto == ["server-config-review"], nikto
# 一括で実際に走る main コマンド（secondary の委譲後）を activity ごとに集める
def batch_mains():
    for a in acts:
        for s in split_delegated(select_steps(iter_steps(a, cr, "t.test", "X"), None), own)[0]:
            for r in s["runs"]:
                if r["role"] == "main":
                    yield a["id"], r["cmd"]
mains = list(batch_mains())
# 重い/冗長なコマンドは一括で1回だけ:
# ポート確認（ports-http.txt を作る curl ループ）は enum-apps、whatweb は fingerprint-stack、
# 全JSクロール（app-js.txt を作る curl ループ）は metafiles-crawl でだけ走る
full = [aid for aid, c in mains if "tee X/artifacts/ports-http.txt" in c]
assert full == ["enum-apps"], full
ww = [aid for aid, c in mains if re.search(r"(^|; )whatweb ", c)]
assert ww == ["fingerprint-stack"], ww
jscrawl = [aid for aid, c in mains if "app-js.txt" in c and "curl" in c]
assert jscrawl == ["metafiles-crawl"], jscrawl
# 単体 run_activity でも同じ委譲をする（owners は coverage.yaml 全体）。secondary で
# primary が別にある WSTG-ID のコマンドは、フォルダ単体で回しても走らせない（ffuf 二重実行を防ぐ）。
gown = primary_owners(cov["activities"])
def solo_mains(aid):
    a = next(x for x in cov["activities"] if x["id"] == aid)
    kept, _ = split_delegated(select_steps(iter_steps(a, cr, "t.test", "X"), None), gown)
    return [r["cmd"] for s in kept for r in s["runs"] if r["role"] == "main"]
mf = solo_mains("metafiles-crawl")
assert not any("ffuf -w" in c for c in mf), "単体 run_activity が secondary（CONF-05）の ffuf を実行する"
assert any("app-js.txt" in c for c in mf), "委譲で metafiles-crawl の primary 手順まで落ちている"
DUP
ok "run_target: 一括作成（既存スキップ・--reuse-latest）・成功分の再開スキップ・エラーで停止・secondary の重複実行なし"

echo "[5/8] export_checklist.py（集約規則）"
"${PY[@]}" - <<PYEOF
import pathlib, re
p = pathlib.Path("${DIR}/run.yaml"); s = p.read_text()
s = s.replace("verdict: todo", "verdict: fail", 1)
s = re.sub(r"verdict: todo", "verdict: pass", s, count=1)
p.write_text(s)
PYEOF
"${PY[@]}" scripts/export_checklist.py --root "${TMP}/ev" --out "${TMP}/out.csv" >/dev/null
"${PY[@]}" - <<PYEOF || ng "集約結果がおかしい"
import csv, sys
rows = list(csv.DictReader(open("${TMP}/out.csv", encoding="utf-8-sig")))
assert len(rows) >= 90, len(rows)
assert [r for r in rows if r["status"] == "fail"], "fail が集計されない"
assert [r for r in rows if r["status"] == "pass"], "pass が集計されない"
assert [r for r in rows if r["status"] == "todo"], "未実施が todo で初期化されない"
cols = list(rows[0])
expected = ["wstg_id","category","title","status","activities","evidence_paths","finding_summary","updated"]
assert cols == expected, f"列の契約が変わっている: {cols}"
PYEOF
ok "todo 初期化・fail/pass 集約・列の並び"

echo "[6/8] gen_playbooks.py（一時ディレクトリへ）"
if compgen -G "docs/owasp/*" > /dev/null; then
  "${PY[@]}" scripts/gen_playbooks.py --out-dir "${TMP}/pb" >/dev/null
  n=$(ls "${TMP}/pb"/WSTG-*.md | wc -l)
  [ "${n}" -ge 90 ] || ng "カードが ${n} 枚しか生成されない"
  grep -q "判定基準" "${TMP}/pb/WSTG-SESS-02.md" || ng "カードの体裁が壊れている"
  ok "カード ${n} 枚"
  # 使用ツールは手順から導出する（手順に出たツールが載る／原文由来の雑多語は出さない）
  awk '/## 使用ツール/{f=1;next} /^## /{f=0} f&&/theHarvester/{ok=1} END{exit !ok}' \
    "${TMP}/pb/WSTG-INFO-01.md" || ng "使用ツールが手順から導出されていない（theHarvester 欠落）"
  grep -Eq '^- (Watch|Star|Eyeballs)$' "${TMP}/pb"/WSTG-*.md \
    && ng "原文由来の雑多な語が使用ツールに混入している" || true
  ok "使用ツールは手順から導出（原文由来の雑多語なし）"
  diff -rq playbooks "${TMP}/pb" >/dev/null && ok "コミット済みカードは最新" \
    || echo "  warn playbooks/ が古い: uv run scripts/gen_playbooks.py"
else
  echo "  skip WSTG 原文なし"
fi

echo "[7/8] tasks.py（タスクリストと進捗）"
"${PY[@]}" scripts/tasks.py --check >/dev/null && ok "TASKS.md は最新" \
  || ng "TASKS.md が古い: uv run scripts/tasks.py --write"
# フェーズ単位の Kali ツール準備（apt 一括）が出ているか
grep -q "^\*\*準備（このフェーズで使う Kali ツール" TASKS.md \
  && grep -Eq "apt install -y .*whois" TASKS.md \
  || ng "フェーズ単位の Kali ツール準備が TASKS.md に出ていない"
ok "フェーズ単位の Kali ツール準備（apt 一括）"
# npm 系は Kali に npm が無いので、apt での導入まで案内に含める
grep -qF "sudo apt install -y npm && sudo npm install -g retire" TASKS.md \
  || ng "npm 系ツールの案内に npm の導入が含まれていない（sudo: npm: command not found になる）"
ok "npm 系ツールは apt 前提込みで案内"
# Burp Suite 本体は apt（burpsuite）でセットアップに含める（機能・拡張は Burp 内なので個別導入不要）
grep -Eq "apt install -y .*\bburpsuite\b" TASKS.md \
  || ng "Burp Suite（burpsuite）が apt セットアップに含まれていない"
ok "Burp Suite は apt（burpsuite）でセットアップに含まれる"
"${PY[@]}" scripts/tasks.py --root "${TMP}/ev" > "${TMP}/progress.txt" || ng "進捗表示が落ちる"
grep -q "次にやること" "${TMP}/progress.txt" || ng "次にやることが出ない"
grep -q "実施中\|完了" "${TMP}/progress.txt" || ng "進捗が反映されない"
ok "進捗表示（evidence 走査）"

echo "[8/8] 機密境界"
git -C "${REPO_ROOT}" ls-files evidence | grep -qv '^evidence/.gitkeep$' && ng "evidence/ が追跡されている" || true
git -C "${REPO_ROOT}" ls-files docs | grep -qv '^docs/owasp/FETCH.md$' && ng "docs/owasp/ が追跡されている" || true
ok "evidence/ と docs/owasp/ は未追跡（.gitkeep と FETCH.md のみ）"

echo "すべて通過しました。"
