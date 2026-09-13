# WSTG-CONF-10 — Test for Subdomain Takeover

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

宙に浮いた DNS レコードにより、第三者がサブドメインを乗っ取れないかを確認する。

WSTG の Test Objectives:

- Enumerate all possible domains (previous and current).
- Identify forgotten or misconfigured domains.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. サブドメインを列挙（`amass`/`crt.sh`）し、各 CNAME を `dig CNAME sub.target.co.jp` で確認
2. CNAME 先が未登録のクラウドサービス（S3/GitHub Pages/Heroku 等）を指していないか確認
3. 疑わしいものはサービスの「該当リソースが存在しない」旨のエラー画面が出るかで判定
4. 乗っ取り可能性がある場合も実際の取得は行わず、CNAME と応答を証跡に留める

## 使用ツール

- amass
- crt.sh
- dig

## 判定基準（pass / fail の見分け）

- **pass**: 全サブドメインの向き先が実在し、解放済みクラウドリソースを指す CNAME がない。
- **fail**: 解放済みのホスティング先を指す CNAME/A があり、第三者が同名リソースを取得して掌握できる。
- 補足: 実際の乗っ取りは行わない。到達性とエラー応答（NoSuchBucket 等）で判断し、証拠として記録する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-bucket.txt`, `artifacts/dangling-dns.md`, `artifacts/subdomains.txt`, `artifacts/dorking-hits.md`, `cmd/whois.txt`
- `covers:` — `{id: WSTG-CONF-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認
- `recon-osint` — 外部 OSINT・公開情報の収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/10-Test_for_Subdomain_Takeover
