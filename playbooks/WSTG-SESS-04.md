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

1. セッション ID・トークンが URL・ログ・Referer・隠しフィールドに露出しないか Burp の HTTP 履歴で確認
2. ブラウザ開発者ツールで localStorage/sessionStorage にセッション情報が平文保存されないか確認
3. わざとエラーを誘発し（不正な型・存在しないID・巨大値・壊れたJSON）、返るエラーページ・スタックトレース・デバッグ出力に セッションID/トークン/内部変数が載らないか確認する（応答本文を `grep -iE "session|token|PHPSESSID|JSESSIONID|csrf"` 相当で走査）。載る＝ログ・画面経由の漏えい
4. TLS で保護されていても、URL 露出はブラウザ履歴/プロキシログに残る点を finding に添える

## 使用ツール

- Burp Suite
- ブラウザ開発者ツール

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
