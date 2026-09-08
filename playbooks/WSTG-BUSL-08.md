# WSTG-BUSL-08 — Test Upload of Unexpected File Types

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

想定外の種類のファイルをアップロードできないかを確認する。

WSTG の Test Objectives:

- Review the project documentation for file types that are rejected by the system.
- Verify that the unwelcomed file types are rejected and handled safely.
- Verify that file batch uploads are secure and do not allow any bypass against the set security measures.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Study the applications logical requirements.
2. Prepare a library of files that are "not approved" for upload that may contain files such as: jsp, exe, or HTML files containing script.
3. In the application navigate to the file submission or upload mechanism.
4. Submit the "not approved" file for upload and verify that they are properly prevented from uploading
5. Check if the website only do file type check in client-side JavaScript
6. Check if the website only check the file type by "Content-Type" in HTTP request.
7. Check if the website only check by the file extension.

## 使用ツール

- Burp Suite
- EICAR テストファイル
- 手動

## 判定基準（pass / fail の見分け）

- **pass**: 拡張子と実際の中身（マジックバイト）の両方を検証し、許可種別のみ受理する。
- **fail**: 拡張子偽装・Content-Type 偽装で、許可されていない種類のファイルが保存される。
- 補足: 保存先が Web 公開領域かどうかで重大度が大きく変わる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/upload-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `file-upload-tests` — ファイルアップロードの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/08-Test_Upload_of_Unexpected_File_Types
