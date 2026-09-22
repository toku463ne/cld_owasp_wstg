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

1. 登録フォームを Burp で捕捉し、同一メール/ユーザ名で二重登録できるか試す
2. 登録に必要な検証（メール確認・管理者承認）を省略して自己登録できないか確認
3. ロール指定パラメータ（`role=admin` 等）を Burp Repeater で登録リクエストに追加し、権限昇格して登録できないか試す
4. 使い捨てメール・大量自動登録への対策（CAPTCHA・レート制限）の有無を確認

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: 本人確認・承認の手順があり、登録だけで特権を得られない。
- **fail**: 誰でも自己登録で特権ロールを取得できる、同一人物が複数アカウントを無制限に作れる等。
- 補足: 業務上の許容範囲は顧客の運用次第。仕様と照らして判断する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/role-matrix.md`, `notes.md`
- `covers:` — `{id: WSTG-IDNT-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/02-Test_User_Registration_Process
