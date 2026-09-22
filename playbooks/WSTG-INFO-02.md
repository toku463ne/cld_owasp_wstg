# WSTG-INFO-02 — Fingerprint Web Server

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

Web サーバの種類とバージョンがどこまで外部から判別できるかを確認する。

WSTG の Test Objectives:

- Determine the version and type of a running web server to enable further discovery of any known vulnerabilities.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `curl -sI https://target/` で Server / X-Powered-By / Via ヘッダを確認
2. `nmap -sV -p80,443 -oN evidence/<活動フォルダ>/artifacts/nmap-http.txt target` と `whatweb --log-json=evidence/<活動フォルダ>/artifacts/whatweb.json https://target/` で製品名・バージョンを突き合わせる
3. 存在しないパス（`curl -s https://target/nope123`）を叩き、404 ページの体裁からも製品を推定
4. 手順2 で特定した製品名+バージョンから CPE 名（CVE 照合のキー）を引く: `curl -s --get --data-urlencode "keywordSearch=apache http server 2.4.49" https://services.nvd.nist.gov/rest/json/cpes/2.0 -o evidence/<活動フォルダ>/artifacts/nvd-cpe.json` の中身を `jq -r '.totalResults, (.products[].cpe.cpeName)' evidence/<活動フォルダ>/artifacts/nvd-cpe.json` で確認する（keywordSearch は実際に特定した製品名+バージョンに置き換える。0 件なら note の言い換えを試す）
5. 引いた cpeName で既知 CVE を一覧する: `curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:apache:http_server:2.4.49&resultsPerPage=100' -o evidence/<活動フォルダ>/artifacts/nvd-cve.json` → `jq -r '.totalResults' evidence/<活動フォルダ>/artifacts/nvd-cve.json` と `jq -r '.vulnerabilities[].cve | [.id, (.metrics.cvssMetricV31[0].cvssData.baseScore // "-" | tostring), .descriptions[0].value[0:100]] | @tsv' evidence/<活動フォルダ>/artifacts/nvd-cve.json`。CVSS 7.0 以上の CVE があれば CVE-ID と「バージョンをどこで特定したか」を finding に書く

## 使用ツール

- curl
- nmap
- whatweb
- jq

## 判定基準（pass / fail の見分け）

- **pass**: バナー・ヘッダ・エラーページから製品名とバージョンが特定できない、または既知脆弱性のないバージョン。
- **fail**: Server ヘッダ等でバージョンまで特定でき、そのバージョンに既知の脆弱性がある。
- 補足: バージョン秘匿だけでは対策にならない。パッチ状況とセットで報告する。CVE 照合はブラウザ不要で、NVD の REST API を curl で引く（検索キーは CPE 名なので、cpes/2.0 で cpeName を引いてから cves/2.0 に渡す）。whatweb/nmap の表記と NVD の呼称はずれる（nmap の "Apache httpd 2.4.49" → cpe:2.3:a:apache:http_server:2.4.49）。cpes/2.0 が 0 件なら製品名を言い換える／バージョンを粗く（2.4.49 → 2.4）して引き直す。CPE が違えば cves/2.0 は当然 0 件になるので、CPE が取れたことを確認するまで「既知脆弱性なし」と書かない。API キー無しは 30 秒 5 リクエストまで（超過は 403）。curl は http_proxy/https_proxy を見るのでプロキシ配下でも追加指定は不要。外向き HTTPS が塞がれた環境では `searchsploit apache 2.4.49`（apt: exploitdb、ローカルDBのみで通信不要）で代替し、その旨を record に書く。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server
