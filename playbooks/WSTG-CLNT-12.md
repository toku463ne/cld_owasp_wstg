# WSTG-CLNT-12 — Testing Browser Storage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ブラウザストレージに機微情報が残っていないかを確認する。

WSTG の Test Objectives:

- Determine whether the website is storing sensitive data in client-side storage.
- The code handling of the storage objects should be examined for possibilities of injection attacks, such as utilizing unvalidated input or vulnerable libraries.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ブラウザ開発者ツール→Application で localStorage/sessionStorage/IndexedDB/Cookie の中身を確認
2. セッショントークン・個人情報・機微データが平文で保存されていないか確認
3. 保存データが XSS で読める（HttpOnly でない）・信頼して処理される経路がないか確認
4. 機微データのクライアント保存を finding に（保存の是非と保護の両面で）

## 使用ツール

- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: localStorage/sessionStorage/IndexedDB に資格情報・トークン・個人情報を保存していない。
- **fail**: アクセストークンや個人情報が localStorage に平文で保存され、XSS で持ち出せる。
- 補足: ログアウト後にストレージが消えるかも確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-12, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/12-Testing_Browser_Storage
