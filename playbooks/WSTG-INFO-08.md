# WSTG-INFO-08 — Fingerprint Web Application Framework

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

アプリのフレームワーク・CMS・ライブラリとそのバージョンを特定する。

WSTG の Test Objectives:

- Fingerprint the components being used by the web applications.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `whatweb --log-json=evidence/<活動フォルダ>/artifacts/whatweb.json https://target/` と ブラウザ拡張 Wappalyzer でフレームワーク/CMS を推定
2. 応答ヘッダと Cookie を保存して基盤を推定: `curl -sD evidence/<活動フォルダ>/artifacts/headers.txt -o /dev/null https://target/ && grep -iE '^(set-cookie|x-powered-by|server|x-aspnet-version|x-generator):' evidence/<活動フォルダ>/artifacts/headers.txt`。Cookie 名（`JSESSIONID`=Java / `ASP.NET_SessionId`=.NET / `laravel_session`=Laravel / `ci_session`=CodeIgniter）・`X-Powered-By`・URL パスから基盤を特定
3. 取得したフロント JS を `retire --path <JSフォルダ> --outputformat json --outputpath evidence/<活動フォルダ>/artifacts/retire.json`（Retire.js）で走査し、jQuery 等ライブラリのバージョンと既知脆弱性を確認
4. 手順1・2 で特定した CMS/フレームワークごとに CPE 名を引く（retire.js が CVE まで出したフロント JS は不要）: `curl -s --get --data-urlencode "keywordSearch=wordpress 6.4.2" https://services.nvd.nist.gov/rest/json/cpes/2.0 -o evidence/<活動フォルダ>/artifacts/nvd-cpe-cms.json` → `jq -r '.totalResults, (.products[].cpe.cpeName)' evidence/<活動フォルダ>/artifacts/nvd-cpe-cms.json`
5. その cpeName で CVE を一覧し、finding にバージョン根拠（どこで判ったか）を添える: `curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:wordpress:wordpress:6.4.2&resultsPerPage=100' -o evidence/<活動フォルダ>/artifacts/nvd-cve-cms.json` → `jq -r '.vulnerabilities[].cve | [.id, (.metrics.cvssMetricV31[0].cvssData.baseScore // "-" | tostring), .descriptions[0].value[0:100]] | @tsv' evidence/<活動フォルダ>/artifacts/nvd-cve-cms.json`

## 使用ツール

- whatweb
- Wappalyzer
- curl
- Retire.js
- jq

## 判定基準（pass / fail の見分け）

- **pass**: 使用フレームワークが特定できない、または特定できても既知脆弱性のないバージョン。
- **fail**: 既知脆弱性のあるバージョンのフレームワーク・ライブラリを使用している（Cookie 名・パス・ヘッダ・JS から特定）。
- 補足: フロント側のライブラリ（jQuery 等）は Retire.js で確認できる。Retire.js は実行時に github から脆弱性DB（jsrepository.json）を取りに行くため、プロキシ必須／外向き通信が絞られた環境では更新に失敗することがある（amass の libpostal と同じ構図）。`--path` は既にダウンロード済みのローカル JS を走査するので、DB さえ取得できれば対象への通信は不要。更新できないときは事前に DB を取得しておくか、下の NVD API での照合に回す。CMS・フレームワーク側の CVE 照合はブラウザ不要で、NVD の cpes/2.0（製品名+バージョン → cpeName）→ cves/2.0（cpeName → CVE 一覧）を curl で引く（API キー無しは 30 秒 5 リクエストまで。0 件の読み替えは WSTG-INFO-02 の note と同じ）。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/08-Fingerprint_Web_Application_Framework
