# WSTG-ATHN-02 — Testing for Default Credentials

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

既定の資格情報や推測しやすいアカウントが残っていないかを確認する。

WSTG の Test Objectives:

- Enumerate the applications for default credentials and validate if they still exist.
- Review and assess new user accounts and if they are created with any defaults or identifiable patterns.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 製品/機器の既定資格情報（`admin/admin`・ベンダ既定）を管理画面・アプリログインで試す
2. 既定ユーザ名の列挙（`admin`/`root`/`test`/`guest`）と、初期パスワード未変更を確認
3. インストーラ・セットアップ画面が残り、無認証でアクセスできないか確認
4. 成功した組合せは要約のみ finding に、実際の資格情報は evidence にパス参照で残す

## 使用ツール

- Burp Intruder
- THC Hydra
- Nikto 2

## 判定基準（pass / fail の見分け）

- **pass**: 既定アカウントが削除・無効化・パスワード変更済み。
- **fail**: admin/admin 等の既定資格情報でログインできる、または製品既定アカウントが有効。
- 補足: 総当たりではなく「製品既定値の確認」に留める。試行回数は事前合意の範囲で。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/02-Testing_for_Default_Credentials
