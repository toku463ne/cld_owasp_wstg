# WSTG-SESS-08 — Testing for Session Puzzling

## 目的

同一のセッション変数が複数用途で使い回され、状態を取り違えないかを確認する。

WSTG の Test Objectives:

- Identify all session variables.
- Break the logical flow of session generation.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Black-Box Testing** — This vulnerability can be detected and exploited by enumerating all of the session variables used by the application and in which context th …
2. **Examples** — A very simple example could be the password reset functionality that, in the entry point, could request the user to provide some identifying …
3. **Gray-Box Testing** — The most effective way to detect these vulnerabilities is via a source code review.

## 使用ツール

- Burp Suite
- curl
- ブラウザ2枚
- Burp Suite
- Autorize / AuthMatrix
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 認証・リセット・登録など機能ごとに独立した状態を持ち、途中状態で他機能に入れない。
- **fail**: パスワードリセットの途中状態が認証済みとして扱われる等、フローをまたいで権限が湧く。
- 補足: 複数フローを並行して開始し、途中で行き来するのが見つけ方のコツ。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`, `artifacts/authz-matrix.csv`, `notes.md`
- `covers:` — `{id: WSTG-SESS-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）
- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/08-Testing_for_Session_Puzzling
