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

1. ブラウザで対象ページを開き、Ctrl+U（ソース表示）で HTML コメント `<!-- -->` を確認
2. 開発者ツール→Sources で読み込まれる JS を一覧し、`grep -iE "password|apikey|token|internal|todo|debug"` 相当で走査
3. minify JS の `//# sourceMappingURL` を辿り `.map` を取得、原本コードにコメント/内部情報が無いか見る
4. `<meta>`・生成コメント（CMS 名・バージョン）・非公開エンドポイントの記述を記録

## 使用ツール

- ブラウザ
- ブラウザ開発者ツール

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
