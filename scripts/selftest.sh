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

# --target 命名 + ワークシート生成 + capture.py 取り込み
"${PY[@]}" scripts/new_activity.py recon-osint --target ex.test --root "${TMP}/ev" --date 20260101 >/dev/null
TDIR="${TMP}/ev/recon-osint-ex.test-20260101"
WS="${TDIR}/worksheet.md"
[ -f "${WS}" ] || ng "--target のフォルダ/ワークシートが作られない"
grep -q "whois ex.test" "${WS}" && grep -q "^@cmd whois | cmd/whois.txt" "${WS}" \
  || ng "ワークシートにコマンドが target 置換で埋まっていない"
# 実施者の貼付を模擬して capture
"${PY[@]}" - "${WS}" <<'PYEOF'
import sys
p=sys.argv[1]; t=open(p).read()
t=t.replace("@cmd whois | cmd/whois.txt\n$ whois ex.test\n```paste\n```",
            "@cmd whois | cmd/whois.txt\n$ whois ex.test\n```paste\nDomain Name: EX.TEST\n```")
t=t.replace("@verdict todo\n@finding \n","@verdict info\n@finding whois 確認済み。\n",1)
open(p,"w").write(t)
PYEOF
"${PY[@]}" scripts/capture.py "${TDIR}" >/dev/null
[ -s "${TDIR}/cmd/whois.txt" ] || ng "capture が cmd/ に出力を保存しない"
grep -q "Domain Name: EX.TEST" "${TDIR}/cmd/whois.txt" || ng "貼付内容が保存されない"
"${PY[@]}" -c "
import yaml
d=yaml.safe_load(open('${TDIR}/run.yaml'))
assert d['target_scope']=='ex.test', d['target_scope']
c={x['id']:x for x in d['covers']}
assert c['WSTG-INFO-01']['verdict']=='info', c['WSTG-INFO-01']
assert c['WSTG-INFO-01']['evidence']=='cmd/whois.txt', c['WSTG-INFO-01']
assert any(e.get('source')=='worksheet' for e in d['commands']), d['commands']
" || ng "capture が run.yaml（covers/commands）を正しく更新しない"
ok "worksheet 生成 + capture 取り込み（--target 命名・covers 更新）"

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
"${PY[@]}" scripts/tasks.py --root "${TMP}/ev" > "${TMP}/progress.txt" || ng "進捗表示が落ちる"
grep -q "次にやること" "${TMP}/progress.txt" || ng "次にやることが出ない"
grep -q "実施中\|完了" "${TMP}/progress.txt" || ng "進捗が反映されない"
ok "進捗表示（evidence 走査）"

echo "[8/8] 機密境界"
git -C "${REPO_ROOT}" ls-files evidence | grep -qv '^evidence/.gitkeep$' && ng "evidence/ が追跡されている" || true
git -C "${REPO_ROOT}" ls-files docs | grep -qv '^docs/owasp/FETCH.md$' && ng "docs/owasp/ が追跡されている" || true
ok "evidence/ と docs/owasp/ は未追跡（.gitkeep と FETCH.md のみ）"

echo "すべて通過しました。"
