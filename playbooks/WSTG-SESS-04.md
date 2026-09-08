# WSTG-SESS-04 — Testing for Exposed Session Variables

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

セッショントークンが漏れやすい場所に出ていないかを確認する。

WSTG の Test Objectives:

- Ensure that proper encryption is implemented.
- Review the caching configuration.
- Assess the channel and methods' security.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Testing for Encryption & Reuse of Session Tokens Vulnerabilities** — Protection from eavesdropping is often provided by SSL encryption, but may incorporate other tunneling or encryption
2. **Testing for Proxies & Caching Vulnerabilities** — Proxies must also be considered when reviewing application security
3. **Testing for GET & POST Vulnerabilities** — In general, GET requests should not be used, as the Session ID may be exposed in Proxy or Firewall logs
4. **Testing for Transport Vulnerabilities** — All interaction between the Client and Application should be tested at least against the following criteria.

## 使用ツール

- Burp Suite
- curl
- ブラウザ2枚

## 判定基準（pass / fail の見分け）

- **pass**: トークンが Cookie でのみ送受信され、URL・ログ・Referer・エラー画面に現れない。
- **fail**: URL クエリやリダイレクト先にトークンが載る、外部サイトへ Referer で漏れる。
- 補足: 外部リソース（CDN・解析タグ）を読み込む画面での Referer 挙動を確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`
- `covers:` — `{id: WSTG-SESS-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/04-Testing_for_Exposed_Session_Variables
