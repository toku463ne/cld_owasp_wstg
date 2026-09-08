# WSTG-INPV-18 — Testing for Server-side Template Injection

## 目的

入力がテンプレートエンジンの式として評価されないかを確認する。

WSTG の Test Objectives:

- Detect template injection vulnerability points.
- Identify the templating engine.
- Build the exploit.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Identify Template Injection Vulnerability** — The first step in testing SSTI in plaintext context is to construct common template expressions used by various template engines as payloads …
2. **Identify the Templating Engine** — Based on the information from the previous step now the tester has to identify which template engine is used by supplying various template e …
3. **Build the RCE Exploit** — The main goal in this step is to identify to gain further control on the server with an RCE exploit by studying the template documentation a …

## 使用ツール

- Tplmap
- Backslash Powered Scanner Burp Suite extension
- Template expression test strings/payloads list

## 判定基準（pass / fail の見分け）

- **pass**: {{7*7}} 等が文字列のまま表示される。
- **fail**: 式が評価されて 49 が返る、さらにオブジェクトアクセスからコード実行に至る。
- 補足: エンジン特定後の深追いは影響が大きい。評価成立の証明までで止めるのが基本。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-18, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/18-Testing_for_Server-side_Template_Injection
