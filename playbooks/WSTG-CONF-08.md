# WSTG-CONF-08 — Test RIA Cross Domain Policy

## 目的

crossdomain.xml / clientaccesspolicy.xml による過剰なクロスドメイン許可がないかを確認する。

WSTG の Test Objectives:

- Review and validate the policy files.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. To test for RIA policy file weakness the tester should try to retrieve the policy files crossdomain.xml and clientaccesspolicy.xml from the application's root, and from every folder found.
2. For example, if the application's URL is http://www.owasp.org, the tester should try to download the files http://www.owasp.org/crossdomain.xml and http://www.owasp.org/clientaccesspolicy.xm …
3. After retrieving all the policy files, the permissions allowed should be be checked under the least privilege principle.
4. `<cross-domain-policy> <allow-access-from domain="*" /> </cross-domain-policy>
5. A list of policy files found.
6. A list of weak settings in the policies.

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
