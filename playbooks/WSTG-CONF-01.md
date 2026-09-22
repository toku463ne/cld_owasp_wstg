# WSTG-CONF-01 — Test Network Infrastructure Configuration

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. `nmap -sV -p- --open -oN evidence/<活動フォルダ>/artifacts/nmap-allports.txt target` で公開ポート/サービスを洗い出す
2. SSH(22)/RDP(3389)/DB(3306,5432,1433)/管理コンソール等が公開されていないか確認
3. `nikto -h https://target -o evidence/<活動フォルダ>/artifacts/nikto.txt` と特定製品の既知脆弱性・既定資格情報を照合
4. クラウドのセキュリティグループ/FW 設定（ヒアリング）と実スキャン結果を突き合わせ、差分を指摘

## 使用ツール

- nmap
- nikto

## 判定基準（pass / fail の見分け）

- **pass**: 公開ポートが業務上必要なものだけで、管理系は接続元制限がかかっている。
- **fail**: SSH・RDP・DB・管理コンソール等が無制限に公開されている、またはサポート切れの製品が動いている。
- 補足: クラウドのセキュリティグループ設定と実際のスキャン結果を突き合わせる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/config-review.md`, `notes.md`, `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-CONF-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `server-config-review` — サーバ／プラットフォーム構成レビュー
- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント
- `tls-scan` — TLS 設定スキャン

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/01-Test_Network_Infrastructure_Configuration
