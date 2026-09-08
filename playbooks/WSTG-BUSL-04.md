# WSTG-BUSL-04 — Test for Process Timing

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

処理時間・順序の隙を突けないか（レースを含む）を確認する。

WSTG の Test Objectives:

- Review the project documentation for system functionality that may be impacted by time.
- Develop and execute misuse cases.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. The tester should identify which processes are dependent on time, whether it was a window for a task to be completed, or if it was execution time between two processes that could allow the b …
2. Following that, it is best to automate the requests that will abuse the above discovered processes, as tools are better fit to analyze the timing and are more precise than manual testing.
3. The tester should draw a diagram of how the process flows, the injection points, and prepare the requests before hand to launch them at the vulnerable processes.

## 使用ツール

- Burp Suite
- 手動操作
- 業務仕様書

## 判定基準（pass / fail の見分け）

- **pass**: 重要処理が排他制御され、並行実行しても二重適用されない。
- **fail**: 同時実行でクーポン多重適用・残高の二重引き出し等が起きる。
- 補足: 並行リクエストは負荷になる。件数と時間帯を事前に合意する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/04-Test_for_Process_Timing
