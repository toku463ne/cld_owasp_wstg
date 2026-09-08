# WSTG-CONF-01 — Test Network Infrastructure Configuration

## 目的

ネットワーク構成として、公開すべきでないサービス・ポート・管理経路が外部に出ていないかを確認する。

WSTG の Test Objectives:

- Review the applications' configurations set across the network and validate that they are not vulnerable.
- Validate that used frameworks and systems are secure and not susceptible to known vulnerabilities due to unmaintained software or default settings and credentials.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Known Server Vulnerabilities** — Vulnerabilities found in the different areas of the application architecture, be it in the web server or in the back end database, can sever …
2. **Administrative Tools** — Any web server infrastructure requires the existence of administrative tools to maintain and update the information used by the application

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

- **pass**: 公開ポートが業務上必要なものだけで、管理系は接続元制限がかかっている。
- **fail**: SSH・RDP・DB・管理コンソール等が無制限に公開されている、またはサポート切れの製品が動いている。
- 補足: クラウドのセキュリティグループ設定と実際のスキャン結果を突き合わせる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/config-review.md`, `notes.md`, `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-CONF-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `server-config-review` — サーバ／プラットフォーム構成レビュー
- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント
- `tls-scan` — TLS 設定スキャン

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/01-Test_Network_Infrastructure_Configuration
