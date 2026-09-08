# WSTG-CLNT-12 — Testing Browser Storage

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

1. **Local Storage** — window.localStorage is a global property that implements the Web Storage API and provides persistent key-value storage in the browser.
2. **List All Key-Value Entries** — `for (let i = 0; i < localStorage.length; i++) { const key = localStorage.key(i); const value = localStorage.getItem(key); console.log(`${ke …
3. **Session Storage** — window.sessionStorage is a global property that implements the Web Storage API and provides ephemeral key-value storage in the browser.
4. **List All Key-Value Entries** — `for (let i = 0; i < localStorage.length; i++) { const key = localStorage.key(i); const value = localStorage.getItem(key); console.log(`${ke …
5. **IndexedDB** — IndexedDB is a transactional, object-oriented database intended for structured data
6. **Print All the Contents of IndexedDB** — `const dumpIndexedDB = dbName => { const DB_VERSION = 1; const req = indexedDB.open(dbName, DB_VERSION); req.onsuccess = function() { const …
7. **Web SQL** — Web SQL is deprecated since November 18, 2010 and it's recommended that web developers do not use it.

## 使用ツール

- ブラウザ開発者ツール
- DOM Invader
- Retire.js
- Burp Suite

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
