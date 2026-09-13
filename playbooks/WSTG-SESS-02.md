# WSTG-SESS-02 — Testing for Cookies Attributes

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

セッション Cookie の属性が適切に設定されているかを確認する。

WSTG の Test Objectives:

- Ensure that the proper security configuration is set for cookies.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `curl -sI` でログイン応答の `Set-Cookie` を取得し、属性を1つずつ確認
2. `Secure`（HTTPS 限定）・`HttpOnly`（JS 遮断）・`SameSite`（Lax/Strict）の有無を確認
3. `Domain`/`Path` が過度に広くないか、`__Host-`/`__Secure-` prefix の適否を確認
4. セッション Cookie と CSRF/その他 Cookie で属性が適切に分かれているか確認

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
