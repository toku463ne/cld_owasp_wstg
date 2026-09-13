# WSTG-BUSL-02 — Test Ability to Forge Requests

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

画面が出さない値やパラメータを自作リクエストで送り込めないかを確認する。

WSTG の Test Objectives:

- Review the project documentation looking for guessable, predictable, or hidden functionality of fields.
- Insert logically valid data in order to bypass normal business logic workflow.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 画面に出ない/無効化されたパラメータ（`price`,`status`,`userId`）を Burp Repeater でリクエストに追加/改変して通るか確認
2. 本来サーバが決めるべき値（価格・権限・所有者）をクライアントから指定して上書きできないか試す
3. 正規フローでは送られないフィールドを推測して注入する
4. サーバが信頼すべきでない入力を信頼している箇所を finding に

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: 想定外パラメータが無視され、価格・権限・状態は常にサーバ側の値が使われる。
- **fail**: 隠しフィールドや未提示パラメータ（price, role, discount 等）を送ると結果が変わる。
- 補足: hidden フィールドと JS の中の定数が探索の入口。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/02-Test_Ability_to_Forge_Requests
