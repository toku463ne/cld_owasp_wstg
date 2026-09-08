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

1. The XPath attack pattern was first published by Amit Klein and is very similar to the usual SQL Injection.
2. `<?xml version="1.0" encoding="ISO-8859-1"?> <users> <user> <username>gandalf</username> <password>!c3</password> <account>admin</account> </user> <user> <username>Stefan0</username> <passwo …
3. An XPath query that returns the account whose username is gandalf and the password is !c3 would be the following:
4. string(//user[username/text()='gandalf' and password/text()='!c3']/account/text())
5. If the application does not properly filter user input, the tester will be able to inject XPath code and interfere with the query result.
6. `Username: ' or '1' = '1 Password: ' or '1' = '1
7. Looks quite familiar, doesn't it? Using these parameters, the query becomes:

## 使用ツール

- Burp Intruder
- sqlmap
- tplmap
- 手動 payload

## 判定基準（pass / fail の見分け）

- **pass**: 特殊文字がエスケープされ、クエリ構造が変わらない。
- **fail**: ' or '1'='1 相当で認証迂回や全ノード取得ができる。
- 補足: XML をユーザ DB に使っている環境で発生する。SQLi と同じ考え方で試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/09-Testing_for_XPath_Injection
