# WSTG-IDNT-01 — Test Role Definitions

## 目的

ロール定義が文書化され、実装と一致しているかを確認する。

WSTG の Test Objectives:

- Identify and document roles used by the application.
- Attempt to switch, change, or access another role.
- Review the granularity of the roles and the needs behind the permissions given.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Roles Identification** — The tester should start by identifying the application roles being tested through any of the following methods:
2. **Switching to Available Roles** — After identifying possible attack vectors, the tester needs to test and validate that they can access the available roles.
3. **Review Roles Permissions** — After gaining access to the roles on the system, the tester must understand the permissions provided to each role.

## 使用ツール

- To make things easier and more documented, one can use:
- Burp's Autorize extension
- ZAP's Access Control Testing add-on

## 判定基準（pass / fail の見分け）

- **pass**: ロールと権限の一覧があり、実機の挙動と齟齬がない。
- **fail**: 定義が存在しない、または定義と実装が食い違う（実際には上位権限が使えるロールがある）。
- 補足: 後続の authz-matrix の土台になる。ここが曖昧だと権限テストが評価できない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/role-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-IDNT-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/01-Test_Role_Definitions
