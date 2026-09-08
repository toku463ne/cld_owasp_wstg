# WSTG-CONF-09 — Test File Permission

## 目的

ファイル・ディレクトリの権限設定が過剰でないかを確認する（ホスト側の確認が前提）。

WSTG の Test Objectives:

- Review and identify any rogue file permissions.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. In Linux, use ls command to check the file permissions. Alternatively, namei can also be used to recursively list file permissions.
2. The files and directories that require file permission testing include but are not limited to:
3. Configuration files/directory
4. Sensitive files (encrypted data, password, key)/directory
5. Log files (security logs, operation logs, admin logs)/directory
6. Executables (scripts, EXE, JAR, class, PHP, ASP)/directory

## 使用ツール

- Windows AccessEnum
- Windows AccessChk
- Linux namei

## 判定基準（pass / fail の見分け）

- **pass**: 設定ファイル・鍵・ログが必要最小限のユーザだけに読み書き可能。
- **fail**: 設定ファイルや秘密鍵が全ユーザ読み取り可、Web 公開ディレクトリが書き込み可等。
- 補足: リモートからは判定できない。ホスト側の情報提供が得られない場合は na とし、その旨を書く。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/config-review.md`, `notes.md`
- `covers:` — `{id: WSTG-CONF-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `server-config-review` — サーバ／プラットフォーム構成レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/09-Test_File_Permission
