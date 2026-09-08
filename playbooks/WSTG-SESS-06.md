# WSTG-SESS-06 — Testing for Logout Functionality

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ログアウトでセッションが確実に破棄されるかを確認する。

WSTG の Test Objectives:

- Assess the logout UI.
- Analyze the session timeout and if the session is properly killed after logout.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Testing for Log Out User Interface** — Verify the appearance and visibility of the log out functionality in the user interface
2. **Testing for Server-Side Session Termination** — First, store the values of cookies that are used to identify a session
3. **Testing for Session Timeout** — Try to determine a session timeout by performing requests to a page in the authenticated area of the web application with increasing delays
4. **Testing for Session Termination in Single Sign-On Environments (Single Sign-Off)** — Perform a log out in the tested application

## 使用ツール

- Burp Suite - Repeater

## 判定基準（pass / fail の見分け）

- **pass**: ログアウト後、旧トークンでのリクエストがすべて拒否される（サーバ側で失効）。
- **fail**: ログアウト後も旧トークンが使える、Cookie 削除だけでサーバ側が失効していない。
- 補足: ログアウトボタンが分かりにくい／存在しない場合も所見として記録する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/session-trace.burp`, `artifacts/token-samples.txt`, `notes.md`
- `covers:` — `{id: WSTG-SESS-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/06-Testing_for_Logout_Functionality
