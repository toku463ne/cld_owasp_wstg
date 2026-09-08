# WSTG-ATHZ-04 — Testing for Insecure Direct Object References

## 目的

識別子を差し替えて他人のデータにアクセスできないか（IDOR）を確認する。

WSTG の Test Objectives:

- Identify points where object references may occur.
- Assess the access control measures and if they're vulnerable to IDOR.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **The Value of a Parameter Is Used Directly to Retrieve a Database Record** — `http://foo.bar/somepage?invoice=12345
2. **The Value of a Parameter Is Used Directly to Perform an Operation in the System** — `http://foo.bar/changepassword?user=someuser
3. **The Value of a Parameter Is Used Directly to Retrieve a File System Resource** — `http://foo.bar/showImage?img=img00011
4. **The Value of a Parameter Is Used Directly to Access Application Functionality** — `http://foo.bar/accessPage?menuitem=12

## 使用ツール

- Burp Suite
- Autorize / AuthMatrix
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 識別子を他ユーザのものに変えると 403/404 になり、所有者チェックが効いている。
- **fail**: 連番 ID や UUID の差し替えで他ユーザのデータを閲覧・更新・削除できる。
- 補足: 参照だけでなく更新・削除系も試す。テストデータ同士で行い、実データは触らない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authz-matrix.csv`, `notes.md`
- `covers:` — `{id: WSTG-ATHZ-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References
