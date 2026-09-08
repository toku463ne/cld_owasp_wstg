# WSTG-BUSL-02 — Test Ability to Forge Requests

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

1. **Through Identifying Guessable Values** — Using an intercepting proxy observe the HTTP POST/GET looking for some indication that values are incrementing at a regular interval or are …
2. **Through Identifying Hidden Options** — Using an intercepting proxy observe the HTTP POST/GET looking for some indication of hidden features such as debug that can be switched on o …

## 使用ツール

- OWASP Zed Attack Proxy (ZAP)
- Burp Suite

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
