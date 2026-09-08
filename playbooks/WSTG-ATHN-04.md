# WSTG-ATHN-04 — Testing for Bypassing Authentication Schema

## 目的

認証を経ずに保護対象へ到達できる経路がないかを確認する。

WSTG の Test Objectives:

- Ensure that authentication is applied across all services that require it.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing** — There are several methods of bypassing the authentication schema that is used by a web application:
2. **Direct Page Request** — If a web application implements access control only on the log in page, the authentication schema could be bypassed
3. **Parameter Modification** — Another problem related to authentication design is when the application verifies a successful log in on the basis of a fixed value paramete …
4. **Session ID Prediction** — Many web applications manage authentication by using session identifiers (session IDs)
5. **SQL Injection (HTML Form Authentication)** — SQL Injection is a widely known attack technique
6. **Gray-Box Testing** — If an attacker has been able to retrieve the application source code by exploiting a previously discovered vulnerability (e.g., directory tr …

## 使用ツール

- WebGoat
- OWASP Zed Attack Proxy (ZAP)

## 判定基準（pass / fail の見分け）

- **pass**: 保護対象 URL に未認証で直接アクセスするとすべて弾かれる。
- **fail**: 直リンク・パラメータ改変（isAdmin=true 等）・SQL インジェクション・セッション改変で認証を迂回できる。
- 補足: 「リダイレクトされるが本文も返ってきている」パターンを見落とさない。本文の中身を確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/04-Testing_for_Bypassing_Authentication_Schema
