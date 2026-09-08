# WSTG-ATHN-05 — Testing for Vulnerable Remember Password

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ログイン保持機能が資格情報を危険な形で保存・送信していないかを確認する。

WSTG の Test Objectives:

- Validate that the generated session is managed securely and do not put the user's credentials in danger.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. As these methods provide a better user experience and allow the user to forget all about their credentials, they increase the attack surface area. Some applications:
2. Store the credentials in an encoded fashion in the browser's storage mechanisms, which can be verified by following the web storage testing scenario and going through the session analysis sc …
3. Automatically inject the user's credentials that can be abused by:
4. Tokens should be analyzed in terms of token-lifetime, where some tokens never expire and put the users in danger if those tokens ever get stolen.

## 使用ツール

- Burp Suite
- curl
- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: 保持用トークンがランダムで有効期限があり、失効操作で無効化される。
- **fail**: パスワードやその可逆な形が Cookie・localStorage に保存される、またはトークンが失効しない。
- 補足: ログアウト後・パスワード変更後にトークンが無効になるかを必ず試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/05-Testing_for_Vulnerable_Remember_Password
