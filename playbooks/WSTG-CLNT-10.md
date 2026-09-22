# WSTG-CLNT-10 — Testing WebSockets

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. DevTools の Network→WS で WebSocket 接続を確認し、ハンドシェイクの Origin 検証有無を見る
2. `wss://`（暗号化）か、認証・認可がメッセージ単位で行われているか確認
3. Burp で WS メッセージを傍受・改変し、認可迂回や注入ができないか試す
4. Origin 検証無し・平文 ws・入力無害化欠如を finding に

## 使用ツール

- ブラウザ開発者ツール
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: wss:// を使用し、ハンドシェイク時に認証・Origin 検証があり、メッセージも認可される。
- **fail**: ws:// の平文通信、Origin 検証なし（Cross-Site WebSocket Hijacking）、認可なしで他人のデータを取得できる。
- 補足: メッセージ単位の認可漏れを見落としやすい。接続後の操作も試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-cors.txt`, `artifacts/ws-trace.md`
- `covers:` — `{id: WSTG-CLNT-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cors-websocket-check` — CORS と WebSocket の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/10-Testing_WebSockets
