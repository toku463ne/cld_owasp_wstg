# WSTG-INPV-11 — Testing for Code Injection

## 目的

入力がサーバ側でコードとして評価されないかを確認する。

WSTG の Test Objectives:

- Identify injection points where you can inject code into the application.
- Assess the injection severity.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing**
2. **Testing for PHP Injection Vulnerabilities** — Using the querystring, the tester can inject code (in this example, a malicious URL) to be processed as part of the included file:
3. **Gray-Box Testing**
4. **Testing for ASP Code Injection Vulnerabilities** — Examine ASP code for user input used in execution functions

## 使用ツール

- Burp Intruder
- sqlmap
- tplmap
- 手動 payload

## 判定基準（pass / fail の見分け）

- **pass**: 入力が eval 等に渡らず、渡る場合も厳格に検証されている。
- **fail**: 入力片がコードとして評価され、任意処理を実行できる（LFI/RFI 経由の実行を含む）。
- 補足: 実行確認は無害なコマンド（sleep・ping 相当）に留め、影響範囲を広げない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-11, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/11-Testing_for_Code_Injection
