# WSTG-INFO-05 — Review Webpage Content for Information Leakage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

HTML コメント・JS・メタデータに、開発時の情報が残っていないかを確認する。

WSTG の Test Objectives:

- Review webpage comments and metadata to find any information leakage.
- Gather JavaScript files and review the JS code to better understand the application and to find any information leakage.
- Identify if source map files or other front-end debug files exist.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Review webpage comments and metadata** — HTML comments are often used by the developers to include debugging information about the application
2. **Identifying JavaScript Code and Gathering JavaScript Files** — Programmers often hardcode sensitive information with JavaScript variables on the front-end
3. **Identifying Source Map Files** — Source map files will usually be loaded when DevTools open
4. **Black-Box Testing** — Check source map files for any sensitive information that can help the attacker gain more insight about the application

## 使用ツール

- Wget
- Browser "view source" function
- Eyeballs
- Curl
- Burp Suite
- Waybackurls
- Google Maps API Scanner

## 判定基準（pass / fail の見分け）

- **pass**: コメントや JS に資格情報・内部 IP・未公開エンドポイント・開発メモがない。
- **fail**: ソース中に API キー・パスワード・内部ホスト名・デバッグ用エンドポイントが含まれる。
- 補足: minify 済み JS の source map（.map）も確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-robots.txt`, `cmd/curl-wellknown.txt`, `artifacts/comments-grep.txt`, `artifacts/error-samples.md`, `cmd/curl-errors.txt`
- `covers:` — `{id: WSTG-INFO-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `metafiles-crawl` — メタファイル・公開コンテンツの収集
- `error-handling-review` — エラーハンドリングのレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/05-Review_Webpage_Content_for_Information_Leakage
