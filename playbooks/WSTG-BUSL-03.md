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

1. 改ざん検知が必要なデータ（署名付きトークン・金額・数量）を Burp で改変し、整合性チェックが働くか確認
2. 隠しフィールド・Cookie・JWT の署名を外す/改変して受理されるか試す
3. サーバ側で再計算・再検証しているか（クライアント値を鵜呑みにしないか）確認
4. 整合性チェックが無い/迂回できる箇所を finding に

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: サーバ側の値が正とされ、クライアント由来の値は検証・再計算される。
- **fail**: 署名なしのトークンや合計値をクライアントが決められ、改ざんが検出されない。
- 補足: 監査ログの改ざん可否も観点に含める。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/03-Test_Integrity_Checks
