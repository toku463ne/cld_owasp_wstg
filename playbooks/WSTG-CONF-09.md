# WSTG-CONF-09 — Test File Permission

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ファイル・ディレクトリの権限設定が過剰でないかを確認する（ホスト側の確認が前提）。

WSTG の Test Objectives:

- Review and identify any rogue file permissions.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 対象サーバに手が届く場合、`ls -la` / `icacls` で Web ルート・設定ファイルの権限を確認
2. 設定ファイル・鍵・ログが others 読み取り可、または実行ユーザで書き換え可能でないか見る
3. アップロードディレクトリに実行権限が付いていないか確認
4. この項目はサーバ内部権限が前提。外部からのみの検査時は情報不足として na/ヒアリング扱い

## 使用ツール

- ls -l
- icacls

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
