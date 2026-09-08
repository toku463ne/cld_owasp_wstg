# WSTG-INFO-10 — Map Application Architecture

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

WAF・LB・リバースプロキシ・API GW・DB など、経路上の構成要素を推定する。

WSTG の Test Objectives:

- Generate a map of the application at hand based on the research conducted.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. The application architecture needs to be mapped through some test to determine what different components are used to build the web application.
2. On more complex setups, such as an online bank system, multiple servers might be involved. These may include a reverse proxy, a front-end web server, an application server, and a database se …
3. Getting knowledge of the application architecture can be easy if this information is provided to the testing team by the application developers in document form or through interviews, but ca …
4. In the latter case, a tester will first start with the assumption that there is a simple setup (a single server).
5. Detecting a reverse proxy in front of the web server can be done by analysis of the web server banner, which might directly disclose the existence of a reverse proxy.
6. In some cases, even the protection system gives itself away. Here's an example of mod_security self identifying:
7. Figure 4.1.10-1: Example mod_security Error Page

## 使用ツール

- Burp Suite
- OWASP ZAP

## 判定基準（pass / fail の見分け）

- **pass**: 構成が把握でき、防御機構（WAF 等）の有無と位置を説明できる。
- **fail**: 本来内部にあるべき構成要素（管理系 API・キャッシュ・DB 管理画面）が外部から直接見えている。
- 補足: 構成推定はヒアリングと突き合わせる。推測のまま報告しない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/entry-points.txt`, `artifacts/sitemap.xml`, `notes.md`
- `covers:` — `{id: WSTG-INFO-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/10-Map_Application_Architecture
