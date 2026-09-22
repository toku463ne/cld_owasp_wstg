# WSTG-BUSL-09 — Test Upload of Malicious Files

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

悪意あるファイルの投入と実行が防がれているかを確認する。

WSTG の Test Objectives:

- Identify the file upload functionality.
- Review the project documentation to identify what file types are considered acceptable, and what types would be considered dangerous or malicious.
- - If documentation is not available then consider what would be appropriate based on the purpose of the application.
- Determine how the uploaded files are processed.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 実行可能/悪性ファイル（Web シェル・EICAR テストウイルス・巨大ファイル・XXE 入り docx/svg）を上げて処理を確認
2. アップロードされた実行ファイルが Web ルートで実行できないか（`curl` で叩く）確認
3. ウイルススキャン・サイズ/型検証・保存場所の分離が機能しているか確認
4. 実行や被害が成立したら重大度高めで finding に。検証は EICAR 等の無害検体で

## 使用ツール

- EICAR テスト検体
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 実行可能ファイルが保存されない、保存されても Web から実行できず、マルウェアスキャンがある。
- **fail**: Web シェルを保存して実行できる、EICAR がスキャンされず保存される。
- 補足: 実際のマルウェアは使わない。EICAR と無害なスクリプトで検証する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/upload-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `file-upload-tests` — ファイルアップロードの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/09-Test_Upload_of_Malicious_Files
