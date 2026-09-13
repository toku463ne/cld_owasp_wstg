# WSTG-ATHN-08 — Testing for Weak Security Question Answer

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

秘密の質問が認証手段として弱すぎないかを確認する。

WSTG の Test Objectives:

- Determine the complexity and how straight-forward the questions are.
- Assess possible user answers and brute force capabilities.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 秘密の質問の選択肢が、SNS 等から推測/調査可能な内容（出身地・母の旧姓）でないか確認
2. 質問への回答試行にレート制限・ロックがあるか確認
3. 質問だけでパスワードリセットまで到達できる（多要素でない）弱いフローでないか確認
4. 自由記述質問で任意の弱い質問を設定できないか確認

## 使用ツール

- Burp Suite
- メールクライアント
- 手動レビュー

## 判定基準（pass / fail の見分け）

- **pass**: 秘密の質問を単独の認証手段として使っていない。
- **fail**: 公開情報から推測できる質問（出身校・母親の旧姓）だけでパスワードリセットができる。
- 補足: 質問の変更・回答の使い回し可否も確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/reset-flow.md`, `notes.md`
- `covers:` — `{id: WSTG-ATHN-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `password-reset-review` — パスワード変更・リセット機能のレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/08-Testing_for_Weak_Security_Question_Answer
