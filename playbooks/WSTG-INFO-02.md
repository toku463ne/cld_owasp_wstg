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
2. 80/443 それぞれの応答ヘッダを保存し、製品名・バージョンの手掛かりを抜き出す（ポートスキャナはプロキシを通らず、プロキシ配下では filtered になって何も取れないため curl で取る。README「プロキシ配下での準備」）: `curl -s -m 15 -D - -o /dev/null http://target/ > evidence/<活動フォルダ>/artifacts/headers-http.txt; curl -sk -m 15 -D - -o /dev/null https://target/ > evidence/<活動フォルダ>/artifacts/headers-https.txt; grep -qi '^HTTP/' evidence/<活動フォルダ>/artifacts/headers-http.txt evidence/<活動フォルダ>/artifacts/headers-https.txt || { echo "80/443 のどちらからも応答が無い＝対象に届いていない。プロキシ配下なら http_proxy/https_proxy が設定されているか確認する（curl -sI https://target/ で疎通確認）" >&2; exit 3; }; grep -iE '^(HTTP/|server:|x-powered-by:|via:|x-aspnet-version:|x-generator:)' evidence/<活動フォルダ>/artifacts/headers-http.txt evidence/<活動フォルダ>/artifacts/headers-https.txt || [ $? -eq 1 ]`。続けて `test ! -e evidence/<活動フォルダ>/artifacts/whatweb.json || rm -f evidence/<活動フォルダ>/artifacts/whatweb.json; whatweb ${https_proxy:+--proxy "${https_proxy##*[/@]}"} --log-json=evidence/<活動フォルダ>/artifacts/whatweb.json https://target/` で製品名・バージョンを突き合わせる（whatweb の --log-json は既存ファイルに追記して JSON が壊れるので、先に消してから実行する。--proxy は host:port 形式なので https_proxy から取り出して渡す。認証付きプロキシは --proxy-user user:pass も足す）
3. 存在しないパスを http/https で叩いて 404 ページの本文を保存し、本文に出ている「製品/バージョン」を抜き出す（既定のエラーページは Server ヘッダでバージョンを隠していても本文に出すことがある。例: openresty/nginx の `<center>openresty/1.21.4.1</center>`、Apache の `<address>Apache/2.4.41 … Server at …</address>`、Tomcat の `Apache Tomcat/9.0.31`）: `curl -sk -m 15 -o evidence/<活動フォルダ>/artifacts/404-https.html -w 'https %{http_code}\n' https://target/wstg-nope-404; curl -s -m 15 -o evidence/<活動フォルダ>/artifacts/404-http.html -w 'http %{http_code}\n' http://target/wstg-nope-404; grep -ohiE '(Apache Tomcat|openresty|nginx|Apache|Microsoft-IIS|Microsoft-HTTPAPI|lighttpd|LiteSpeed|Tengine|Jetty|Werkzeug|gunicorn|PHP|Varnish|Caddy)/[0-9][0-9A-Za-z._-]*' evidence/<活動フォルダ>/artifacts/404-https.html evidence/<活動フォルダ>/artifacts/404-http.html 2>/dev/null | sort -uf | tee evidence/<活動フォルダ>/artifacts/404-versions.txt`。404-versions.txt に出たものは手順4 で CVE 照合に回る。バージョンが出なくても体裁（既定ページのままか・独自ページか）から製品を推定する。IIS/ASP.NET の詳細エラー画面に `ASP.NET Version:4.8.xxxx` が出ていれば .NET の版が特定できるので、手順4 の note の要領で手で引く
4. 手順2 の Server ヘッダ（headers-http.txt / headers-https.txt）・whatweb.json と手順3 の 404 本文（404-versions.txt）から「製品名 バージョン」を取り出し、製品ごとに NVD で CPE 名（CVE 照合のキー）を引く（例示の固定値ではなく、実際に検出した製品で引く）: `grep -hi '^server:' evidence/<活動フォルダ>/artifacts/headers-http.txt evidence/<活動フォルダ>/artifacts/headers-https.txt 2>/dev/null | tr -d '\r' | sed -E 's/^server: *//I' | grep -oE '[A-Za-z][A-Za-z0-9._-]*/[0-9][0-9A-Za-z._-]*' | tr '/' ' ' > evidence/<活動フォルダ>/artifacts/products-raw.txt; sed 's#/# #' evidence/<活動フォルダ>/artifacts/404-versions.txt >> evidence/<活動フォルダ>/artifacts/products-raw.txt 2>/dev/null; grep '^{' evidence/<活動フォルダ>/artifacts/whatweb.json 2>/dev/null | sed 's/,[[:space:]]*$//' | jq -rR 'fromjson? | .plugins // {} | to_entries[] | select(.value.version) | "\(.key) \(.value.version[0])"' >> evidence/<活動フォルダ>/artifacts/products-raw.txt; { sed -E 's/^Microsoft-IIS /Microsoft Internet Information Services /I; s/^Apache ([0-9])/Apache HTTP Server \1/I; /^ASP[._]NET /Id' evidence/<活動フォルダ>/artifacts/products-raw.txt; sed -nE 's/^openresty ([0-9]+\.[0-9]+\.[0-9]+).*/nginx \1/Ip' evidence/<活動フォルダ>/artifacts/products-raw.txt; } | sort -uf > evidence/<活動フォルダ>/artifacts/products.txt; cat evidence/<活動フォルダ>/artifacts/products.txt; > evidence/<活動フォルダ>/artifacts/nvd-cpe.tsv; grep -hi '^x-aspnet-version:' evidence/<活動フォルダ>/artifacts/headers-http.txt evidence/<活動フォルダ>/artifacts/headers-https.txt 2>/dev/null | tr -d '\r' | sed -E 's/^[^:]*: *//' | sort -u | while read -r av; do case "$av" in 4.0.30319*) r='.NET Framework 4.0〜4.8 のどれか（CLR 4 の共通値）';; 2.0.50727*) r='.NET Framework 2.0〜3.5 のどれか（CLR 2 の共通値）';; *) r='.NET Framework（版は要確認）';; esac; printf 'X-AspNet-Version %s\t照合せず: %s。版を特定できないので CVE は自動で引かない。ヘッダ自体をバージョン露出として finding にし、パッチ適用状況はヒアリングで確かめる\n' "$av" "$r"; done | tee -a evidence/<活動フォルダ>/artifacts/nvd-cpe.tsv; if [ ! -s evidence/<活動フォルダ>/artifacts/products.txt ]; then echo "CPE を引けるバージョン付きの製品名が取れていない（Server ヘッダ・whatweb・404 本文にバージョンが出ていない）。CVE 照合はしない。上に X-AspNet-Version の行があればそれはバージョン露出、無ければバージョン秘匿として記録する"; exit 0; fi; n=0; cat evidence/<活動フォルダ>/artifacts/products.txt | while read -r kw; do n=$((n+1)); [ $n -gt 1 ] && sleep 7; curl -s -m 30 --get --data-urlencode "keywordSearch=$kw" https://services.nvd.nist.gov/rest/json/cpes/2.0 -o evidence/<活動フォルダ>/artifacts/nvd-cpe-$n.json; if ! jq -e .products evidence/<活動フォルダ>/artifacts/nvd-cpe-$n.json >/dev/null 2>&1; then printf '%s\t取得失敗（NVD の 403=レート制限か通信エラー。30 秒おいて再実行）\n' "$kw"; continue; fi; jq -r --arg kw "$kw" --arg v ":${kw##* }:" '.products[] | select(.cpe.deprecated | not) | .cpe.cpeName | select(contains($v)) | select(split(":")[6] | . == "-" or . == "*") | select((split(":")[4] | split("_")) - ($kw | ascii_downcase | split(" ")) | length == 0) | "\($kw)\t\(.)"' evidence/<活動フォルダ>/artifacts/nvd-cpe-$n.json | head -3 | grep . || printf '%s\tCPE 0 件（note の言い換えで手で引き直す）\n' "$kw"; done | tee -a evidence/<活動フォルダ>/artifacts/nvd-cpe.tsv; if grep -q '取得失敗' evidence/<活動フォルダ>/artifacts/nvd-cpe.tsv; then echo "NVD から取得できなかった製品がある。30 秒おいてこの手順を再実行する" >&2; exit 4; fi`。products.txt が検出した製品、nvd-cpe.tsv が「製品→cpeName」（廃止済みの CPE と rc 等の先行版を除き、バージョンが一致し、CPE の製品名の語がすべて検索語に含まれるものを最大3件。nginx で nginx_unit を拾わないため）。openresty は nginx を同梱し版の先頭3桁が nginx の版なので（1.21.4.1 → nginx 1.21.4）、NVD で CVE が登録される nginx としても引く。バージョンが出ていなければ照合しない（バージョン秘匿として記録）。`X-AspNet-Version`（例: 4.0.30319）は .NET の CLR の版で、4.0〜4.8 のどれでも同じ値になり CPE を特定できないので、照合せず「ヘッダによるバージョン露出」として nvd-cpe.tsv に残す。`CPE 0 件` の製品は note の要領（製品名の言い換え・バージョンを粗く）で手で引き直す
   > ⚠️ **負荷注意（手順4）**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。超えると 403。製品ごとに 7 秒空けて引く（対象ではなく NVD への負荷）。
