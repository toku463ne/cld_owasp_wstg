# WSTG-INFO-03 — Review Webserver Metafiles for Information Leakage

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

1. **Robots** — Web Spiders, Robots, or Crawlers retrieve a web page and then recursively traverse hyperlinks to retrieve further web content
2. **Analyze robots.txt Using Google Webmaster Tools** — Web site owners can use the Google "Analyze robots.txt" function to analyze the website as part of its Google Webmaster Tools
3. **META Tags** — <META> tags are located within the HEAD section of each HTML document and should be consistent across a web site in the event that the robot …
4. **Robots META Tag** — If there is no <META NAME="ROBOTS" ..
5. **Miscellaneous META Information Tags** — Organizations often embed informational META tags in web content to support various technologies such as screen readers, social networking p …
6. **Sitemaps** — A sitemap is a file where a developer or organization can provide information about the pages, videos, and other files offered by the site o …
7. **Security TXT** — security.txt is a proposed standard which allows websites to define security policies and contact details

## 使用ツール

- Browser (View Source or Dev Tools functionality)
- curl
- wget
- Burp Suite
- ZAP
- Watch
- Star

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
