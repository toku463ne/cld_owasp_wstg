# WSTG-INPV-17 — Testing for Host Header Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. `Host:` ヘッダを `curl -H`/Burp で任意値に書き換え（`Host: evil.example`）て応答に反映/リダイレクトされるか確認
2. パスワードリセットのリンク生成に Host が使われ、リセット URL を攻撃者ドメインに向けられないか試す
3. `X-Forwarded-Host` 等でキャッシュポイズニング・認可迂回ができないか確認
4. Host 依存のリンク生成・ルーティングがある場合は影響を finding に

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: Host を偽装しても、リンク生成・リセットメール・キャッシュキーに反映されない（許可ホストのみ）。
- **fail**: 偽装した Host がリセットリンクや絶対 URL に反映される、キャッシュポイズニングにつながる。
- 補足: X-Forwarded-Host など類似ヘッダも試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- `covers:` — `{id: WSTG-INPV-17, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-request-tamper` — HTTP リクエスト改変系の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/17-Testing_for_Host_Header_Injection
