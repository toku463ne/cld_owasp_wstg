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
grep -qF -- "-o ${TDIR}/artifacts/subfinder.txt" "${REC}" \
  || ng "複数コマンドの出力先が artifacts/ に置換されていない（subfinder）"
# 出力をファイルに落とすコマンドは、取れているかの確認コマンドまで並ぶこと
grep -qF -- "head -c 400 ${TDIR}/artifacts/crtsh.json" "${REC}" \
  || ng "ファイル出力コマンドに確認コマンド（サイズ・先頭）が付いていない"
grep -qF -- "wc -l ${TDIR}/artifacts/subfinder.txt" "${REC}" \
  || ng "テキスト出力コマンドに行数確認が付いていない"
grep -qF -- "artifacts/ex.test" "${REC}" && ng "target 名を出力ファイルと誤認している" || true
# for/while ループも $ 実行コマンドとして拾い、tee の出力先の確認まで並ぶこと（CONF-10）
grep -qF -- "\$ while read -r h; do echo" "${REC}" \
  || ng "for/while ループが $ 実行コマンドとして拾われていない"
grep -qF -- "wc -l ${TDIR}/artifacts/cname-check.txt" "${REC}" \
  || ng "ループの tee 出力先に確認コマンドが付いていない"
# target を含まず OUTDIR に書く後処理コマンド（grep 等）も $ 実行として拾うこと（CONF-10 #2）
grep -qF -- "\$ grep -iaE" "${REC}" \
  || ng "OUTDIR に書く grep 後処理コマンドが $ 実行として拾われていない"
grep -qF -- "tee ${TDIR}/artifacts/takeover-candidates.md" "${REC}" \
  || ng "grep の tee 出力先が artifacts/ に置換されていない"
# 各手順に「結果に何を貼るか」の指示があること（手動/ブラウザを含む）
[ "$(grep -c "^> 貼るもの: " "${REC}")" -ge 5 ] \
  || ng "各手順に「貼るもの:」の指示が入っていない"
grep -q "^> 貼るもの: ① 操作した URL" "${REC}" \
  || ng "[手動/ブラウザ] の手順に貼るものの指示が無い"

# record.md 単体で判定できるよう、目的と pass/fail 基準が各セクションに埋まっていること
grep -q "^- 目的: " "${REC}" && grep -q "^- 判定基準 pass = " "${REC}" \
  || ng "record.md に判定基準（目的・pass/fail）が埋め込まれていない"
# Markdown の見出しは「表題・WSTG-ID・手順/判定」だけ（注釈が見出しとして強調されない）
grep -E "^#" "${REC}" | grep -vE "^(# 実施記録 |## WSTG-|### )" \
  && ng "record.md の注釈が見出し（#）になっている" || true
# 判定の書き方は role 別（secondary に pass を勧めない・primary には info/na も案内する）
awk '/^## WSTG-INFO-01 /{f=1} /^## WSTG-CONF-10 /{f=0} f&&/^上の pass\/fail 基準で判定する。/{ok=1} END{exit !ok}' \
  "${REC}" || ng "primary の判定コメントに pass/info/na の案内が無い"
awk '/^## WSTG-CONF-10 /{f=1} f&&/secondary（入力・補強）/{ok=1} END{exit !ok}' "${REC}" \
  || ng "secondary の cover に role 別の判定コメントが出ていない"
awk '/^## WSTG-CONF-10 /{f=1} f&&/^上の pass\/fail 基準で判定する。/{bad=1} END{exit bad}' "${REC}" \
  || ng "secondary に「無所見なら pass」系の案内が出ている（primary 未実施でも CSV が pass になる）"
grep -q "^- 役割: secondary" "${REC}" || ng "secondary の cover に役割の注記が無い"
ok "判定コメントが role 別（secondary で pass を勧めない）"

# 結果だけ貼って判定未記入なら、run.yaml は変わらず「未記入」と案内されること
"${PY[@]}" - "${REC}" <<'PENDEOF'
import sys
p=sys.argv[1]; t=open(p).read()
t=t.replace("結果:\n```\n```", "結果:\n```\n(pending)\n```", 1)
open(p,"w").write(t)
PENDEOF
"${PY[@]}" scripts/capture.py "${TDIR}" > "${TMP}/capture1.txt"
grep -q "判定未記入" "${TMP}/capture1.txt" || ng "判定未記入が「更新しました」に紛れている"
grep -q "更新しました" "${TMP}/capture1.txt" && ng "判定を転記していないのに更新件数を報告している" || true
grep -q "export_checklist" "${TMP}/capture1.txt" && ng "未記入のまま CSV 出力を勧めている" || true
"${PY[@]}" -c "
import yaml
c={x['id']:x for x in yaml.safe_load(open('${TDIR}/run.yaml'))['covers']}
assert c['WSTG-INFO-01']['verdict']=='todo', '未記入なのに verdict が動いた'
assert c['WSTG-INFO-01']['evidence']=='record.md', 'evidence の記録だけは入る'
" || ng "結果のみの取り込みで covers が想定外に変わる"
ok "capture: 結果のみ（判定未記入）は判定を動かさず、次の一手を案内"

# 実施者の記入を模擬（結果を貼り、verdict/finding を記入）して capture
"${PY[@]}" - "${REC}" <<'PYEOF'
import sys
p=sys.argv[1]; t=open(p).read()
t=t.replace("結果:\n```\n```", "結果:\n```\nDomain Name: EX.TEST\n```", 1)   # 手順1(whois)
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
