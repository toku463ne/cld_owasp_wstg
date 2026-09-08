# WSTG-INPV-01 — Testing for Reflected Cross Site Scripting

## 目的

URL・フォームの入力がそのまま応答に反映され、スクリプトが実行されないかを確認する。

WSTG の Test Objectives:

- Identify variables that are reflected in responses.
- Assess the input they accept and the encoding that gets applied on return (if any).

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing** — A black-box test will include at least three phases:
2. **Detect Input Vectors** — Detect input vectors
3. **Analyze Input Vectors** — Analyze each input vector to detect potential vulnerabilities
4. **Check Impact** — For each test input attempted in the previous phase, the tester will analyze the result and determine if it represents a vulnerability that …
5. **Bypass XSS Filters** — Reflected cross-site scripting attacks are prevented as the web application sanitizes input, a web application firewall blocks malicious inp …
6. **Gray-Box Testing** — Gray-box testing is similar to black-box testing

## 使用ツール

- XSS-Proxy is an advanced Cross-Site-Scripting (XSS) attack tool.

## 判定基準（pass / fail の見分け）

- **pass**: 入力が文脈に応じてエスケープされ、ペイロードが文字列として表示される。
- **fail**: 反射した入力がスクリプトとして実行される（HTML・属性・JS・URL いずれの文脈でも）。
- 補足: 出力文脈ごとにペイロードを変える。WAF による部分ブロックは緩和であって修正ではない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/xss-findings.md`, `artifacts/payloads.txt`
- `covers:` — `{id: WSTG-INPV-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `xss-probe` — XSS・HTML インジェクションの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/01-Testing_for_Reflected_Cross_Site_Scripting
