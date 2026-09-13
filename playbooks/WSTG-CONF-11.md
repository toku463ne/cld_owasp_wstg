# WSTG-CONF-11 — Test Cloud Storage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

クラウドストレージの公開設定が過剰でないかを確認する。

WSTG の Test Objectives:

- Assess that the access control configuration for the storage services is properly in place.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. アプリが参照するストレージ URL（`*.s3.amazonaws.com` / `*.blob.core.windows.net` 等）を JS/HTML から抽出
2. バケット/コンテナに匿名アクセスできるか（`curl -s https://bucket.s3.amazonaws.com/`）確認
3. 一覧・読み取り・書き込み（`aws s3 ls --no-sign-request` 相当）の可否を、許可範囲内で確認
4. 公開が業務上意図されたものか切り分け、意図しない公開のみ finding にする

## 使用ツール

- AWS CLI

## 判定基準（pass / fail の見分け）

- **pass**: バケット・コンテナが匿名アクセス不可、または公開すべきファイルのみ公開。
- **fail**: 一覧取得や任意ファイル取得が匿名でできる、または書き込みができる。
- 補足: 書き込み可否の確認は影響が大きい。実施前に許可範囲を確認し、無害なファイル名で検証する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-bucket.txt`, `artifacts/dangling-dns.md`
- `covers:` — `{id: WSTG-CONF-11, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/11-Test_Cloud_Storage
