# WSTG-CONF-07 — Test HTTP Strict Transport Security

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

HSTS の設定により、平文通信へのダウングレードを防いでいるかを確認する。

WSTG の Test Objectives:

- Review the HSTS header and its validity.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. The presence of the HSTS header can be confirmed by examining the server's response through an intercepting proxy or by using curl as follows:
2. `$ curl -s -D- https://owasp.org | grep -i strict Strict-Transport-Security: max-age=31536000

## 使用ツール

- testssl.sh
- sslyze
- nmap --script ssl-enum-ciphers
- curl
- Burp Suite
- securityheaders.io 相当の手動チェック

## 判定基準（pass / fail の見分け）

- **pass**: HTTPS 応答に Strict-Transport-Security があり、max-age が十分（半年以上）で includeSubDomains 付き。
- **fail**: HSTS ヘッダがない、max-age が極端に短い、または HTTP でしか提供していない画面がある。
- 補足: HSTS は HTTPS 応答でのみ有効。HTTP 側に付けても意味がないことを説明する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/testssl.txt`, `artifacts/tls-summary.md`, `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`
- `covers:` — `{id: WSTG-CONF-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `tls-scan` — TLS 設定スキャン
- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/07-Test_HTTP_Strict_Transport_Security
