# WSTG-CONF-10 — Test for Subdomain Takeover

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

1. **Black-Box Testing** — The first step is to enumerate the victim DNS servers and resource records
2. **Testing DNS A, CNAME Record Subdomain Takeover** — Perform a basic DNS enumeration on the victim's domain (victim.com) using dnsrecon:
3. **Testing NS Record Subdomain Takeover** — Identify all nameservers for the domain in scope:
4. **Gray-Box Testing** — The tester has the DNS zone file available which means DNS enumeration is not necessary

## 使用ツール

- dig - man page
- recon-ng - Web Reconnaissance framework
- theHarvester - OSINT intelligence gathering tool
- Sublist3r - OSINT subdomain enumeration tool
- dnsrecon - DNS Enumeration Script
- OWASP Amass DNS enumeration

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
