# WSTG-INFO-04 — Enumerate Applications on Webserver

## 目的

同一ホスト・同一 IP 上に、対象アプリ以外のアプリや管理系インスタンスが同居していないかを洗い出す。

WSTG の Test Objectives:

- Enumerate the applications within scope that exist on a web server.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Approaches to Address Issue 1 - Non-standard URLs** — There is no way to fully ascertain the existence of non-standard-named web applications
2. **Approaches to Address Issue 2 - Non-standard Ports** — It is easy to check for the existence of web applications on non-standard ports
3. **Approaches to Address Issue 3 - Virtual Hosts** — There are a number of techniques which may be used to identify DNS names associated to a given IP address x.y.z.t.
4. **DNS Zone Transfers** — This technique has limited use nowadays, given the fact that zone transfers are largely not honored by DNS servers
5. **DNS Inverse Queries** — This process is similar to the previous one, but relies on inverse (PTR) DNS records
6. **Web-based DNS Searches** — This kind of search is akin to DNS zone transfer, but relies on web-based services that enable name-based searches on DNS
7. **Reverse-IP Services** — Reverse-IP services are similar to DNS inverse queries, with the difference that the testers query a web-based application instead of a name …

## 使用ツール

- DNS lookup tools such as nslookup, dig and similar.
- Search engines (Google, Bing and other major search engines).
- Specialized DNS-related web-based search service: see text.
- Nmap
- Nessus Vulnerability Scanner
- Nikto
- Watch
- Star

## 判定基準（pass / fail の見分け）

- **pass**: スコープ内ホストで公開されているアプリが、想定どおりのものだけ。
- **fail**: 想定外のアプリ（旧環境・検証環境・別部署のツール・管理コンソール）が同じホストで公開されている。
- 補足: 発見物が検査スコープ外なら、攻撃はせず「存在の報告」に留める。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/ffuf-paths.txt`, `cmd/ffuf-vhost.txt`, `artifacts/app-inventory.md`
- `covers:` — `{id: WSTG-INFO-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `enum-apps` — 仮想ホスト・パスの列挙

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/04-Enumerate_Applications_on_Webserver
