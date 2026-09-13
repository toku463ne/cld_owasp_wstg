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

1. `nmap -sV -p- target` で全ポートのサービスを洗い、Web 以外の管理系ポートも記録
2. 同一 IP の他ホストを `crt.sh`（証明書）とバーチャルホスト総当り（`ffuf -H "Host: FUZZ.target"`）で列挙
3. 見つかった各アプリのトップを開き、旧環境・検証環境・別部署ツール・管理コンソールを判別
4. スコープ外のものは攻撃せず「存在の報告」に留め、artifacts に一覧化

## 使用ツール

- nmap
- crt.sh
- ffuf

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
