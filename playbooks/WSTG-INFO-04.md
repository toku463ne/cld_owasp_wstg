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

1. Web・管理系でよく使うポートに http/https で当て、応答するポートとその Server ヘッダを記録する（ポートスキャナはプロキシを通らないため curl で取る。README「プロキシ配下での準備」。この結果は WSTG-CONF-01・WSTG-CONF-05 でも使い回す）: `for pt in 80 443 81 591 2375 3000 5000 5601 7001 8000 8008 8080 8081 8088 8161 8443 8888 9000 9090 9200 9443 9990 10000 15672; do for sc in http https; do : > evidence/<活動フォルダ>/artifacts/_ph; r=$(curl -sk -m 5 -o /dev/null -D evidence/<活動フォルダ>/artifacts/_ph -w '%{http_code} %{http_connect}' "$sc://target:$pt/"); rc=$?; set -- $r; if [ "$1" != 000 ] && ! grep -qiE '^(x-squid-error|server: *squid)' evidence/<活動フォルダ>/artifacts/_ph; then echo "$pt/tcp open $sc $1 $(grep -i '^server:' evidence/<活動フォルダ>/artifacts/_ph | tail -1 | tr -d '\r')"; else echo "$pt/tcp noresp $sc curl=$rc connect=$2"; fi; done; done | tee evidence/<活動フォルダ>/artifacts/ports-http.txt; grep -q ' open ' evidence/<活動フォルダ>/artifacts/ports-http.txt || { echo "どのポートからも応答が無い＝対象に届いていない。プロキシ配下なら http_proxy/https_proxy が設定されているか確認する（curl -sI https://target/ で疎通確認）" >&2; exit 3; }`。`open` 行が応答したポート（HTTP の応答コードと Server）。`noresp` のうち `connect=403` 等はプロキシが CONNECT を拒否したもの（Squid の既定は 443 以外への CONNECT を拒否）で、閉じているとは限らない。プロキシ経由で確かめられるのは HTTP を話すポートだけで、SSH/RDP/DB などは手順5 の社外からの nmap で押さえる。Squid 以外のプロキシが返すエラー（502/503/504）は open に見えるので、Server 欄がプロキシのものなら除外する
   > ⚠️ **負荷注意（手順1）**: 管理系ポート（Docker API 2375・Elasticsearch 9200 等）にも接続するので、IDS/IPS が反応しうる。リクエスト数は 24 ポート×http/https の 48 回程度。
2. 同一 IP の他ホストを列挙する。まず証明書透明性ログから既知の名前を拾う（手順は WSTG-INFO-02 の crt.sh 参照）。次にバーチャルホスト総当りで応答するホスト名を洗う: `test -s "${WSTG_WORDLIST_VHOST:=/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt}" || { echo "ワードリストが無い: $WSTG_WORDLIST_VHOST（sudo apt install -y seclists か export WSTG_WORDLIST_VHOST=/path/to/list）" >&2; exit 2; }; ffuf -w "$WSTG_WORDLIST_VHOST:FUZZ" ${WSTG_PAUSE:+-p "$WSTG_PAUSE" -t 1} ${https_proxy:+-x "$https_proxy"} -u https://target/ -H "Host: FUZZ.target" -ac -o evidence/<活動フォルダ>/artifacts/ffuf-vhost.json -of json`。`-ac`（自動キャリブレーション）で既定応答を除外し、残ったホスト名を手順3の材料にする。ワードリストは既定で SecLists の上位 5000 件（`sudo apt install seclists`）。対象に合わせて絞るときは `export WSTG_WORDLIST_VHOST=<パス>`。非力な対象では `export WSTG_PAUSE=2` で待ち＋スレッド1に落とす。ffuf は環境変数のプロキシを見ないので、プロキシ経由なら `-x` を明示する
   > ⚠️ **負荷注意（手順2）**: バーチャルホスト総当り（`ffuf -H "Host: FUZZ"`）はワードリストの大きさに比例して大量のリクエストを送る。リストを対象に合わせて絞る。
