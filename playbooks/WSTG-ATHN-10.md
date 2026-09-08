# WSTG-ATHN-10 — Testing for Weaker Authentication in Alternative Channel

## 目的

モバイル・API・SSO など代替チャネルの認証が、本流より弱くなっていないかを確認する。

WSTG の Test Objectives:

- Identify alternative authentication channels.
- Assess the security measures used and if any bypasses exists on the alternative channels.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Understand the Primary Mechanism** — Fully test the website's primary authentication functions
2. **Identify Other Channels** — Other channels can be found by using the following methods:
3. **Enumerate Authentication Functionality** — For each alternative channel where user accounts or functionality are shared, identify if all the authentication functions of the primary ch …
4. **Review and Test** — Alternative channels should be mentioned in the testing report, even if they are marked as "information only" or "out of scope"

## 使用ツール

- Burp Suite
- curl
- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: すべてのチャネルで同等の認証強度・ロックアウト・MFA が適用される。
- **fail**: API やモバイル用エンドポイントだけロックアウトや MFA がない、旧版エンドポイントが残っている。
- 補足: 代替チャネルの洗い出しは recon と burp-crawl の成果を使う。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/10-Testing_for_Weaker_Authentication_in_Alternative_Channel
