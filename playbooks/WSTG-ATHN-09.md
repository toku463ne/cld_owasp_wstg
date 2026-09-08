# WSTG-ATHN-09 — Testing for Weak Password Change or Reset Functionalities

## 目的

パスワード変更・リセット機能に、他人のパスワードを変更できる欠陥がないかを確認する。

WSTG の Test Objectives:

- Determine the resistance of the application to subversion of the account change process allowing someone to change the password of an account.
- Determine the resistance of the passwords reset functionality against guessing or bypassing.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Test Password Reset** — In addition to the previous checks it is important to verify the following:
2. **Test Password Change** — In addition to the previous test it is important to verify:

## 使用ツール

- Burp Suite
- メールクライアント
- 手動レビュー

## 判定基準（pass / fail の見分け）

- **pass**: 変更時に現行パスワードを要求し、リセットトークンは十分ランダム・短寿命・単回使用。
- **fail**: 現行パスワードなしで変更できる、トークンが推測可能・再利用可能、他人の ID を指定してリセットできる。
- 補足: リセット完了時に既存セッションが無効化されるかも確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/reset-flow.md`, `notes.md`
- `covers:` — `{id: WSTG-ATHN-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `password-reset-review` — パスワード変更・リセット機能のレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/09-Testing_for_Weak_Password_Change_or_Reset_Functionalities
