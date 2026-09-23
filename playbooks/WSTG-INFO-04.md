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

1. `nmap -sV -p- -oN evidence/<活動フォルダ>/artifacts/nmap-allports.txt target` で全ポートのサービスを洗い、Web 以外の管理系ポートも記録
   > ⚠️ **負荷注意（手順1）**: `nmap -p-` は全 65535 ポートへ接続を試みる重いスキャン。IDS/IPS や機器の接続数上限を刺激しうる。時間帯に注意し、詰まるなら `--max-rate` で抑える。内部網でも想定外の機器（産業機器・古い装置）が落ちることがある。
2. 同一 IP の他ホストを `crt.sh`（証明書）とバーチャルホスト総当り（`ffuf -H "Host: FUZZ.target"`）で列挙
   > ⚠️ **負荷注意（手順2）**: バーチャルホスト総当り（`ffuf -H "Host: FUZZ"`）はワードリストの大きさに比例して大量のリクエストを送る。リストを対象に合わせて絞る。
3. 見つけたホスト/ポートを evidence/<活動フォルダ>/artifacts/hosts.txt に1行1件で置き（手順1・2 の結果から）、用途判別の材料を一括取得: `while read -r hp; do echo "===== $hp ====="; curl -s -k -m 8 -D - -o evidence/<活動フォルダ>/artifacts/_body "https://$hp/" | grep -iE '^(HTTP/|server:|x-powered-by:|www-authenticate:)'; grep -oiE '<title>[^<]*' evidence/<活動フォルダ>/artifacts/_body | head -1; done < evidence/<活動フォルダ>/artifacts/hosts.txt | tee evidence/<活動フォルダ>/artifacts/vhosts-fingerprint.txt`。取得したタイトル・`Server`・realm と、`dev`/`stg`/`test`/`old`/`admin`/`jenkins`/`grafana`/`phpmyadmin` などのホスト名から用途（検証環境・管理コンソールの疑い）を判別し、各ホストの用途と根拠を artifacts/vhosts.md に1行ずつ書く
4. スコープ外のものは攻撃せず「存在の報告」に留め、artifacts に一覧化

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: `nmap -p-` は全 65535 ポートへ接続を試みる重いスキャン。IDS/IPS や機器の接続数上限を刺激しうる。時間帯に注意し、詰まるなら `--max-rate` で抑える。内部網でも想定外の機器（産業機器・古い装置）が落ちることがある。
- **手順2**: バーチャルホスト総当り（`ffuf -H "Host: FUZZ"`）はワードリストの大きさに比例して大量のリクエストを送る。リストを対象に合わせて絞る。

## 使用ツール

- nmap
- crt.sh
- ffuf
- curl

## 判定基準（pass / fail の見分け）

- **pass**: スコープ内ホストで公開されているアプリが、想定どおりのものだけ。
- **fail**: 想定外のアプリ（旧環境・検証環境・別部署のツール・管理コンソール）が同じホストで公開されている。
- 補足: 発見物が検査スコープ外なら、攻撃はせず「存在の報告」に留める。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/ffuf-paths.txt`, `cmd/ffuf-vhost.txt`, `artifacts/app-inventory.md`
- `covers:` — `{id: WSTG-INFO-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `enum-apps` — 仮想ホスト・パスの列挙

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Enumerate_Applications_on_Webserver
