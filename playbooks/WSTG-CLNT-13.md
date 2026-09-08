# WSTG-CLNT-13 — Testing for Cross Site Script Inclusion

## 目的

認証済みの JS/JSON を外部サイトから読み込ませて情報を抜けないか（XSSI）を確認する。

WSTG の Test Objectives:

- Locate sensitive data across the system.
- Assess the leakage of sensitive data through various techniques.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Collect Data Using Authenticated and Unauthenticated User Sessions** — Identify which endpoints are responsible for sending sensitive data, what parameters are required, and identify all relevant dynamically and …
2. **Determine Whether the Sensitive Data Can Be Leaked Using JavaScript** — Testers should analyze code for the following vehicles for data leakage via XSSI vulnerabilities:
3. **1. Sensitive Data Leakage via Global Variables** — An API key is stored in a JavaScript file with the URI https://victim.com/internal/api.js on the victim's website, victim.com, which is only …
4. **2. Sensitive Data Leakage via Global Function Parameters** — This example is similar to the previous one, except in this case attackingwebsite.com uses a global JavaScript function to extract the sensi …
5. **3. Sensitive Data Leakage via CSV with Quotations Theft** — To leak data the attacker/tester has to be able to inject JavaScript code into the CSV data
6. **4. Sensitive Data Leakage via JavaScript Runtime Errors** — Browsers normally present standardized JavaScript error messages
7. **5. Sensitive Data Leakage via Prototype Chaining Using this** — In JavaScript, the this keyword is dynamically scoped

## 使用ツール

- ブラウザ開発者ツール
- DOM Invader
- Retire.js
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 動的 JS/JSON がスクリプトとして読み込めない、または推測不能なトークンで保護される。
- **fail**: 認証情報を含む JS/JSON を外部ページの script タグで読み込み、内容を取得できる。
- 補足: JSON 応答が配列リテラルのみ・JSONP 対応の場合に成立しやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-13, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/13-Testing_for_Cross_Site_Script_Inclusion
