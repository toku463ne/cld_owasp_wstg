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
2. 80/443 それぞれの応答ヘッダを保存し、製品名・バージョンの手掛かりを抜き出す（ポートスキャナはプロキシを通らず、プロキシ配下では filtered になって何も取れないため curl で取る。README「プロキシ配下での準備」）: `curl -s -m 15 -D - -o /dev/null http://target/ > evidence/<活動フォルダ>/artifacts/headers-http.txt; curl -sk -m 15 -D - -o /dev/null https://target/ > evidence/<活動フォルダ>/artifacts/headers-https.txt; grep -qi '^HTTP/' evidence/<活動フォルダ>/artifacts/headers-http.txt evidence/<活動フォルダ>/artifacts/headers-https.txt || { echo "80/443 のどちらからも応答が無い＝対象に届いていない。プロキシ配下なら http_proxy/https_proxy が設定されているか確認する（curl -sI https://target/ で疎通確認）" >&2; exit 3; }; grep -iE '^(HTTP/|server:|x-powered-by:|via:|x-aspnet-version:|x-generator:)' evidence/<活動フォルダ>/artifacts/headers-http.txt evidence/<活動フォルダ>/artifacts/headers-https.txt || [ $? -eq 1 ]`。続けて `whatweb ${https_proxy:+--proxy "${https_proxy##*[/@]}"} --log-json=evidence/<活動フォルダ>/artifacts/whatweb.json https://target/` で製品名・バージョンを突き合わせる（whatweb の --proxy は host:port 形式なので https_proxy から取り出して渡す。認証付きプロキシは --proxy-user user:pass も足す）
3. 存在しないパス（`curl -s https://target/nope123`）を叩き、404 ページの体裁からも製品を推定
4. 手順2 で特定した製品名+バージョンから CPE 名（CVE 照合のキー）を引く: `curl -s --get --data-urlencode "keywordSearch=apache http server 2.4.49" https://services.nvd.nist.gov/rest/json/cpes/2.0 -o evidence/<活動フォルダ>/artifacts/nvd-cpe.json` の中身を `jq -r '.totalResults, (.products[].cpe.cpeName)' evidence/<活動フォルダ>/artifacts/nvd-cpe.json` で確認する（keywordSearch は実際に特定した製品名+バージョンに置き換える。0 件なら note の言い換えを試す）
   > ⚠️ **負荷注意（手順4）**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。超えると 403。連続で叩かない（対象ではなく NVD への負荷）。
5. 引いた cpeName で既知 CVE を一覧する: `curl -s 'https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=cpe:2.3:a:apache:http_server:2.4.49&resultsPerPage=100' -o evidence/<活動フォルダ>/artifacts/nvd-cve.json` → `jq -r '.totalResults' evidence/<活動フォルダ>/artifacts/nvd-cve.json` と `jq -r '.vulnerabilities[].cve | [.id, (.metrics.cvssMetricV31[0].cvssData.baseScore // "-" | tostring), .descriptions[0].value[0:100]] | @tsv' evidence/<活動フォルダ>/artifacts/nvd-cve.json`。CVSS 7.0 以上の CVE があれば CVE-ID と「バージョンをどこで特定したか」を finding に書く
   > ⚠️ **負荷注意（手順5）**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。手順4と続けて叩くと 403 になりやすいので間隔を空ける。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順4**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。超えると 403。連続で叩かない（対象ではなく NVD への負荷）。
- **手順5**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。手順4と続けて叩くと 403 になりやすいので間隔を空ける。

## 使用ツール

- curl
- whatweb
- jq

## 判定基準（pass / fail の見分け）

- **pass**: バナー・ヘッダ・エラーページから製品名とバージョンが特定できない、または既知脆弱性のないバージョン。
- **fail**: Server ヘッダ等でバージョンまで特定でき、そのバージョンに既知の脆弱性がある。
- 補足: バージョン秘匿だけでは対策にならない。パッチ状況とセットで報告する。CVE 照合はブラウザ不要で、NVD の REST API を curl で引く（検索キーは CPE 名なので、cpes/2.0 で cpeName を引いてから cves/2.0 に渡す）。Server ヘッダ/whatweb の表記と NVD の呼称はずれる（`Server: Apache/2.4.49` → cpe:2.3:a:apache:http_server:2.4.49）。cpes/2.0 が 0 件なら製品名を言い換える／バージョンを粗く（2.4.49 → 2.4）して引き直す。CPE が違えば cves/2.0 は当然 0 件になるので、CPE が取れたことを確認するまで「既知脆弱性なし」と書かない。API キー無しは 30 秒 5 リクエストまで（超過は 403）。curl は http_proxy/https_proxy を見るのでプロキシ配下でも追加指定は不要。外向き HTTPS が塞がれた環境では `searchsploit apache 2.4.49`（apt: exploitdb、ローカルDBのみで通信不要）で代替し、その旨を record に書く。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/headers-http.txt`, `artifacts/headers-https.txt`, `artifacts/whatweb.json`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server
