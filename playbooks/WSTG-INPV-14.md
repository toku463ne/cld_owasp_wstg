# WSTG-INPV-14 — Testing for Incubated Vulnerability

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

保存された不正データが後続処理で発火する（潜伏型）欠陥がないかを確認する。

WSTG の Test Objectives:

- Identify injections that are stored and require a recall step to the stored injection.
- Understand how a recall step could occur.
- Set listeners or activate the recall step if possible.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 単体では無害でも、保存→別処理で発火する連鎖（例: 保存 XSS が管理バッチで実行）を探す
2. 入力が時間差・別コンポーネント経由で悪用される経路を業務フローから推定
3. 複数の弱点（格納＋後段の信頼）を Burp で組み合わせて成立するシナリオを検証
4. 単発テストで見落とす連鎖を finding にシナリオとして整理

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 保存時・利用時の両方で検証・エスケープされる。
- **fail**: 保存時は無害でも、バッチ・帳票・管理画面など別経路で発火する。
- 補足: 発火先が管理者画面や外部連携先の場合、重大度を上げる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-INPV-14, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/14-Testing_for_Incubated_Vulnerability
