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

# --target 命名 + 実施記録(record.md) 生成 + capture.py 取り込み
"${PY[@]}" scripts/new_activity.py recon-osint --target ex.test --root "${TMP}/ev" --date 20260101 >/dev/null
TDIR="${TMP}/ev/recon-osint-ex.test-20260101"
REC="${TDIR}/record.md"
[ -f "${REC}" ] || ng "--target のフォルダ/実施記録(record.md)が作られない"
grep -q "^\$ whois ex.test" "${REC}" && grep -q "\[コマンド\]" "${REC}" && grep -q "\[手動/ブラウザ\]" "${REC}" \
  || ng "record.md が Q&A 形式（コマンド/手動 + $ 行）で target 置換されていない"
# ツールの出力先はエビデンスフォルダの artifacts/ に置換されること（OUTDIR を残さない）
grep -q "OUTDIR" "${REC}" && ng "record.md に OUTDIR プレースホルダが残っている" || true
grep -qF -- "mv theharvester.xml theharvester.json ${TDIR}/artifacts/" "${REC}" \
  || ng "theHarvester の出力を artifacts/ へ移す手順になっていない"
grep -qF -- "-o ${TDIR}/artifacts/amass-passive.txt" "${REC}" \
  || ng "複数コマンドの出力先が artifacts/ に置換されていない（amass）"
# record.md 単体で判定できるよう、目的と pass/fail 基準が各セクションに埋まっていること
grep -q "^- 目的: " "${REC}" && grep -q "^- 判定基準 pass = " "${REC}" \
  || ng "record.md に判定基準（目的・pass/fail）が埋め込まれていない"
# Markdown の見出しは「表題・WSTG-ID・手順/判定」だけ（注釈が見出しとして強調されない）
grep -E "^#" "${REC}" | grep -vE "^(# 実施記録 |## WSTG-|### )" \
  && ng "record.md の注釈が見出し（#）になっている" || true
# 実施者の記入を模擬（結果を貼り、verdict/finding を記入）して capture
"${PY[@]}" - "${REC}" <<'PYEOF'
import sys
p=sys.argv[1]; t=open(p).read()
t=t.replace("$ whois ex.test\n```\n\n結果:\n```\n```",
            "$ whois ex.test\n```\n\n結果:\n```\nDomain Name: EX.TEST\n```",1)
t=t.replace("@verdict todo\n\n@finding \n","@verdict info\n\n@finding whois 確認済み。\n",1)
open(p,"w").write(t)
PYEOF
"${PY[@]}" scripts/capture.py "${TDIR}" >/dev/null
grep -q "Domain Name: EX.TEST" "${REC}" || ng "record.md に貼った raw 結果が保持されない"
"${PY[@]}" -c "
import yaml
d=yaml.safe_load(open('${TDIR}/run.yaml'))
assert d['target_scope']=='ex.test', d['target_scope']
c={x['id']:x for x in d['covers']}
assert c['WSTG-INFO-01']['verdict']=='info', c['WSTG-INFO-01']
assert c['WSTG-INFO-01']['finding'], 'finding 未転記'
assert c['WSTG-INFO-01']['evidence']=='record.md', c['WSTG-INFO-01']
assert c['WSTG-CONF-10']['verdict']=='todo', '未記入は据え置き'
" || ng "capture が run.yaml の covers を正しく更新しない"
ok "record.md(Q&A) 生成 + capture 取り込み（--target 命名・covers 更新・raw 保持）"

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
"${PY[@]}" scripts/tasks.py --root "${TMP}/ev" > "${TMP}/progress.txt" || ng "進捗表示が落ちる"
grep -q "次にやること" "${TMP}/progress.txt" || ng "次にやることが出ない"
grep -q "実施中\|完了" "${TMP}/progress.txt" || ng "進捗が反映されない"
ok "進捗表示（evidence 走査）"

echo "[8/8] 機密境界"
git -C "${REPO_ROOT}" ls-files evidence | grep -qv '^evidence/.gitkeep$' && ng "evidence/ が追跡されている" || true
git -C "${REPO_ROOT}" ls-files docs | grep -qv '^docs/owasp/FETCH.md$' && ng "docs/owasp/ が追跡されている" || true
ok "evidence/ と docs/owasp/ は未追跡（.gitkeep と FETCH.md のみ）"

echo "すべて通過しました。"
