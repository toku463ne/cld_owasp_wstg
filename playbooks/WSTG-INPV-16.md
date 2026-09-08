# WSTG-INPV-16 — Testing for HTTP Incoming Requests

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

リバースプロキシ等が受け取るリクエストの扱いに、迂回や露出がないかを確認する。

WSTG の Test Objectives:

- Monitor all incoming and outgoing HTTP requests to the Web Server to inspect any suspicious requests.
- Monitor HTTP traffic without changes of end user Browser proxy or client-side application.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Reverse Proxy** — There is situation that we would like to monitor all HTTP incoming requests on web server but we can't change configuration on the browser o …
2. **Port Forwarding** — Port forwarding is another way to allow us intercept HTTP requests without changes of client-side
3. **TCP-level Network Traffic Capture** — This technique monitor all the network traffic at TCP-level

## 使用ツール

- Fiddler
- TCPProxy
- Charles Web Debugging Proxy
- WireShark
- PowerEdit-Pcap
- pcapteller
- replayproxy
- Ostinato

## 判定基準（pass / fail の見分け）

- **pass**: 内部向けパス・管理系へのリクエストが前段で確実に遮断される。
- **fail**: パス正規化の差やヘッダ細工で、前段の制限を越えて内部へ到達できる。
- 補足: 前段機器の設定ヒアリングと突き合わせないと誤判定しやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- `covers:` — `{id: WSTG-INPV-16, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-request-tamper` — HTTP リクエスト改変系の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/16-Testing_for_HTTP_Incoming_Requests
