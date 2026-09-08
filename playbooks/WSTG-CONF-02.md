# WSTG-CONF-02 — Test Application Platform Configuration

## 目的

Web サーバ・アプリサーバの既定構成が残っていないかを確認する。

WSTG の Test Objectives:

- Ensure that defaults and known files have been removed.
- Validate that no debugging code or extensions are left in the production environments.
- Review the logging mechanisms set in place for the application.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing**
2. **Comment Review** — It is very common for programmers to add comments when developing large web-based applications
3. **System Configuration** — Various tools, documents, or checklists can be used to give IT and security professionals a detailed assessment of target systems' conforman …
4. **Gray-Box Testing**
5. **Configuration Review** — The web server or application server configuration takes an important role in protecting the contents of the site and it must be carefully r …
6. **Logging** — Logging is an important asset of the security of an application architecture, since it can be used to detect flaws in applications (users co …
7. **Log Location** — Typically servers will generate local logs of their actions and errors, consuming the disk of the system the server is running on

## 使用ツール

- 手動レビュー
- ls -l / icacls
- nikto
- CIS Benchmark チェックリスト
- nmap -sV
- whatweb
- Wappalyzer
- httpx

## 判定基準（pass / fail の見分け）

- **pass**: サンプルページ・既定管理画面・不要モジュールが無効化され、ディレクトリリスティングも無効。
- **fail**: 既定のサンプルアプリ・テストページ・ディレクトリリスティング・不要な拡張が有効なまま。
- 補足: /server-status, /phpinfo.php, /examples など定番パスを必ず叩く。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/config-review.md`, `notes.md`, `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-CONF-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `server-config-review` — サーバ／プラットフォーム構成レビュー
- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/02-Test_Application_Platform_Configuration
