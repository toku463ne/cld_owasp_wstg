# WSTG-INPV-17 — Testing for Host Header Injection

## 目的

Host ヘッダの値を信用した処理がないかを確認する。

WSTG の Test Objectives:

- Assess if the Host header is being parsed dynamically in the application.
- Bypass security controls that rely on the header.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **X-Forwarded Host Header Bypass** — In the event that Host header injection is mitigated by checking for invalid input injected via the Host header, you can supply the value to …
2. **Web Cache Poisoning** — Using this technique, an attacker can manipulate a web-cache to serve poisoned content to anyone who requests it
3. **Password Reset Poisoning** — It is common for password reset functionality to include the Host header value when creating password reset links that use a generated secre …

## 使用ツール

- Burp Suite
- Burp HTTP Request Smuggler
- curl

## 判定基準（pass / fail の見分け）

- **pass**: Host を偽装しても、リンク生成・リセットメール・キャッシュキーに反映されない（許可ホストのみ）。
- **fail**: 偽装した Host がリセットリンクや絶対 URL に反映される、キャッシュポイズニングにつながる。
- 補足: X-Forwarded-Host など類似ヘッダも試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- `covers:` — `{id: WSTG-INPV-17, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-request-tamper` — HTTP リクエスト改変系の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/17-Testing_for_Host_Header_Injection
