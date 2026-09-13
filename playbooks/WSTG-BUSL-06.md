# WSTG-BUSL-06 — Testing for the Circumvention of Work Flows

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

業務フローの順序を飛ばして目的の状態に到達できないかを確認する。

WSTG の Test Objectives:

- Review the project documentation for methods to skip or go through steps in the application process in a different order from the intended business logic flow.
- Develop a misuse case and try to circumvent every logic flow identified.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 多段フロー（申込→承認→確定、カート→決済）の途中ステップを URL 直打ち/Burp で飛ばせるか確認
2. 順序を入れ替える・前工程を省く・完了後に前工程へ戻ると状態が不整合にならないか確認
3. 各ステップでサーバ側が前提状態を検証しているか確認
4. ワークフローを迂回して不正な最終状態（未払い確定等）を作れた場合は finding に

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 各ステップでサーバ側の状態が検証され、途中を飛ばすと拒否される。
- **fail**: 支払い前に完了状態へ進める、承認を経ずに確定できる等。
- 補足: 「戻る」「直リンク」「並行タブ」の3パターンを試すと出やすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/06-Testing_for_the_Circumvention_of_Work_Flows
