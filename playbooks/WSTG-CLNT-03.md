# WSTG-CLNT-03 — Testing for HTML Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が HTML として解釈され、画面を改変できないかを確認する。

WSTG の Test Objectives:

- Identify HTML injection points and assess the severity of the injected content.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 入力が HTML として反映される箇所に `<h1>test</h1>` `<b>` 等を入れ、タグが解釈されるか確認
2. スクリプト無しでもコンテンツ偽装・フィッシング用の要素を差し込めるか確認
3. 反映先の文脈（本文/属性）に応じてタグ注入の成否を確認
4. HTML 注入が成立する箇所を finding に（XSS に発展し得るかも併記）

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