5. 手順4 で引いた cpeName ごとに既知 CVE を一覧する: `grep -oE 'cpe:2\.3:[^[:space:]]+' evidence/<活動フォルダ>/artifacts/nvd-cpe.tsv > evidence/<活動フォルダ>/artifacts/cpe-names.txt || { echo "照合する CPE が無い（手順4 の結果が バージョン不明 / CPE 0 件 のどちらかを確認）"; exit 0; }; n=0; cat evidence/<活動フォルダ>/artifacts/cpe-names.txt | while read -r cpe; do n=$((n+1)); sleep 7; curl -s -m 30 "https://services.nvd.nist.gov/rest/json/cves/2.0?virtualMatchString=$cpe&resultsPerPage=100" -o evidence/<活動フォルダ>/artifacts/nvd-cve-$n.json; if ! jq -e .vulnerabilities evidence/<活動フォルダ>/artifacts/nvd-cve-$n.json >/dev/null 2>&1; then printf '%s\t取得失敗（NVD の 403=レート制限か通信エラー。30 秒おいて再実行）\n' "$cpe"; continue; fi; printf '== %s\t%s 件\n' "$cpe" "$(jq -r .totalResults evidence/<活動フォルダ>/artifacts/nvd-cve-$n.json)"; jq -r '.vulnerabilities[].cve | [.id, (.metrics.cvssMetricV31[0].cvssData.baseScore // "-" | tostring), .descriptions[0].value[0:100]] | @tsv' evidence/<活動フォルダ>/artifacts/nvd-cve-$n.json | sort -t$'\t' -k2,2 -rn; done | tee evidence/<活動フォルダ>/artifacts/nvd-cve.tsv; if grep -q '取得失敗' evidence/<活動フォルダ>/artifacts/nvd-cve.tsv; then echo "NVD から取得できなかった CPE がある。30 秒おいてこの手順を再実行する" >&2; exit 4; fi`。nvd-cve.tsv に CVE-ID・CVSS v3.1 基本値・概要をスコア順で出す。CVSS 7.0 以上の CVE があれば、CVE-ID と「バージョンをどこで特定したか」（Server ヘッダ / whatweb）を finding に書く
   > ⚠️ **負荷注意（手順5）**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。CPE ごとに 7 秒空けて引く。403 で失敗したら 30 秒おいて再実行する。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順4**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。超えると 403。製品ごとに 7 秒空けて引く（対象ではなく NVD への負荷）。
- **手順5**: NVD API は API キー無しだと 30 秒あたり 5 リクエストまで。CPE ごとに 7 秒空けて引く。403 で失敗したら 30 秒おいて再実行する。

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
