# WSTG-INPV-06 — Testing for LDAP Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が LDAP フィルタの構造に影響しないかを確認する。

WSTG の Test Objectives:

- Identify LDAP injection points.
- Assess the severity of the injection.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Let's suppose we have a web application using a search filter like the following one:
2. searchfilter="(cn="+user+")"
3. which is instantiated by an HTTP request like this:
4. http://www.example.com/ldapsearch?user=John
5. If the value John is replaced with a *, by sending the request:
6. http://www.example.com/ldapsearch?user=*
7. the filter will look like:

## 使用ツール

- Softerra LDAP Browser

## 判定基準（pass / fail の見分け）

- **pass**: 特殊文字（* ( ) \ NUL）がエスケープされ、フィルタが壊れない。
- **fail**: * や )(uid=* 等で認証迂回・全件取得ができる。
- 補足: 認証画面と検索画面の両方が入口になり得る。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/06-Testing_for_LDAP_Injection
