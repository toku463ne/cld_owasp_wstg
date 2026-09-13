# WSTG-ATHN-06 — Testing for Browser Cache Weaknesses

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

認証済み画面がブラウザキャッシュに残り、後から閲覧されないかを確認する。

WSTG の Test Objectives:

- Review if the application stores sensitive information on the client-side.
- Review if access can occur without authorization.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 認証済み画面のレスポンスヘッダを `curl -sI`/Burp で取得し `Cache-Control: no-store` / `Pragma: no-cache` の有無を確認
2. ログアウト後にブラウザの「戻る」で認証済み画面が再表示されないか確認
3. ブラウザキャッシュ（ディスク上）に機微画面が残っていないか確認
4. 機微画面でキャッシュ抑止がない場合、共用端末での漏えいリスクとして finding に

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 機微画面の応答に Cache-Control: no-store（必要なら no-cache, must-revalidate）が付いている。
- **fail**: 認証後の画面がキャッシュされ、ログアウト後に戻るボタンや履歴から内容を再表示できる。
- 補足: 実機で「ログアウト→戻る」を試すのが最も伝わる証拠になる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`, `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）
- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/06-Testing_for_Browser_Cache_Weaknesses
