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

# fingerprint-stack: NVD 照合が curl/jq、受動観測が curl、確認コマンドは重複しないこと
"${PY[@]}" scripts/new_activity.py fingerprint-stack --target ex.test --root "${TMP}/ev" --date 20260101 >/dev/null
FDIR="${TMP}/ev/fingerprint-stack-ex.test-20260101"
FEJS="${FDIR}/evidence.js"
"${PY[@]}" - "${FEJS}" "${FDIR}" <<'DEDUP'
import json, sys
d = json.loads(open(sys.argv[1], encoding="utf-8").read().split("window.WSTG_EVIDENCE = ", 1)[1].rstrip(";\n"))
fdir = sys.argv[2]
cmds = [r["cmd"] for it in d["items"] for st in it["steps"] for r in st["runs"] if r.get("cmd")]
need = f"head -c 400 {fdir}/artifacts/nvd-cve.json"
assert sum(1 for c in cmds if need in c) == 1, "確認コマンドが重複している"
assert any("curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0" in c for c in cmds), "CVE 照合が curl になっていない"
assert any(c.startswith("jq -r '.totalResults'") for c in cmds), "jq が実行コマンドになっていない"
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
"${PY[@]}" scripts/tasks.py --root "${TMP}/ev" > "${TMP}/progress.txt" || ng "進捗表示が落ちる"
grep -q "次にやること" "${TMP}/progress.txt" || ng "次にやることが出ない"
grep -q "実施中\|完了" "${TMP}/progress.txt" || ng "進捗が反映されない"
ok "進捗表示（evidence 走査）"

echo "[8/8] 機密境界"
git -C "${REPO_ROOT}" ls-files evidence | grep -qv '^evidence/.gitkeep$' && ng "evidence/ が追跡されている" || true
git -C "${REPO_ROOT}" ls-files docs | grep -qv '^docs/owasp/FETCH.md$' && ng "docs/owasp/ が追跡されている" || true
ok "evidence/ と docs/owasp/ は未追跡（.gitkeep と FETCH.md のみ）"

echo "すべて通過しました。"
