# WSTG-IDNT-03 — Test Account Provisioning Process

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

アカウント払い出し・停止・削除の運用が適切かを確認する。

WSTG の Test Objectives:

- Verify which accounts may provision other accounts and of what type.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Determine which roles are able to provision users and what sort of accounts they can provision.
2. Is there any verification, vetting and authorization of provisioning requests?
3. Is there any verification, vetting and authorization of de-provisioning requests?
4. Can an administrator provision other administrators or just users?
5. Can an administrator or other user provision accounts with privileges greater than their own?
6. Can an administrator or user de-provision themselves?
7. How are the files or resources owned by the de-provisioned user managed? Are they deleted? Is access transferred?

## 使用ツール

- Watch
- Star

## 判定基準（pass / fail の見分け）

- **pass**: 払い出しに承認があり、退職・異動時の停止手順が定義・実行されている。
- **fail**: 管理者が承認なくアカウントを作成できる、退職者アカウントが有効なまま残る。
- 補足: 実機よりヒアリングと証跡（申請記録）で判断する項目。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/role-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-IDNT-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/03-Test_Account_Provisioning_Process