3. 見つけたホスト/ポートを evidence/<活動フォルダ>/artifacts/hosts.txt に1行1件で置き（手順1・2 の結果から）、用途判別の材料を一括取得（hosts.txt を置くまで一括実行では「入力待ち」で飛ばす）: `test -s evidence/<活動フォルダ>/artifacts/hosts.txt || exit 75; while read -r hp; do echo "===== $hp ====="; curl -s -k -m 8 -D - -o evidence/<活動フォルダ>/artifacts/_body "https://$hp/" | grep -iE '^(HTTP/|server:|x-powered-by:|www-authenticate:)'; grep -oiE '<title>[^<]*' evidence/<活動フォルダ>/artifacts/_body | head -1; done < evidence/<活動フォルダ>/artifacts/hosts.txt | tee evidence/<活動フォルダ>/artifacts/vhosts-fingerprint.txt`。取得したタイトル・`Server`・realm と、`dev`/`stg`/`test`/`old`/`admin`/`jenkins`/`grafana`/`phpmyadmin` などのホスト名から用途（検証環境・管理コンソールの疑い）を判別し、各ホストの用途と根拠を artifacts/vhosts.md に1行ずつ書く
4. スコープ外のものは攻撃せず「存在の報告」に留め、artifacts に一覧化
5. 社外の端末（社内プロキシを通らず対象に直結できる検査用 VPS 等）から全ポートを手動で走査する。社内プロキシは SSH/RDP/DB 宛の CONNECT を許可しないので、手順1 の curl では HTTP 以外のポートを確かめられない: `nmap -sV -Pn -p- --open -oN nmap-allports.txt target`。できた nmap-allports.txt をこのフォルダの artifacts/ にそのまま置く（WSTG-CONF-01・WSTG-CONF-05 が読む。置くまで WSTG-CONF-01 の手順1・2 は「入力待ち」）。スキャン元の IP・実施日時・nmap のバージョンを artifacts/manual-WSTG-INFO-04-s5.txt に書き、スキャン元 IP は対象の管理者に事前に伝えておく（WAF/IDS に遮断されると全ポート filtered になる）。全ポート filtered・0 件なら到達できていないので、その旨を書いて判定に使わない
   > ⚠️ **負荷注意（手順5）**: `nmap -p-` は全 65535 ポートへ接続を試みる重いスキャン。IDS/IPS や機器の接続数上限を刺激しうる。時間帯に注意し、詰まるなら `--max-rate 100` や `-T2` で抑える（`--scan-delay` は `-p-` だと事実上終わらないので使わない）。社外 IP からのスキャンなので、スキャン元 IP を対象の管理者に事前に伝える。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: 管理系ポート（Docker API 2375・Elasticsearch 9200 等）にも接続するので、IDS/IPS が反応しうる。リクエスト数は 24 ポート×http/https の 48 回程度。
- **手順2**: バーチャルホスト総当り（`ffuf -H "Host: FUZZ"`）はワードリストの大きさに比例して大量のリクエストを送る。リストを対象に合わせて絞る。
- **手順5**: `nmap -p-` は全 65535 ポートへ接続を試みる重いスキャン。IDS/IPS や機器の接続数上限を刺激しうる。時間帯に注意し、詰まるなら `--max-rate 100` や `-T2` で抑える（`--scan-delay` は `-p-` だと事実上終わらないので使わない）。社外 IP からのスキャンなので、スキャン元 IP を対象の管理者に事前に伝える。

## 使用ツール

- curl
- nmap
- crt.sh
- ffuf

## 判定基準（pass / fail の見分け）

- **pass**: スコープ内ホストで公開されているアプリが、想定どおりのものだけ。
- **fail**: 想定外のアプリ（旧環境・検証環境・別部署のツール・管理コンソール）が同じホストで公開されている。
- 補足: 発見物が検査スコープ外なら、攻撃はせず「存在の報告」に留める。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/ffuf-paths.txt`, `cmd/ffuf-vhost.txt`, `artifacts/ports-http.txt`, `artifacts/nmap-allports.txt`, `artifacts/app-inventory.md`
- `covers:` — `{id: WSTG-INFO-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `enum-apps` — 仮想ホスト・パスの列挙

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Enumerate_Applications_on_Webserver
