# WSTG-ATHZ-03 — Testing for Privilege Escalation

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

1. **Testing for Role/Privilege Manipulation** — In every portion of the application where a user can create information in the database (e.g., making a payment, adding a contact, or sendin …
2. **Manipulation of User Group** — The following HTTP POST allows the user that belongs to grp001 to access order #0001:
3. **Manipulation of User Profile** — The following server's answer shows a hidden field in the HTML returned to the user after a successful authentication.
4. **Manipulation of Condition Value** — In an environment where the server sends an error message contained as a value in a specific parameter in a set of answer codes, as the foll …
5. **Manipulation of IP Address** — Some websites limit access or count the number of failed login attempts based on IP address.
6. **URL Traversal** — Try to traverse the website and check if some of pages that may miss the authorization check.
7. **WhiteBox** — If the URL authorization check is only done by partial URL match, then it's likely testers or hackers may workaround the authorization by UR …

## 使用ツール

- OWASP Zed Attack Proxy (ZAP)
- Watch
- Star

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
