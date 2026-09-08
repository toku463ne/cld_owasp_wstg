# WSTG-CLNT-10 — Testing WebSockets

## 目的

WebSocket の接続・認可・暗号化が適切かを確認する。

WSTG の Test Objectives:

- Identify the usage of WebSockets.
- Assess its implementation by using the same tests on normal HTTP channels.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing** — Identify that the application is using WebSockets.
2. **Gray-Box Testing** — Gray-box testing is similar to black-box testing

## 使用ツール

- OWASP Zed Attack Proxy (ZAP)
- WebSocket Client
- Google Chrome Simple WebSocket Client

## 判定基準（pass / fail の見分け）

- **pass**: wss:// を使用し、ハンドシェイク時に認証・Origin 検証があり、メッセージも認可される。
- **fail**: ws:// の平文通信、Origin 検証なし（Cross-Site WebSocket Hijacking）、認可なしで他人のデータを取得できる。
- 補足: メッセージ単位の認可漏れを見落としやすい。接続後の操作も試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-cors.txt`, `artifacts/ws-trace.md`
- `covers:` — `{id: WSTG-CLNT-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cors-websocket-check` — CORS と WebSocket の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets
