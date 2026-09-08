# WSTG-SESS-05 — Testing for Cross Site Request Forgery

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

状態変更操作が CSRF 対策で守られているかを確認する。

WSTG の Test Objectives:

- Determine whether it is possible to initiate requests on a user's behalf that are not initiated by the user.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Audit the application to ascertain if its session management is vulnerable. If session management relies only on client-side values (information available to the browser), then the applicati …
2. Resources accessible via HTTP GET requests are easily vulnerable, though POST requests can be automated via JavaScript and are vulnerable as well; therefore, the use of POST alone is not eno …
3. In case of POST, the following sample can be used.
4. Create an HTML page similar to that shown below
5. Host the HTML on a malicious or third-party site
6. Send the link for the page to the victim(s) and induce them to click it.
7. `<html> <body onload='document.CSRF.submit()'> <form action='http://targetWebsite/Authenticate.jsp' method='POST' name='CSRF'> <input type='hidden' name='name' value='Hacked'> <input type='h …

## 使用ツール

- OWASP ZAP
- CSRF Tester
- Pinata-csrf-tool

## 判定基準（pass / fail の見分け）

- **pass**: 状態変更に単回性のトークンが必要、または SameSite と Origin/Referer 検証で守られている。
- **fail**: トークンなし・検証なし・トークンを削除しても成功する・ユーザ間で使い回せる。
- 補足: PoC の HTML を artifacts に置くと再現手順として最も分かりやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`
- `covers:` — `{id: WSTG-SESS-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/05-Testing_for_Cross_Site_Request_Forgery
