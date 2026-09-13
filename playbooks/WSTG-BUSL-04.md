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

1. 処理の応答時間差（成功/失敗・存在/非存在）を Burp/`curl` で計測し、情報が漏れないか確認
2. 時間依存の業務（予約・在庫・クーポン）で、タイミングを突いた不正取得ができないか確認
3. レースコンディション（後述 BUSL-05 と関連）につながる時間窓がないか確認
4. 計測結果（応答時間の統計）を artifacts に残し、判別可能性を finding に

## 使用ツール

- Burp Suite
- curl

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
