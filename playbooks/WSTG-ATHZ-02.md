# WSTG-ATHZ-02 — Testing for Bypassing Authorization Schema

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

認可チェックを回避して他ロールの機能・データにアクセスできないかを確認する。

WSTG の Test Objectives:

- Assess if horizontal or vertical access is possible.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 低権限アカウントで、高権限用の URL/機能に直接アクセス（force browsing）できるか確認
2. Burp で高権限操作のリクエストを捕捉し、低権限セッションの Cookie に差し替えて再送（横移動/縦移動）
3. 認可判定がクライアント側（メニュー非表示のみ）に依存していないか確認
4. 未認証でも保護リソースに到達できないか、Cookie を外して再送し確認

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 低権限ロールで高権限のリクエストを再送すると、すべて 401/403 になる。
- **fail**: 低権限や未認証で管理系リクエストが成功する（画面が出ない＝保護されている、ではない）。
- 補足: 表示制御のみで API 側の認可がないパターンが最頻出。必ずリクエスト単位で試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authz-matrix.csv`, `notes.md`, `artifacts/graphql-schema.json`, `artifacts/api-findings.md`
- `covers:` — `{id: WSTG-ATHZ-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）
- `api-graphql-test` — API / GraphQL の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/02-Testing_for_Bypassing_Authorization_Schema
