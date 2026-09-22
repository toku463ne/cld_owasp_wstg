# WSTG-SESS-05 — Testing for Cross Site Request Forgery

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

状態変更操作が CSRF 対策で守られているかを確認する。

WSTG の Test Objectives:

- Determine whether it is possible to initiate requests on a user's behalf that are not initiated by the user.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 状態変更操作（送金・設定変更・削除）のリクエストに CSRF トークンがあるか Burp で確認
2. トークンを Burp Repeater で削除/固定値に改変して再送し、受理されるか（検証されているか）試す
3. トークンがセッションに紐づくか（他人のトークンが通らないか）、`SameSite` Cookie で守られているか確認
4. GET で状態変更できる/`Referer`・`Origin` 検証がない箇所を CSRF 可として finding に

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: 状態変更に単回性のトークンが必要、または SameSite と Origin/Referer 検証で守られている。
- **fail**: トークンなし・検証なし・トークンを削除しても成功する・ユーザ間で使い回せる。
- 補足: PoC の HTML を artifacts に置くと再現手順として最も分かりやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`
- `covers:` — `{id: WSTG-SESS-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/05-Testing_for_Cross_Site_Request_Forgery
