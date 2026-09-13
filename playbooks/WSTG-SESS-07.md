# WSTG-SESS-07 — Testing Session Timeout

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

セッションのタイムアウトが適切に働くかを確認する。

WSTG の Test Objectives:

- Validate that a hard session timeout exists.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ログイン後に放置し、Burp で保持したセッションが無効化されるまでの時間を計測
2. 無効化がサーバ側判定か（クライアント時計依存でないか）を、Cookie の有効期限と実挙動で確認
3. 機微度に対しタイムアウトが長すぎないか（例: 銀行系で数時間）を評価
4. アイドルタイムアウトと絶対タイムアウトの両方の有無を確認

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 無操作タイムアウトと絶対タイムアウトがあり、業務リスクに見合った長さ。
- **fail**: タイムアウトがない、極端に長い、またはクライアント側だけで制御している。
- 補足: 計測には時間がかかる。放置して再試行する手順を run.yaml の steps に残す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/session-trace.burp`, `artifacts/token-samples.txt`, `notes.md`
- `covers:` — `{id: WSTG-SESS-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/07-Testing_Session_Timeout
