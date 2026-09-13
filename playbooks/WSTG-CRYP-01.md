# WSTG-CRYP-01 — Testing for Weak Transport Layer Security

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

TLS の構成（プロトコル・暗号スイート・証明書）が現行水準を満たすかを確認する。

WSTG の Test Objectives:

- Validate the service configuration.
- Review the digital certificate's cryptographic strength and validity.
- Ensure that the TLS security is not bypassable and is properly implemented across the application.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `testssl.sh https://target` または `sslyze --regular target` で全 TLS ポートを一括検査
2. SSLv3/TLS1.0/1.1・弱い暗号スイート（RC4/3DES/EXPORT）・弱い鍵長が有効でないか確認
3. 証明書の有効期限・発行者・ホスト名一致、既知脆弱性（Heartbleed/ROBOT 等）を確認
4. `nmap --script ssl-enum-ciphers -p443 target` で裏取り。結果は artifacts/tls-summary.md に

## 使用ツール

- testssl.sh
- sslyze
- nmap

## 判定基準（pass / fail の見分け）

- **pass**: TLS1.2/1.3 のみ、弱い暗号スイートなし、証明書が有効で信頼チェーンが正しい。
- **fail**: SSLv3/TLS1.0/1.1 が有効、RC4/3DES/NULL/EXPORT が有効、証明書が期限切れ・自己署名・名前不一致。
- 補足: 対象は Web だけでなく、メール・API・管理ポートの TLS も含める。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/testssl.txt`, `artifacts/tls-summary.md`
- `covers:` — `{id: WSTG-CRYP-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `tls-scan` — TLS 設定スキャン

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/01-Testing_for_Weak_Transport_Layer_Security
