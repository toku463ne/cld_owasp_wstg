# WSTG-INPV-05 — Testing for SQL Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が SQL 文の構造に影響しないかを確認する。

WSTG の Test Objectives:

- Identify SQL injection points.
- Assess the severity of the injection and the level of access that can be achieved through it.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Detection Techniques** — The first step in this test is to understand when the application interacts with a DB Server in order to access some data
2. **Standard SQL Injection Testing**
3. **Classic SQL Injection** — Consider the following SQL query:
4. **SELECT Statement** — Consider the following SQL query:
5. **Stacked Queries** — Depending on the API which the web application is using and the DBMS (e.g
6. **Fingerprinting the Database** — Even though the SQL language is a standard, every DBMS has its peculiarity and differs from each other in many aspects like special commands …
7. **Errors Returned by the Application** — The first way to find out what back end database is used is by observing the error returned by the application

## 使用ツール

- SQL Injection Fuzz Strings (from wfuzz tool) - Fuzzdb
- sqlbftools
- Bernardo Damele A. G.: sqlmap, automatic SQL injection tool
- Muhaimin Dzulfakar: MySqloit, MySql Injection takeover tool

## 判定基準（pass / fail の見分け）

- **pass**: 入力を変えてもエラー・応答時間・件数に構造的な変化がなく、プレースホルダ利用が確認できる。
- **fail**: エラーベース・ブーリアン・時間差のいずれかで SQL の挙動を制御できる。
- 補足: sqlmap は許可範囲と負荷に注意。--risk/--level を上げる前に合意を取る。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection
