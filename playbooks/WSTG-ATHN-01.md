# WSTG-ATHN-01 — Testing for Credentials Transported over an Encrypted Channel

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

資格情報が暗号化された経路でのみ送信されているかを確認する。

WSTG の Test Objectives:

- Assess whether any use case of the web site or application causes the server or the client to exchange credentials without encryption.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ログイン画面を HTTP で開けるか試す: `curl -s http://target/login`（HTTPS 強制か確認）
2. Burp で認証情報送信リクエストを捕捉し、送信先が https で POST body に載っている（GET/URL でない）か確認
3. HTTPS 画面から HTTP エンドポイントへ資格情報を投げていないか、リダイレクト前の初回リクエストも確認
4. ログイン後の各機能でも平文チャネルへ資格情報が漏れないか history を見る

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: ログイン画面と送信先の両方が HTTPS で、HTTP へのフォールバックがない。
- **fail**: 資格情報が HTTP で送信される、HTTPS 画面から HTTP へ POST している、または GET のクエリに載っている。
- 補足: リダイレクト前の最初のリクエストが平文になっていないかも確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/01-Testing_for_Credentials_Transported_over_an_Encrypted_Channel
