# WSTG-INFO-03 — Review Webserver Metafiles for Information Leakage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

robots.txt・sitemap・security.txt・.well-known 配下から情報が漏れていないかを確認する。

WSTG の Test Objectives:

- Identify hidden or obfuscated paths and functionality through the analysis of metadata files.
- Extract and map other information that could lead to better understanding of the systems at hand.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `curl -s https://target/robots.txt` `sitemap.xml` `.well-known/security.txt` を取得
2. `curl -s https://target/.well-known/` 配下、`humans.txt`、`crossdomain.xml` も確認
3. robots.txt の Disallow 行を1件ずつブラウザ/ curl で開き、非公開領域を指していないか見る
4. sitemap に載る URL を認証なしで開き、非公開のはずの画面が列挙されていないか確認

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: メタファイルに非公開領域のパスや内部情報が書かれていない。
- **fail**: robots.txt の Disallow が管理画面・バックアップ等の場所を教えている、または sitemap に非公開 URL が載っている。
- 補足: Disallow はクロール抑止であってアクセス制御ではない、という説明を必ず添える。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-robots.txt`, `cmd/curl-wellknown.txt`, `artifacts/comments-grep.txt`
- `covers:` — `{id: WSTG-INFO-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `metafiles-crawl` — メタファイル・公開コンテンツの収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/03-Review_Webserver_Metafiles_for_Information_Leakage
