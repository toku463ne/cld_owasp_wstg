# WSTG-CLNT-02 — Testing for JavaScript Execution

## 目的

入力が JS の実行文脈に入り込まないかを確認する。

WSTG の Test Objectives:

- Identify sinks and possible JavaScript injection points.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Consider the following: DOM XSS exercise
2. The page contains the following script:
3. `<script> function loadObj(){ var cc=eval('('+aMess+')'); document.getElementById('mess').textContent=cc.message; } if(window.location.hash.indexOf('message')==-1) { var aMess='({"message":" …
4. The above code contains a source location.hash that is controlled by the attacker that can inject directly in the message value a JavaScript Code to take the control of the user browser.
5. The OWASP® Foundation works to improve the security of software through its community-led open source software projects,
6. hundreds of chapters worldwide, tens of thousands of members, and by hosting local and global conferences.

## 使用ツール

- ブラウザ開発者ツール
- DOM Invader
- Retire.js
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: JS 文字列に埋め込まれる値がエスケープされ、文脈を抜け出せない。
- **fail**: eval / setTimeout / Function に外部由来の値が渡り実行される。
- 補足: CLNT-01 と重なる。どのシンクで成立したかを finding に明記する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/02-Testing_for_JavaScript_Execution
