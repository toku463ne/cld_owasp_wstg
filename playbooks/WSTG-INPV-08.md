# WSTG-INPV-08 — Testing for SSI Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

SSI（Server Side Includes）ディレクティブが入力経由で実行されないかを確認する。

WSTG の Test Objectives:

- Identify SSI injection points.
- Assess the severity of the injection.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. To test for exploitable SSI, inject SSI directives as user input. If SSI are enabled and user input validation has not been properly implemented, the server will execute the directive.
2. First determine if the web server supports SSI directives. Often, the answer is yes, as SSI support is quite common.
3. Another way of verifying that SSI directives are enabled is by checking for pages with the .shtml extension, which is associated with SSI directives.
4. The next step is determining all the possible user input vectors and testing to see if the SSI injection is exploitable.
5. First find all the pages where user input is allowed. Possible input vectors may also include headers and cookies.
6. Once you have a list of potential injection points, you may determine if the input is correctly validated.
7. The below example returns the value of the variable. The references section has helpful links with server-specific documentation to help you better assess a particular system.

## 使用ツール

- Web Proxy Burp Suite
- OWASP ZAP
- String searcher: grep

## 判定基準（pass / fail の見分け）

- **pass**: SSI が無効、または入力中の <!--#exec 等が文字列として扱われる。
- **fail**: SSI ディレクティブが解釈され、ファイル読み出しやコマンド実行に至る。
- 補足: .shtml が有効なレガシー環境で残っていることがある。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/08-Testing_for_SSI_Injection
