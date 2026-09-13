# WSTG-CONF-08 — Test RIA Cross Domain Policy

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

crossdomain.xml / clientaccesspolicy.xml による過剰なクロスドメイン許可がないかを確認する。

WSTG の Test Objectives:

- Review and validate the policy files.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `curl -s https://target/crossdomain.xml` と `clientaccesspolicy.xml` を取得
2. `allow-access-from domain="*"` などワイルドカード許可になっていないか確認
3. `secure="false"` や過度に広い許可ドメインが指定されていないか見る
4. 該当ファイルが存在しない/最小限なら pass、緩い許可があれば影響を finding に記載

## 使用ツール

- Nikto
- OWASP Zed Attack Proxy Project
- W3af

## 判定基準（pass / fail の見分け）

- **pass**: これらのポリシーファイルが存在しない、または許可ドメインが必要最小限。
- **fail**: allow-access-from domain="*" のようなワイルドカード許可がある。
- 補足: Flash は終息済みだが、ファイルが残っていると他クライアントが参照する場合がある。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-crossdomain.txt`, `artifacts/ria-findings.md`
- `covers:` — `{id: WSTG-CONF-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `ria-legacy-check` — RIA クロスドメインポリシーとレガシー Flash の確認

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/08-Test_RIA_Cross_Domain_Policy
