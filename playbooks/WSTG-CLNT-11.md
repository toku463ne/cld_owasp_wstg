# WSTG-CLNT-11 — Testing Web Messaging

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

postMessage による画面間通信が安全かを確認する。

WSTG の Test Objectives:

- Assess the security of the message's origin.
- Validate that it's using safe methods and validating its input.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Examine Origin Security** — Testers should check whether the application code is filtering and processing messages from trusted domains
2. **Examine Input Validation** — Although the website is theoretically accepting messages from trusted domains only, data must still be treated as externally-sourced, untrus …
3. **Static Code Analysis** — JavaScript code should be analyzed to determine how web messaging is implemented

## 使用ツール

- ブラウザ開発者ツール
- DOM Invader
- Retire.js
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 送信時に targetOrigin を明示し、受信時に event.origin を検証している。
- **fail**: targetOrigin が "*"、または origin 未検証のまま受信データを DOM/eval に渡している。
- 補足: 受信側ハンドラを JS から探すのが早い。addEventListener('message') を検索する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-11, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/11-Testing_Web_Messaging
