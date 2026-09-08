# WSTG-ATHN-01 — Testing for Credentials Transported over an Encrypted Channel

## 目的

資格情報が暗号化された経路でのみ送信されているかを確認する。

WSTG の Test Objectives:

- Assess whether any use case of the web site or application causes the server or the client to exchange credentials without encryption.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Login** — Find the address of the login page and attempt to switch the protocol to HTTP
2. **Account Creation** — To test for unencrypted account creation, attempt to force browse to the HTTP version of the account creation and create an account, for exa …
3. **Password Reset, Change Password or Other Account Manipulation** — Similar to login and account creation, if the web application has features that allow a user to change an account or call a different servic …
4. **Accessing Resources While Logged In** — After logging in, access all the features of the application, including public features that do not necessarily require a login to access

## 使用ツール

- Burp Suite
- curl
- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: ログイン画面と送信先の両方が HTTPS で、HTTP へのフォールバックがない。
- **fail**: 資格情報が HTTP で送信される、HTTPS 画面から HTTP へ POST している、または GET のクエリに載っている。
- 補足: リダイレクト前の最初のリクエストが平文になっていないかも確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/01-Testing_for_Credentials_Transported_over_an_Encrypted_Channel
