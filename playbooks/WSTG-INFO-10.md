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

1. `curl -sI` の応答ヘッダ（`Via`/`X-Cache`/`Server`/`Set-Cookie` の LB 印）から中間装置を推定
2. `traceroute`／TTL・応答差から WAF・CDN・リバースプロキシの有無を判断（WAF は不正入力への 403/406 で炙り出す）
3. サブドメイン・ポートから API GW・キャッシュ・DB 管理画面が外部露出していないか確認
4. 推定した構成図を描き、ヒアリング結果と突き合わせて確定（推測のまま報告しない）

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
