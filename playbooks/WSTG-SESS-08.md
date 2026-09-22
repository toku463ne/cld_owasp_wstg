# WSTG-SESS-08 — Testing for Session Puzzling

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

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

1. 認証途中・パスワードリセット途中など中間状態で発行される変数/セッションを Burp で確認
2. 中間状態のセッションを使い Burp で本来到達できない後続画面へ進めないか試す
3. 同一セッションが複数のロール/フローで再利用され、状態が混線しないか確認
4. 状態遷移を飛ばす/巻き戻すことで権限や本人確認を回避できないか検証

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 認証・リセット・登録など機能ごとに独立した状態を持ち、途中状態で他機能に入れない。
- **fail**: パスワードリセットの途中状態が認証済みとして扱われる等、フローをまたいで権限が湧く。
- 補足: 複数フローを並行して開始し、途中で行き来するのが見つけ方のコツ。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`, `artifacts/authz-matrix.csv`, `notes.md`
- `covers:` — `{id: WSTG-SESS-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）
- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/08-Testing_for_Session_Puzzling
