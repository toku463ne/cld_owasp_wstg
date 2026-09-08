# WSTG-CONF-04 — Review Old Backup and Unreferenced Files for Sensitive Information

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

公開ディレクトリに残った旧版・バックアップ・未参照ファイルを探す。

WSTG の Test Objectives:

- Find and analyse unreferenced files that might contain sensitive information.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing** — Testing for unreferenced files uses both automated and manual techniques, and typically involves a combination of the following:
2. **Inference from the Naming Scheme Used for Published Content** — Enumerate all of the application's pages and functionality
3. **Other Clues in Published Content** — Many web applications leave clues in published content that can lead to the discovery of hidden pages and functionality
4. **Blind Guessing** — In its simplest form, this involves running a list of common filenames through a request engine in an attempt to guess files and directories …
5. **Information Obtained Through Server Vulnerabilities and Misconfiguration** — The most obvious way in which a misconfigured server may disclose unreferenced pages is through directory listing
6. **Use of Publicly Available Information** — Pages and functionality in Internet-facing web applications that are not referenced from within the application itself may be referenced fro …
7. **Filename Filter Bypass** — Because deny list filters are based on regular expressions, one can sometimes take advantage of obscure OS filename expansion features in wh …

## 使用ツール

- Nessus
- Nikto2
- Web spider tools
- wget
- Wget for Windows
- Sam Spade
- Spike proxy includes a web site crawler function
- Xenu

## 判定基準（pass / fail の見分け）

- **pass**: 総当たりでバックアップ・旧版・エディタの一時ファイルが見つからない。
- **fail**: .bak/.old/~/.swp/.zip、リポジトリメタデータ（.git/、.svn/）等が取得できる。
- 補足: .git/config が取れたらリポジトリ全体を復元できる可能性がある。重大度は高く扱う。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/ffuf-backup.txt`, `artifacts/found-files.md`
- `covers:` — `{id: WSTG-CONF-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `backup-unref` — 旧・バックアップ・未参照ファイルの探索

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/04-Review_Old_Backup_and_Unreferenced_Files_for_Sensitive_Information
