# WSTG-CLNT-08 — Testing for Cross Site Flashing

## 目的

残存する Flash コンテンツに情報漏えい・XSS の余地がないかを確認する。

WSTG の Test Objectives:

- Decompile and analyze the application's code.
- Assess sinks inputs and unsafe method usages.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Decompilation** — Since SWF files are interpreted by a virtual machine embedded in the player itself, they can be potentially decompiled and analyzed
2. **Undefined Variables FlashVars** — FlashVars are the variables that the SWF developer planned on receiving from the web page
3. **Unsafe Methods** — When an entry point is identified, the data it represents could be used by unsafe methods
4. **Exploitation by Reflected XSS** — The swf file should be hosted on the victim's host, and the techniques of reflected XSS must be used
5. **GetURL (AS2) / NavigateToURL (AS3)** — The GetURL function in ActionScript 2.0 and NavigateToURL in ActionScript 3.0 lets the movie load a URI into the browser's window
6. **Using asfunction** — You can use the special asfunction protocol to cause the link to execute an ActionScript function in a SWF file instead of opening a URL
7. **ExternalInterface** — ExternalInterface.call is a static method introduced by Adobe to improve player/browser interaction for both ActionScript 2.0 and ActionScri …

## 使用ツール

- curl
- 手動レビュー

## 判定基準（pass / fail の見分け）

- **pass**: Flash コンテンツが存在しない（現在はこれが通常）。
- **fail**: swf が残り、allowScriptAccess 等の設定でスクリプト実行やクロスドメインアクセスができる。
- 補足: 現行ブラウザでは実行されないが、資産として残っていれば整理を助言する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-crossdomain.txt`, `artifacts/ria-findings.md`
- `covers:` — `{id: WSTG-CLNT-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `ria-legacy-check` — RIA クロスドメインポリシーとレガシー Flash の確認

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/08-Testing_for_Cross_Site_Flashing
