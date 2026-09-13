# WSTG-BUSL-01 — Test Business Logic Data Validation

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. 業務データ（金額・数量・日付・状態）を業務上あり得ない値（負数・0・過大・過去日）に改変して受理されるか確認
2. クライアント側バリデーションを Burp で外し、サーバ側が同じ検証をしているか確認
3. 型・範囲・整合性（合計と明細の一致等）のサーバ側検証の抜けを探す
4. 業務ルールに反する状態を作れた場合、業務影響とともに finding に

## 使用ツール

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
