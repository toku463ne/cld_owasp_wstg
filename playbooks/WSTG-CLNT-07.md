# WSTG-CLNT-07 — Testing Cross Origin Resource Sharing

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

CORS 設定が過剰に緩くないかを確認する。

WSTG の Test Objectives:

- Identify endpoints that implement CORS.
- Ensure that the CORS configuration is secure or harmless.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `curl -sI -H "Origin: https://evil.example" https://target/api` で `Access-Control-Allow-Origin` の応答を確認
2. Origin をそのまま反射する・`*` かつ `Allow-Credentials: true` になっていないか確認
3. 任意/緩いオリジンからの認証付きリクエストで機微データを読めないか検証
4. 過度に緩い CORS（旧指示の CONF-12 相当）を finding に

## 使用ツール

- curl
- Burp Suite
- securityheaders.io 相当の手動チェック
- curl
- Burp Suite
- wscat

## 判定基準（pass / fail の見分け）

- **pass**: Access-Control-Allow-Origin が許可オリジンのみ、認証付きリクエストでワイルドカードや Origin 反射がない。
- **fail**: 任意の Origin を反射しつつ Allow-Credentials: true、または null オリジンを許可している。
- 補足: プリフライトだけでなく、実リクエストの応答ヘッダで確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`, `cmd/curl-cors.txt`, `artifacts/ws-trace.md`
- `covers:` — `{id: WSTG-CLNT-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）
- `cors-websocket-check` — CORS と WebSocket の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing
