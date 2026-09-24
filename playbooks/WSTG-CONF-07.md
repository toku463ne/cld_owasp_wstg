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

1. `curl -sD evidence/<活動フォルダ>/artifacts/root-headers.txt -o /dev/null https://target/` で応答ヘッダを保存し（この後の手順・WSTG-CLNT-09 でも使い回す）、`grep -i '^strict-transport-security:' evidence/<活動フォルダ>/artifacts/root-headers.txt` で HSTS の有無・値を確認
2. `max-age`（半年=15768000 以上が目安）・`includeSubDomains`・`preload` の各ディレクティブを確認
3. `curl -sI http://target/` で HTTP アクセス時の挙動（HTTPS へ 301 されるか）を確認
4. HTTP 応答に HSTS を付けても無効な点を踏まえ、HTTPS 応答での設定を評価

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: HTTPS 応答に Strict-Transport-Security があり、max-age が十分（半年以上）で includeSubDomains 付き。
- **fail**: HSTS ヘッダがない、max-age が極端に短い、または HTTP でしか提供していない画面がある。
- 補足: HSTS は HTTPS 応答でのみ有効。HTTP 側に付けても意味がないことを説明する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/testssl.txt`, `artifacts/tls-summary.md`, `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`
- `covers:` — `{id: WSTG-CONF-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `tls-scan` — TLS 設定スキャン
- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/07-Test_HTTP_Strict_Transport_Security
