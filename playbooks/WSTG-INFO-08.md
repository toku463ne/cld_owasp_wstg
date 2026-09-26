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

1. フレームワーク/CMS は WSTG-INFO-02 手順2 で取得済みの whatweb.json から読む（whatweb を再実行しない）: `test -s evidence/<活動フォルダ>/artifacts/whatweb.json || { echo "whatweb.json が無い。先に WSTG-INFO-02 を回す" >&2; exit 2; }; grep '^{' evidence/<活動フォルダ>/artifacts/whatweb.json 2>/dev/null | sed 's/,[[:space:]]*$//' | jq -rR 'fromjson? | .plugins // {} | keys[]' | sort -u` ＋ ブラウザ拡張 Wappalyzer で突き合わせる。単独実行で whatweb.json が無いときは先に WSTG-INFO-02 を回す。whatweb.json は1件1行の JSON として読むので、以前の実行で追記されて壊れたファイルでも読める
2. 応答ヘッダと Cookie を保存して基盤を推定: `curl -sD evidence/<活動フォルダ>/artifacts/headers.txt -o /dev/null https://target/ && { grep -iE '^(set-cookie|x-powered-by|server|x-aspnet-version|x-generator):' evidence/<活動フォルダ>/artifacts/headers.txt || [ $? -eq 1 ]; }`。Cookie 名（`JSESSIONID`=Java / `ASP.NET_SessionId`=.NET / `laravel_session`=Laravel / `ci_session`=CodeIgniter）・`X-Powered-By`・URL パスから基盤を特定
3. 対象ページが読み込むフロント JS をブラウザ（開発者ツール）や Burp で保存して artifacts/js/ に置き、`test -n "$(ls -A evidence/<活動フォルダ>/artifacts/js/ 2>/dev/null)" || exit 75; retire --path evidence/<活動フォルダ>/artifacts/js/ --outputformat json --outputpath evidence/<活動フォルダ>/artifacts/retire.json --exitwith 0`（Retire.js）で走査して jQuery 等ライブラリのバージョンと既知脆弱性を確認する。retire は脆弱性を見つけると既定で exit 13 を返し一括実行が止まるため `--exitwith 0` で抑え、結果は retire.json で判断する。artifacts/js/ が空なら「入力待ち」（exit 75）として一括処理を止めずに飛ばす。JS を置いた後に同じ run_target を再実行するか `uv run scripts/run_activity.py <このフォルダ> --only WSTG-INFO-08:3` で走らせる
4. CMS・フレームワークの CVE 照合は WSTG-INFO-02 手順4・5 が whatweb の検出分（WordPress・PHP 等）もまとめて引いている（products.txt・nvd-cpe.tsv・nvd-cve.tsv）。NVD を二重に叩かず、手順1・2 で特定したものの行をそこから読む
5. whatweb に出ず手順2（Cookie・パス）や Wappalyzer でだけ特定できたものは、WSTG-INFO-02 の note の要領で手で引く（cpes/2.0 に keywordSearch=製品名 バージョン → 得た cpeName で cves/2.0 に virtualMatchString）。finding にバージョン根拠（どこで判ったか）を添える
   > ⚠️ **負荷注意（手順5）**: NVD API はキー無しで 30 秒 5 リクエストまで（超過は 403）。手で続けて引くときは間隔を空ける。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順5**: NVD API はキー無しで 30 秒 5 リクエストまで（超過は 403）。手で続けて引くときは間隔を空ける。

## 使用ツール

- whatweb
- jq
- Wappalyzer
- curl
- ブラウザ開発者ツール
- Burp Suite
- Retire.js

## 判定基準（pass / fail の見分け）

- **pass**: 使用フレームワークが特定できない、または特定できても既知脆弱性のないバージョン。
- **fail**: 既知脆弱性のあるバージョンのフレームワーク・ライブラリを使用している（Cookie 名・パス・ヘッダ・JS から特定）。
- 補足: フロント側のライブラリ（jQuery 等）は Retire.js で確認できる。Retire.js は実行時に github から脆弱性DB（jsrepository.json）を取りに行くため、プロキシ必須／外向き通信が絞られた環境では更新に失敗することがある（amass の libpostal と同じ構図）。`--path` は既にダウンロード済みのローカル JS を走査するので、DB さえ取得できれば対象への通信は不要。更新できないときは事前に DB を取得しておくか、下の NVD API での照合に回す。CMS・フレームワーク側の CVE 照合はブラウザ不要で、NVD の cpes/2.0（製品名+バージョン → cpeName）→ cves/2.0（cpeName → CVE 一覧）を curl で引く（API キー無しは 30 秒 5 リクエストまで。0 件の読み替えは WSTG-INFO-02 の note と同じ）。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/headers-http.txt`, `artifacts/headers-https.txt`, `artifacts/whatweb.json`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/08-Fingerprint_Web_Application_Framework
