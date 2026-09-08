# WSTG-INPV-02 — Testing for Stored Cross Site Scripting

## 目的

保存された入力が、他の利用者の画面でスクリプトとして実行されないかを確認する。

WSTG の Test Objectives:

- Identify stored input that is reflected on the client-side.
- Assess the input they accept and the encoding that gets applied on return (if any).

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing** — The process for identifying stored XSS vulnerabilities is similar to the process described during the testing for reflected XSS.
2. **Input Forms** — The first step is to identify all points where user input is stored into the back-end and then displayed by the application
3. **Analyze HTML Code** — Input stored by the application is normally used in HTML tags, but it can also be found as part of JavaScript content
4. **Testing for Stored XSS** — This involves testing the input validation and filtering controls of the application
5. **Leverage Stored XSS with BeEF** — Stored XSS can be exploited by advanced JavaScript exploitation frameworks such as BeEF and XSS Proxy.
6. **File Upload** — If the web application allows file upload, it is important to check if it is possible to upload HTML content
7. **Gray-Box Testing** — Gray-box testing is similar to black-box testing

## 使用ツール

- XSS-Proxy is an advanced Cross-Site-Scripting (XSS) attack tool.

## 判定基準（pass / fail の見分け）

- **pass**: 保存値が表示時に適切にエスケープされる。
- **fail**: 保存した値が別ユーザ・管理画面で実行される（管理画面での発火は重大度が上がる）。
- 補足: 投入したテストデータは記録し、可能なら試験後に削除する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/xss-findings.md`, `artifacts/payloads.txt`
- `covers:` — `{id: WSTG-INPV-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `xss-probe` — XSS・HTML インジェクションの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/02-Testing_for_Stored_Cross_Site_Scripting
