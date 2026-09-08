# WSTG-BUSL-01 — Test Business Logic Data Validation

## 目的

業務上ありえない値をサーバ側で拒否できているかを確認する。

WSTG の Test Objectives:

- Identify data injection points.
- Validate that all checks are occurring on the back end and can't be bypassed.
- Attempt to break the format of the expected data and analyze how the application is handling it.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Review the project documentation and use exploratory testing looking for data entry points or hand off points between systems or software.
2. Once found try to insert logically invalid data into the application/system.
3. Perform front-end GUI Functional Valid testing on the application to ensure that the only "valid" values are accepted.
4. Using an intercepting proxy observe the HTTP POST/GET looking for places that variables such as cost and quality are passed.
5. Once variables are found start interrogating the field with logically "invalid" data, such as social security numbers or unique identifiers that do not exist or that do not fit the business …

## 使用ツール

- OWASP Zed Attack Proxy (ZAP)
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 数量・金額・日付などの業務制約がサーバ側で検証される。
- **fail**: 負の数量・極端な金額・過去日付などが受理され、業務結果が変わる。
- 補足: クライアント側検証しかない場合は必ず fail。プロキシで直接投げて確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/01-Test_Business_Logic_Data_Validation
