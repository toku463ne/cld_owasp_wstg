# WSTG-CONF-02 — Test Application Platform Configuration

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. 定番パスを叩く: `curl -s https://target/{server-status,server-info,phpinfo.php,examples/,manual/,test/}`
2. ディレクトリリスティングを確認（`curl -s https://target/images/` 等で index が返るか）
3. 既定管理画面・サンプルアプリの有無を確認: `for pth in manager manager/html docs examples host-manager admin-console web-console; do echo "$pth -> $(curl -s -o /dev/null -w '%{http_code}' https://target/$pth/)"; done | tee evidence/<活動フォルダ>/artifacts/default-apps.txt`。200/401/403 が返るパスは存在（Tomcat `/manager` 等）。既定資格情報の可否は別途確認
4. 不要機能が有効でないか応答で確認する: `curl -sI -X OPTIONS https://target/` の `Allow` 行に PUT/DELETE/TRACE が並ばないか、`Server`/`X-Powered-By` に余計なモジュール（`mod_status`・PHP等）が出ないか、`?debug=true`・`X-Debug` 系でデバッグ出力（スタック・SQL・変数ダンプ）が返らないか。有効な不要機能を artifacts に列挙し finding に

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: サンプルページ・既定管理画面・不要モジュールが無効化され、ディレクトリリスティングも無効。
- **fail**: 既定のサンプルアプリ・テストページ・ディレクトリリスティング・不要な拡張が有効なまま。
- 補足: /server-status, /phpinfo.php, /examples など定番パスを必ず叩く。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/config-review.md`, `notes.md`, `artifacts/headers-http.txt`, `artifacts/headers-https.txt`, `artifacts/whatweb.json`
- `covers:` — `{id: WSTG-CONF-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `server-config-review` — サーバ／プラットフォーム構成レビュー
- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/02-Test_Application_Platform_Configuration
