# WSTG-CLNT-06 — Testing for Client-side Resource Manipulation

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

JS が読み込むリソース（スクリプト・iframe・データ）の URL を操作できないかを確認する。

WSTG の Test Objectives:

- Identify sinks with weak input validation.
- Assess the impact of the resource manipulation.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. JS がユーザ制御データで動的にリソース URL（script/img/iframe の src）を組み立てないか確認
2. その URL に外部/悪性リソースを指定させて読み込ませられないか試す
3. `location`,`XMLHttpRequest`,`fetch` の宛先がユーザ入力で操作されないか確認
4. リソース読み込み先を乗っ取れた場合の影響を finding に

## 使用ツール

- ブラウザ開発者ツール
- DOM Invader
- Retire.js
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 読み込み先が固定または許可リスト制。
- **fail**: パラメータで読み込み元を差し替え、外部のスクリプトやコンテンツを読み込ませられる。
- 補足: JSONP エンドポイントが残っている場合は特に確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/06-Testing_for_Client-side_Resource_Manipulation
