# WSTG-INPV-09 — Testing for XPath Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が XPath クエリの構造に影響しないかを確認する。

WSTG の Test Objectives:

- Identify XPATH injection points.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. XPath クエリを伴う入力に `' or '1'='1` `x' or name()='` を Burp Repeater で入れ、認証迂回/全件取得を試す
2. 真偽差・エラーからブラインド XPath 注入が可能か確認
3. XML データストアを使うログイン等で、フィルタが壊れて迂回できないか確認
4. 成立経路（どの入力・どのクエリ）を finding に明記

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: 特殊文字がエスケープされ、クエリ構造が変わらない。
- **fail**: ' or '1'='1 相当で認証迂回や全ノード取得ができる。
- 補足: XML をユーザ DB に使っている環境で発生する。SQLi と同じ考え方で試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/09-Testing_for_XPath_Injection
