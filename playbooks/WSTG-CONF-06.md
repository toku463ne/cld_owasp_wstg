# WSTG-CONF-06 — Test HTTP Methods

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

サーバが受け付ける HTTP メソッドを列挙し、危険なメソッドや迂回の余地がないかを確認する。

WSTG の Test Objectives:

- Enumerate supported HTTP methods.
- Test for access control bypass.
- Test XST vulnerabilities.
- Test HTTP method overriding techniques.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Discover the Supported Methods** — To perform this test, the tester needs some way to figure out which HTTP methods are supported by the web server that is being examined
2. **Testing the PUT Method** — Capture the base request of the target with a web proxy.
3. **Testing for Access Control Bypass** — Find a page to visit that has a security constraint such that a GET request would normally force a 302 redirect to a log in page or force a …
4. **Testing for Cross-Site Tracing Potential** — Note: in order to understand the logic and the goals of a cross-site tracing (XST) attack, one must be familiar with cross-site scripting at …
5. **Testing for HTTP Method Overriding** — Some web frameworks provide a way to override the actual HTTP method in the request by emulating the missing HTTP verbs passing some custom …

## 使用ツール

- Ncat
- cURL
- nmap http-methods NSE script
- w3af plugin htaccess_methods

## 判定基準（pass / fail の見分け）

- **pass**: 業務上必要なメソッド（GET/POST/HEAD 等）だけが有効で、未定義メソッドは 405 で拒否される。
- **fail**: PUT/DELETE/TRACE/CONNECT が有効、または任意メソッドや X-HTTP-Method-Override で認可を迂回できる。
- 補足: OPTIONS の応答は自己申告にすぎない。実際に各メソッドを投げて確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-options.txt`, `cmd/nmap-http-methods.txt`
- `covers:` — `{id: WSTG-CONF-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-methods` — HTTP メソッドの列挙と検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/06-Test_HTTP_Methods
