# WSTG-IDNT-02 — Test User Registration Process

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

利用者登録プロセスに、なりすましや権限の不正取得の余地がないかを確認する。

WSTG の Test Objectives:

- Verify that the identity requirements for user registration are aligned with business and security requirements.
- Validate the registration process.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Verify that the identity requirements for user registration are aligned with business and security requirements:
2. Can anyone register for access?
3. Are registrations vetted by a human prior to provisioning, or are they automatically granted if the criteria are met?
4. Can the same person or identity register multiple times?
5. Can users register for different roles or permissions?
6. What proof of identity is required for a registration to be successful?
7. Are registered identities verified?

## 使用ツール

- A HTTP proxy can be a useful tool to test this control.

## 判定基準（pass / fail の見分け）

- **pass**: 本人確認・承認の手順があり、登録だけで特権を得られない。
- **fail**: 誰でも自己登録で特権ロールを取得できる、同一人物が複数アカウントを無制限に作れる等。
- 補足: 業務上の許容範囲は顧客の運用次第。仕様と照らして判断する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/role-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-IDNT-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/02-Test_User_Registration_Process
