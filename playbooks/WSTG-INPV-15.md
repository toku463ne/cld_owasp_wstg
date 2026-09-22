# WSTG-INPV-15 — Testing for HTTP Splitting Smuggling

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

リクエスト/レスポンスの境界解釈のずれを悪用できないかを確認する。

WSTG の Test Objectives:

- Assess if the application is vulnerable to splitting, identifying what possible attacks are achievable.
- Assess if the chain of communication is vulnerable to smuggling, identifying what possible attacks are achievable.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. リクエスト/応答に CRLF（`%0d%0a`）を `curl`/Burp で注入し、ヘッダ分割・レスポンス分割ができるか確認
2. フロント/バックの解釈差を突く smuggling（`Content-Length` と `Transfer-Encoding` の食い違い）を検証
3. キャッシュポイズニング・認可迂回につながらないか確認
4. 中間装置（CDN/LB）構成に依存するため、成立条件と経路を finding に明記

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: CR/LF がヘッダに注入できず、Content-Length と Transfer-Encoding の扱いが経路全体で一貫している。
- **fail**: ヘッダ分割、またはフロントとバックの解釈差でリクエストを密輸できる。
- 補足: スマグリング検証は他利用者に影響し得る。実施前に必ず合意と時間帯調整を行う。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- `covers:` — `{id: WSTG-INPV-15, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-request-tamper` — HTTP リクエスト改変系の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/15-Testing_for_HTTP_Splitting_Smuggling
