# WSTG-BUSL-03 — Test Integrity Checks

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

データの整合性チェック（改ざん検知）が機能しているかを確認する。

WSTG の Test Objectives:

- Review the project documentation for components of the system that move, store, or handle data.
- Determine what type of data is logically acceptable by the component and what types the system should guard against.
- Determine who should be allowed to modify or read that data in each component.
- Attempt to insert, update, or delete data values used by each component that should not be allowed per the business logic workflow.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Specific Testing Method 1** — Using a proxy capture HTTP traffic looking for hidden fields.
2. **Specific Testing Method 2** — Using a proxy capture HTTP traffic looking for a place to insert information into areas of the application that are non-editable.
3. **Specific Testing Method 3** — List components of the application or system that could be impacted, for example logs or databases.

## 使用ツール

- Various system/application tools such as editors and file manipulation tools.
- OWASP Zed Attack Proxy (ZAP)
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: サーバ側の値が正とされ、クライアント由来の値は検証・再計算される。
- **fail**: 署名なしのトークンや合計値をクライアントが決められ、改ざんが検出されない。
- 補足: 監査ログの改ざん可否も観点に含める。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/03-Test_Integrity_Checks
