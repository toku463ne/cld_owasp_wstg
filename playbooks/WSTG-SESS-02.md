# WSTG-SESS-02 — Testing for Cookies Attributes

## 目的

セッション Cookie の属性が適切に設定されているかを確認する。

WSTG の Test Objectives:

- Ensure that the proper security configuration is set for cookies.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Cookie Attributes**
2. **Secure Attribute** — The Secure attribute tells the browser to only send the cookie if the request is being sent over a secure channel such as HTTPS
3. **HttpOnly Attribute** — The HttpOnly attribute is used to help prevent attacks such as session leakage, since it does not allow the cookie to be accessed via a clie …
4. **Domain Attribute** — The Domain attribute is used to compare the cookie's domain against the domain of the server for which the HTTP request is being made
5. **Path Attribute** — The Path attribute plays a major role in setting the scope of the cookies in conjunction with the domain
6. **Expires Attribute** — The Expires attribute is used to:
7. **SameSite Attribute** — The SameSite attribute is used to assert that a cookie ought not to be sent along with cross-site requests

## 使用ツール

- OWASP Zed Attack Proxy Project
- Web Proxy Burp Suite
- Tamper Data for FF Quantum
- "FireSheep" for FireFox
- "EditThisCookie" for Chrome
- "Cookiebro - Cookie Manager" for FireFox

## 判定基準（pass / fail の見分け）

- **pass**: Secure・HttpOnly が付き、SameSite が Lax 以上、Domain/Path が必要最小限。
- **fail**: Secure か HttpOnly が欠けている、SameSite=None なのに用途上不要、Domain が広すぎる。
- 補足: 認証済みで発行される Cookie を対象にする。トラッキング用 Cookie と混同しない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`, `artifacts/session-trace.burp`, `artifacts/token-samples.txt`
- `covers:` — `{id: WSTG-SESS-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）
- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/02-Testing_for_Cookies_Attributes
