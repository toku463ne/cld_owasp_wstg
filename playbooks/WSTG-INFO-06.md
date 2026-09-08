# WSTG-INFO-06 — Identify Application Entry Points

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

アプリが受け付ける入力点（URL・パラメータ・ヘッダ・Cookie・ファイル）を漏れなく列挙し、以降のテストの土台にする。

WSTG の Test Objectives:

- Identify possible entry and injection points through request and response analysis.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Requests** — Identify where GETs are used and where POSTs are used.
2. **Responses** — Identify where new cookies are set (Set-Cookie header), modified, or added to.
3. **Black-Box Testing**
4. **Testing for Application Entry Points** — The following are two examples on how to check for application entry points.
5. **Gray-Box Testing** — Testing for application entry points via a gray-box methodology would consist of everything already identified above with one addition
6. **OWASP Attack Surface Detector** — The Attack Surface Detector (ASD) tool investigates the source code and uncovers the endpoints of a web application, the parameters these en …

## 使用ツール

- OWASP Zed Attack Proxy (ZAP)
- Burp Suite
- Fiddler

## 判定基準（pass / fail の見分け）

- **pass**: 入力点の一覧が作成でき、後続テストで参照できる状態になっている（このテスト自体は原則 info/pass）。
- **fail**: 認証が必要なはずのエントリポイントに未認証で到達できる等、列挙の過程で明確な問題が見つかった場合。
- 補足: 判定より網羅性が目的。認証済み・未認証の両方でクロールしないと漏れる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/entry-points.txt`, `artifacts/sitemap.xml`, `notes.md`, `cmd/ffuf-paths.txt`, `cmd/ffuf-vhost.txt`
- `covers:` — `{id: WSTG-INFO-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し
- `enum-apps` — 仮想ホスト・パスの列挙

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/06-Identify_Application_Entry_Points
