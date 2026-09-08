# WSTG-CLNT-03 — Testing for HTML Injection

## 目的

入力が HTML として解釈され、画面を改変できないかを確認する。

WSTG の Test Objectives:

- Identify HTML injection points and assess the severity of the injected content.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Consider the following DOM XSS exercise http://www.domxss.com/domxss/01_Basics/06_jquery_old_html.html
2. The HTML code contains the following script:
3. `<script src="../js/jquery-1.7.1.js"></script> <script> function setMessage(){ var t=location.hash.slice(1); $("div[id="+t+"]").text("The DOM is now loaded and can be manipulated."); } $(doc …
4. It is possible to inject HTML code.
5. The OWASP® Foundation works to improve the security of software through its community-led open source software projects,
6. hundreds of chapters worldwide, tens of thousands of members, and by hosting local and global conferences.

## 使用ツール

- Burp Suite
- DOM Invader
- 手動 payload

## 判定基準（pass / fail の見分け）

- **pass**: タグがエスケープされ、文字列として表示される。
- **fail**: 任意タグ挿入で偽のフォーム・リンクを差し込める（スクリプト実行に至らなくてもフィッシングに使える）。
- 補足: スクリプトが動かなくても指摘対象。影響は「見た目の改変＋誘導」で説明する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/xss-findings.md`, `artifacts/payloads.txt`
- `covers:` — `{id: WSTG-CLNT-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `xss-probe` — XSS・HTML インジェクションの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/03-Testing_for_HTML_Injection
