# WSTG-ATHZ-03 — Testing for Privilege Escalation

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

自分より高い権限へ昇格できないかを確認する。

WSTG の Test Objectives:

- Identify injection points related to privilege manipulation.
- Fuzz or otherwise attempt to bypass security measures.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 低権限アカウントで、ロールを示すパラメータ/Cookie/JWT クレーム（`role`,`isAdmin`,`group`）を管理者値に改変し Burp Repeater で再送
2. 管理者専用機能のリクエストを低権限セッションで再送し、実行できるか確認
3. 多段承認・所有者チェックを飛ばして他ユーザ資源を操作できないか試す
4. 水平（同ロール他人）・垂直（上位ロール）の両方向で昇格を検証

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: ロール・権限を示す値を改変しても、サーバ側で拒否される。
- **fail**: パラメータ・JWT クレーム・Cookie の改変や、権限付与 API の直接呼び出しで昇格できる。
- 補足: 水平（他ユーザ）と垂直（上位権限）を分けて記録すると報告が明確になる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authz-matrix.csv`, `notes.md`
- `covers:` — `{id: WSTG-ATHZ-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/03-Testing_for_Privilege_Escalation
