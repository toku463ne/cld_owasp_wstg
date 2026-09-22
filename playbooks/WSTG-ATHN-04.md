# WSTG-ATHN-04 — Testing for Bypassing Authentication Schema

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

認証を経ずに保護対象へ到達できる経路がないかを確認する。

WSTG の Test Objectives:

- Ensure that authentication is applied across all services that require it.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 認証必須ページに直 URL でアクセス（force browsing）し、未認証で開けないか確認
2. ログイン後にセットされる Cookie/パラメータ（`isAuth=false`→`true` 等）を Burp で改変して迂回を試す
3. SQL インジェクション（`' or '1'='1`）・パラメータ改変・レスポンス改変（302→200）で認証を飛ばせるか試す
4. 多段認証の途中ステップを飛ばして最終ページに到達できないか確認

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 保護対象 URL に未認証で直接アクセスするとすべて弾かれる。
- **fail**: 直リンク・パラメータ改変（isAdmin=true 等）・SQL インジェクション・セッション改変で認証を迂回できる。
- 補足: 「リダイレクトされるが本文も返ってきている」パターンを見落とさない。本文の中身を確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/04-Testing_for_Bypassing_Authentication_Schema
