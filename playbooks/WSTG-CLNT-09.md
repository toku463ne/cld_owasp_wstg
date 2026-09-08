# WSTG-CLNT-09 — Testing for Clickjacking

## 目的

画面を iframe に埋め込ませ、クリックを誘導できないかを確認する。

WSTG の Test Objectives:

- Understand security measures in place.
- Assess how strict the security measures are and if they are bypassable.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Bypass Clickjacking Protection** — If the http://www.target.site page does not appear in the inline frame, the site probably has some form of protection against clickjacking
2. **Client-side Protection: Frame Busting** — The most common client-side method, that has been developed to protect a web page from clickjacking, is called Frame Busting and it consists …
3. **Server-side Protection: X-Frame-Options** — An alternative approach to client-side frame busting code was implemented by Microsoft and it consists of an header based defense
4. **Create a Proof of Concept** — Once we have discovered that the site we are testing is vulnerable to clickjacking attack, we can proceed with the development of a proof of …

## 使用ツール

- curl
- Burp Suite
- securityheaders.io 相当の手動チェック

## 判定基準（pass / fail の見分け）

- **pass**: 機微画面に X-Frame-Options: DENY/SAMEORIGIN か CSP frame-ancestors がある。
- **fail**: 任意サイトから iframe 埋め込みでき、操作を誘導できる（PoC の HTML で確認）。
- 補足: 対象は「状態を変える操作がある画面」。静的ページのみなら影響は限定的。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`
- `covers:` — `{id: WSTG-CLNT-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/09-Testing_for_Clickjacking
