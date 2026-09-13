# WSTG-INPV-18 — Testing for Server-side Template Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. テンプレートに渡り得る入力に `{{7*7}}` `${7*7}` `#{7*7}` `<%= 7*7 %>` を入れ、`49` に評価されるか確認
2. 評価された場合はエンジンを特定し、対応ペイロードで内部変数/コマンド実行に到達できるか確認
3. 反映先がサーバ側テンプレート（メール/PDF/画面）か切り分ける
4. SSTI が RCE に至る経路を確認。実証は最小限に留め finding に

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
