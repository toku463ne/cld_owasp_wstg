# WSTG-BUSL-07 — Test Defenses Against Application Misuse

## 目的

想定外の使い方をされたときにアプリが検知・防御するかを確認する。

WSTG の Test Objectives:

- Generate notes from all tests conducted against the system.
- Review which tests had a different functionality based on aggressive input.
- Understand the defenses in place and verify if they are enough to protect the system against bypassing techniques.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. This test is unusual in that the result can be drawn from all the other tests performed against the web application.
2. Actions that log a user out or lock their account
3. These may only be localized. Common localized (per function) defenses are:
4. Rejecting input containing certain characters
5. Locking out an account temporarily after a number of authentication failures
6. Localized security controls are not sufficient. There are often no defenses against general mis-use such as:
7. Bypassing presentation layer input validation

## 使用ツール

- Burp Suite
- 手動操作
- 業務仕様書

## 判定基準（pass / fail の見分け）

- **pass**: 異常な利用（大量リクエスト・不正パラメータ連発）を検知し、記録・遮断・通知が行われる。
- **fail**: 明らかな攻撃パターンを繰り返しても検知も抑止もされない。
- 補足: 検知の有無は顧客側のログ確認が必要。ヒアリング結果も evidence に残す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/07-Test_Defenses_Against_Application_Misuse
