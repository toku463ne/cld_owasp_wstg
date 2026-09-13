# WSTG-CLNT-13 — Testing for Cross Site Script Inclusion

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

認証済みの JS/JSON を外部サイトから読み込ませて情報を抜けないか（XSSI）を確認する。

WSTG の Test Objectives:

- Locate sensitive data across the system.
- Assess the leakage of sensitive data through various techniques.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. JSON/JS を返す認証付きエンドポイントを、`<script src>` で外部ページから読み込めるか確認（`curl` で Content-Type も確認）
2. 動的 JS・JSONP が Cookie 認証で機微データを返し、他サイトから読めないか（CSRF 的窃取）検証
3. `X-Content-Type-Options: nosniff`・適切な Content-Type・CSRF 対策の有無を確認
4. クロスサイトでデータを読み出せた場合は XSSI として finding に

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: 動的 JS/JSON がスクリプトとして読み込めない、または推測不能なトークンで保護される。
- **fail**: 認証情報を含む JS/JSON を外部ページの script タグで読み込み、内容を取得できる。
- 補足: JSON 応答が配列リテラルのみ・JSONP 対応の場合に成立しやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-13, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/13-Testing_for_Cross_Site_Script_Inclusion
