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

1. URL/ホストを受け取る入力（`?url=`,`?image=`,webhook）に `http://169.254.169.254/`（クラウドメタデータ）を `curl`/Burp で指定し取得できるか確認
2. 内部 IP（`http://127.0.0.1:port`,`http://10.x`）へのアクセスや、`file://`/`gopher://` スキームを試す
3. リダイレクト・DNS リバインド・別表記（`http://0x7f000001`）でフィルタ迂回を試す
4. 内部到達・メタデータ取得が成立したら SSRF として重大度高めで finding に

## 使用ツール

- curl
- Burp Suite

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
