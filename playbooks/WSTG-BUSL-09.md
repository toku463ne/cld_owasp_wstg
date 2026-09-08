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

1. **Malicious File Types** — The simplest checks that an application can do are to determine that only trusted types of files can be uploaded.
2. **Web Shells** — If the server is configured to execute code, then it may be possible to obtain command execution on the server by uploading a file known as …
3. **Filter Evasion** — The first step is to determine what the filters are allowing or blocking, and where they are implemented
4. **Malicious File Contents** — Once the file type has been validated, it is important to also ensure that the contents of the file are safe
5. **Malware** — Applications should generally scan uploaded files with anti-malware software to ensure that they do not contain anything malicious
6. **Archive Directory Traversal** — If the application extracts archives (such as Zip files), then it may be possible to write to unintended locations using directory traversal
7. **Zip Bombs** — A Zip bomb (more generally known as a decompression bomb) is an archive file that contains a large volume of data

## 使用ツール

- Metasploit's payload generation functionality
- Intercepting proxy

## 判定基準（pass / fail の見分け）

- **pass**: 実行可能ファイルが保存されない、保存されても Web から実行できず、マルウェアスキャンがある。
- **fail**: Web シェルを保存して実行できる、EICAR がスキャンされず保存される。
- 補足: 実際のマルウェアは使わない。EICAR と無害なスクリプトで検証する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/upload-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `file-upload-tests` — ファイルアップロードの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/09-Test_Upload_of_Malicious_Files
