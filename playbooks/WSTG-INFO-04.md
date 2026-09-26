# WSTG-INFO-04 — Enumerate Applications on Webserver

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

同一ホスト・同一 IP 上に、対象アプリ以外のアプリや管理系インスタンスが同居していないかを洗い出す。

WSTG の Test Objectives:

- Enumerate the applications within scope that exist on a web server.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Web・管理系の主要ポートに curl で当て、応答するポートを記録する: `for pt in 80 443 81 591 2375 3000 5000 5601 7001 8000 8008 8080 8081 8088 8161 8443 8888 9000 9090 9200 9443 9990 10000 15672; do for sc in http https; do : > evidence/<活動フォルダ>/artifacts/_ph; r=$(curl -sk -m 5 -o /dev/null -D evidence/<活動フォルダ>/artifacts/_ph -w '%{http_code} %{http_connect}' "$sc://target:$pt/"); rc=$?; set -- $r; if [ "$1" != 000 ] && ! grep -qiE '^(x-squid-error|server: *squid)' evidence/<活動フォルダ>/artifacts/_ph; then echo "$pt/tcp open $sc $1 $(grep -i '^server:' evidence/<活動フォルダ>/artifacts/_ph | tail -1 | tr -d '\r')"; else echo "$pt/tcp noresp $sc curl=$rc connect=$2"; fi; done; done | tee evidence/<活動フォルダ>/artifacts/ports-http.txt; grep -q ' open ' evidence/<活動フォルダ>/artifacts/ports-http.txt || { echo "どのポートからも応答が無い＝対象に届いていない。プロキシ配下なら http_proxy/https_proxy が設定されているか確認する（curl -sI https://target/ で疎通確認）" >&2; exit 3; }`。`open` は応答あり、`noresp … connect=403` はプロキシの拒否で閉とは限らない
   > ⚠️ **負荷注意（手順1）**: 管理系ポート（Docker API 2375・Elasticsearch 9200 等）にも接続するので、IDS/IPS が反応しうる。リクエスト数は 24 ポート×http/https の 48 回程度。
2. 同一 IP の他ホストを列挙する。証明書透明性ログ（WSTG-INFO-01 の crt.sh）で既知の名前を拾い、バーチャルホスト総当りで応答するホスト名を洗う: `test -s "${WSTG_WORDLIST_VHOST:=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt}" || { echo "ワードリストが無い: $WSTG_WORDLIST_VHOST（sudo apt install -y seclists か export WSTG_WORDLIST_VHOST=/path/to/list）" >&2; exit 2; }; ffuf -w "$WSTG_WORDLIST_VHOST:FUZZ" ${WSTG_PAUSE:+-p "$WSTG_PAUSE" -t 1} ${https_proxy:+-x "$https_proxy"} -u https://target/ -H "Host: FUZZ.target" -ac -o evidence/<活動フォルダ>/artifacts/ffuf-vhost.json -of json`。残ったホスト名を手順3 の材料にする
   > ⚠️ **負荷注意（手順2）**: バーチャルホスト総当り（`ffuf -H "Host: FUZZ"`）はワードリストの大きさに比例して大量のリクエストを送る。リストを対象に合わせて絞る。
3. 見つけたホスト/ポートを evidence/<活動フォルダ>/artifacts/hosts.txt に1行1件で置き（手順1・2 の結果から）、用途判別の材料を一括取得: `test -s evidence/<活動フォルダ>/artifacts/hosts.txt || exit 75; while read -r hp; do echo "===== $hp ====="; curl -s -k -m 8 -D - -o evidence/<活動フォルダ>/artifacts/_body "https://$hp/" | grep -iE '^(HTTP/|server:|x-powered-by:|www-authenticate:)'; grep -oiE '<title>[^<]*' evidence/<活動フォルダ>/artifacts/_body | head -1; done < evidence/<活動フォルダ>/artifacts/hosts.txt | tee evidence/<活動フォルダ>/artifacts/vhosts-fingerprint.txt`。取得したタイトル・`Server`・realm と、`dev`/`stg`/`test`/`old`/`admin`/`jenkins`/`grafana`/`phpmyadmin` などのホスト名から用途（検証環境・管理コンソールの疑い）を判別し、各ホストの用途と根拠を artifacts/vhosts.md に1行ずつ書く
4. スコープ外のものは攻撃せず「存在の報告」に留め、artifacts に一覧化
5. 社外の端末から全ポートを nmap で走査する（手動）: `nmap -sV -Pn -p- --open -oN nmap-allports.txt target`。結果を evidence/<活動フォルダ>/artifacts/nmap-allports.txt に置き、スキャン元 IP・日時を観察欄に書く
   > ⚠️ **負荷注意（手順5）**: `nmap -p-` は全 65535 ポートへ接続を試みる重いスキャン。IDS/IPS や機器の接続数上限を刺激しうる。時間帯に注意し、詰まるなら `--max-rate 100` や `-T2` で抑える（`--scan-delay` は `-p-` だと事実上終わらないので使わない）。社外 IP からのスキャンなので、スキャン元 IP を対象の管理者に事前に伝える。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: 管理系ポート（Docker API 2375・Elasticsearch 9200 等）にも接続するので、IDS/IPS が反応しうる。リクエスト数は 24 ポート×http/https の 48 回程度。
- **手順2**: バーチャルホスト総当り（`ffuf -H "Host: FUZZ"`）はワードリストの大きさに比例して大量のリクエストを送る。リストを対象に合わせて絞る。
- **手順5**: `nmap -p-` は全 65535 ポートへ接続を試みる重いスキャン。IDS/IPS や機器の接続数上限を刺激しうる。時間帯に注意し、詰まるなら `--max-rate 100` や `-T2` で抑える（`--scan-delay` は `-p-` だと事実上終わらないので使わない）。社外 IP からのスキャンなので、スキャン元 IP を対象の管理者に事前に伝える。

## 使用ツール

- curl
- crt.sh
- ffuf
- nmap

## 判定基準（pass / fail の見分け）

- **pass**: スコープ内ホストで公開されているアプリが、想定どおりのものだけ。
- **fail**: 想定外のアプリ（旧環境・検証環境・別部署のツール・管理コンソール）が同じホストで公開されている。
- 補足: 発見物が検査スコープ外なら、攻撃はせず「存在の報告」に留める。手順1 はプロキシ経由なので HTTP を話すポートしか確かめられない（Squid は既定で 443 以外への CONNECT を拒否。Squid 以外のプロキシの 502/503/504 は open に見えるので Server 欄で除外）。SSH/RDP/DB は手順5 の社外 nmap で押さえる（WSTG-CONF-01/05 が読む。CONF-01 手順1 は置いたあと手で実行する）。スキャン元 IP は対象の管理者に事前に伝え、全ポート filtered なら到達できていないので判定に使わない。手順2 の ffuf: `-ac` で既定応答を除外。ワードリストは既定で SecLists 上位 5000 件（`export WSTG_WORDLIST_VHOST=<パス>` で差し替え）、非力な対象は `export WSTG_PAUSE=2`、ffuf は環境変数のプロキシを見ないので `-x` を付けてある。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/ffuf-paths.txt`, `cmd/ffuf-vhost.txt`, `artifacts/ports-http.txt`, `artifacts/nmap-allports.txt`, `artifacts/app-inventory.md`
- `covers:` — `{id: WSTG-INFO-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `enum-apps` — 仮想ホスト・パスの列挙

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Enumerate_Applications_on_Webserver
