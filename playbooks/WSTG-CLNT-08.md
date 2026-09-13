# WSTG-CLNT-08 — Testing for Cross Site Flashing

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. Flash（SWF）が残る環境で、`allowScriptAccess`/`allowDomain` の設定と外部からの制御可否を確認
2. SWF に渡るパラメータ（`FlashVars`）経由で JS 実行・遷移を誘発できないか確認
3. レガシー技術。存在自体が縮退対象なので、残っていれば撤去も助言
4. 成立する XSF 経路があれば finding に

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
