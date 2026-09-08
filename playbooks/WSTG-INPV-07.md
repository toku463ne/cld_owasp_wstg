# WSTG-INPV-07 — Testing for XML Injection

## 目的

XML 入力の解析で構造改変や外部実体参照（XXE）が起きないかを確認する。

WSTG の Test Objectives:

- Identify XML injection points.
- Assess the types of exploits that can be attained and their severities.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Discovery** — The first step in order to test an application for the presence of a XML Injection vulnerability consists of trying to insert XML metacharac …
2. **Tag Injection** — Once the first step is accomplished, the tester will have some information about the structure of the XML document

## 使用ツール

- XML Injection Fuzz Strings (from wfuzz tool)

## 判定基準（pass / fail の見分け）

- **pass**: 外部実体・DTD が無効化され、タグ挿入も無害化される。
- **fail**: XXE でファイル読み出し・SSRF ができる、または XML 構造を改変して業務値を変えられる。
- 補足: SOAP・SAML・ファイルアップロード（docx/svg）も XML の入口。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/07-Testing_for_XML_Injection
