# WSTG-CONF-03 — Test File Extensions Handling for Sensitive Information

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

拡張子の扱いによって、ソースや設定ファイルの中身が露出しないかを確認する。

WSTG の Test Objectives:

- Dirbust sensitive file extensions, or extensions that might contain raw data (e.g. scripts, raw data, credentials, etc.).
- Validate that no system framework bypasses exist on the rules set.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 既知ファイルの拡張子を変えて取得: `curl -s https://target/index.php.bak`（`.old .inc .txt .src ~`）
2. 設定/ソース拡張子（`.config .inc .sql .java .cs`）が平文配信されないか（200 で中身が返るか）確認
3. 大文字小文字違い（`.PHP`）・二重拡張子（`.php.jpg`）でハンドラ差が出ないか試す
4. 取得できたソース/設定は要約のみ finding に、実物は evidence にパス参照で保存

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: 実行対象の拡張子は実行され、.inc/.bak/.config 等は配信されない（404/403）。
- **fail**: .php.bak や .asp.old などでソースが平文で取得できる、または想定外の拡張子が実行される。
- 補足: 大文字小文字違い・二重拡張子（.php.jpg）も試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/ffuf-backup.txt`, `artifacts/found-files.md`, `cmd/traversal.txt`, `artifacts/traversal-findings.md`, `artifacts/upload-matrix.md`
- `covers:` — `{id: WSTG-CONF-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `backup-unref` — 旧・バックアップ・未参照ファイルの探索
- `traversal-probe` — ディレクトリトラバーサル・ファイルインクルードの検証
- `file-upload-tests` — ファイルアップロードの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/03-Test_File_Extensions_Handling_for_Sensitive_Information
