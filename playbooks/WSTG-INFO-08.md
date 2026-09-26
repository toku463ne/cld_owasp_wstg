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

1. WSTG-INFO-02 の whatweb.json からフレームワーク/CMS を一覧する: `test -s evidence/<活動フォルダ>/artifacts/whatweb.json || { echo "whatweb.json が無い。先に WSTG-INFO-02 を回す" >&2; exit 2; }; grep '^{' evidence/<活動フォルダ>/artifacts/whatweb.json 2>/dev/null | sed 's/,[[:space:]]*$//' | jq -rR 'fromjson? | .plugins // {} | keys[]' | sort -u | tee evidence/<活動フォルダ>/artifacts/whatweb-plugins.txt`。結果は whatweb-plugins.txt
2. ブラウザ拡張 Wappalyzer で技術スタックを確認する（手動）: Chrome/Firefox に Wappalyzer 拡張を入れる → 対象のトップとログイン後の主要画面を開き、ツールバーの Wappalyzer アイコンをクリック → 表示された製品名とバージョン（例: jQuery 1.8.1、ASP.NET）を観察欄に書き、手順1 の一覧と突き合わせる
3. 応答ヘッダと Cookie を保存して基盤を推定: `curl -sD evidence/<活動フォルダ>/artifacts/headers.txt -o /dev/null https://target/ && { grep -iE '^(set-cookie|x-powered-by|server|x-aspnet-version|x-generator):' evidence/<活動フォルダ>/artifacts/headers.txt || [ $? -eq 1 ]; }`。Cookie 名（`JSESSIONID`=Java / `ASP.NET_SessionId`=.NET / `laravel_session`=Laravel / `ci_session`=CodeIgniter）・`X-Powered-By`・URL パスから基盤を特定
4. ブラウザで対象の通信を HAR に記録する（手動）: F12 で開発者ツールを開く → Network タブの「Preserve log」に✓ → Ctrl+Shift+R で再読み込みし、ログイン画面・主要画面も一通り開く → 一覧を右クリック →「Save all as HAR」（Firefox は「すべてを HAR 形式で保存」）→ evidence/<活動フォルダ>/artifacts/site.har として保存
5. 手順4 の HAR に記録された JS を取得し、Retire.js で既知脆弱性を確認する: `test -s evidence/<活動フォルダ>/artifacts/site.har || exit 75; mkdir -p evidence/<活動フォルダ>/artifacts/js; jq -r '.log.entries[] | select((.response.content.mimeType // "") | test("javascript|ecmascript")) | .request.url' evidence/<活動フォルダ>/artifacts/site.har | sort -u | tee evidence/<活動フォルダ>/artifacts/js-urls.txt | while read -r u; do f=$(printf '%s' "$u" | sed -E 's|^[a-z]+://||; s|[?#].*$||; s|[^A-Za-z0-9._-]|_|g'); case "$f" in *.js) ;; *) f="$f.js";; esac; curl -sk -m 30 -o "evidence/<活動フォルダ>/artifacts/js/$f" "$u"; done; retire --path evidence/<活動フォルダ>/artifacts/js/ --outputformat json --outputpath evidence/<活動フォルダ>/artifacts/retire.json --exitwith 0; jq -r '.data[]? | (.file | sub(".*/"; "")) as $f | .results[]? | select((.vulnerabilities // []) | length > 0) | [.component + " " + .version, ([.vulnerabilities[].severity] | unique | join(",")), ([.vulnerabilities[].identifiers.CVE[]?] | unique | join(" ")), $f] | @tsv' evidence/<活動フォルダ>/artifacts/retire.json | tee evidence/<活動フォルダ>/artifacts/retire-summary.tsv; echo "走査した JS: $(ls evidence/<活動フォルダ>/artifacts/js/ | wc -l) 件 / 既知脆弱性のあるライブラリ: $(grep -c . evidence/<活動フォルダ>/artifacts/retire-summary.tsv) 件"`。retire-summary.tsv に「ライブラリ 版・深刻度・CVE・ファイル」が出る
6. CMS・フレームワークの CVE 照合は WSTG-INFO-02 手順4・5 が whatweb の検出分（WordPress・PHP 等）もまとめて引いている（products.txt・nvd-cpe.tsv・nvd-cve.tsv）。NVD を二重に叩かず、手順1・2 で特定したものの行をそこから読む
7. whatweb に出ず手順2（Wappalyzer）や手順3（Cookie・パス）でだけ特定できたものは、WSTG-INFO-02 の note の要領で手で引く（cpes/2.0 に keywordSearch=製品名 バージョン → 得た cpeName で cves/2.0 に virtualMatchString）。finding にバージョン根拠（どこで判ったか）を添える
   > ⚠️ **負荷注意（手順7）**: NVD API はキー無しで 30 秒 5 リクエストまで（超過は 403）。手で続けて引くときは間隔を空ける。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順7**: NVD API はキー無しで 30 秒 5 リクエストまで（超過は 403）。手で続けて引くときは間隔を空ける。

## 使用ツール

- whatweb
- jq
- Wappalyzer
- curl
- ブラウザ
- ブラウザ開発者ツール
- Retire.js

## 判定基準（pass / fail の見分け）

- **pass**: 使用フレームワークが特定できない、または特定できても既知脆弱性のないバージョン。
- **fail**: 既知脆弱性のあるバージョンのフレームワーク・ライブラリを使用している（Cookie 名・パス・ヘッダ・JS から特定）。
- 補足: フロント側のライブラリ（jQuery 等）は Retire.js で確認できる。Retire.js は実行時に github から脆弱性DB（jsrepository.json）を取りに行くため、プロキシ必須／外向き通信が絞られた環境では更新に失敗することがある（amass の libpostal と同じ構図）。`--path` は既にダウンロード済みのローカル JS を走査するので、DB さえ取得できれば対象への通信は不要。更新できないときは事前に DB を取得しておくか、下の NVD API での照合に回す。CMS・フレームワーク側の CVE 照合はブラウザ不要で、NVD の cpes/2.0（製品名+バージョン → cpeName）→ cves/2.0（cpeName → CVE 一覧）を curl で引く（API キー無しは 30 秒 5 リクエストまで。0 件の読み替えは WSTG-INFO-02 の note と同じ）。whatweb は再実行せず WSTG-INFO-02 の結果を読む（無ければ先に INFO-02 を回す。1件1行で読むので追記で壊れたファイルも読める）。手順4 の HAR は Chrome/Edge/Firefox の開発者ツールで保存できる（Burp の内蔵ブラウザも F12 で同じ）。HAR には Cookie・トークンも入るので evidence の外に出さない。手順5 は HAR の URL から JS を取り直す（認証が要る JS は取れないことがあるので、js-urls.txt と走査件数を見比べる）。retire は脆弱性を見つけると exit 13 で一括が止まるので `--exitwith 0` で抑え、判断は retire.json / retire-summary.tsv で。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/headers-http.txt`, `artifacts/headers-https.txt`, `artifacts/whatweb.json`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/08-Fingerprint_Web_Application_Framework
