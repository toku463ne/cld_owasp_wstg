# WSTG-ATHZ-02 — Testing for Bypassing Authorization Schema

## 目的

認可チェックを回避して他ロールの機能・データにアクセスできないかを確認する。

WSTG の Test Objectives:

- Assess if horizontal or vertical access is possible.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Testing for Horizontal Bypassing Authorization Schema** — For every function, specific role, or request that the application executes, it is necessary to verify:
2. **Testing for Vertical Bypassing Authorization Schema** — A vertical authorization bypass is specific to the case that an attacker obtains a role higher than their own
3. **Banking Site Roles Scenario** — The following table illustrates the system roles on a banking site
4. **Administrator Page Access** — Suppose that the administrator menu is part of the administrator account.
5. **Testing for Access to Administrative Functions** — For example, suppose that the addUser function is part of the administrative menu of the application, and it is possible to access it by req …
6. **Testing for Access to Resources Assigned to a Different Role** — Various applications setup resource controls based on user roles
7. **Testing for Special Request Header Handling** — Some applications support non-standard headers such as X-Original-URL or X-Rewrite-URL in order to allow overriding the target URL in reques …

## 使用ツール

- OWASP Zed Attack Proxy (ZAP)
- - ZAP add-on: Access Control Testing
- Port Swigger Burp Suite
- - Burp extension: AuthMatrix
- - Burp extension: Autorize

## 判定基準（pass / fail の見分け）

- **pass**: 低権限ロールで高権限のリクエストを再送すると、すべて 401/403 になる。
- **fail**: 低権限や未認証で管理系リクエストが成功する（画面が出ない＝保護されている、ではない）。
- 補足: 表示制御のみで API 側の認可がないパターンが最頻出。必ずリクエスト単位で試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authz-matrix.csv`, `notes.md`, `artifacts/graphql-schema.json`, `artifacts/api-findings.md`
- `covers:` — `{id: WSTG-ATHZ-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）
- `api-graphql-test` — API / GraphQL の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/02-Testing_for_Bypassing_Authorization_Schema
