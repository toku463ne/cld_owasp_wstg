# WSTG-CRYP-03 — Testing for Sensitive Information Sent via Unencrypted Channels

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

機微情報が暗号化されない経路で送られていないかを確認する。

WSTG の Test Objectives:

- Identify sensitive information transmitted through the various channels.
- Assess the privacy and security of the channels used.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Burp history で、機微情報（資格情報・トークン・個人情報）が HTTP（平文）で送られていないか確認
2. 混在コンテンツ（HTTPS ページ内の HTTP リソース）や、HTTP へフォールバックする経路を確認
3. 機微データが URL・Referer に載って外部へ漏れないか確認
4. 平文送出の箇所を列挙。ATHN-01 と重複時は経路の違いを finding に区別して記載

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 資格情報・個人情報・トークンがすべて TLS 経路のみで送受信される。
- **fail**: HTTP での送信、平文プロトコル（FTP/Telnet/SMTP 平文）の利用、機微情報の GET クエリ露出がある。
- 補足: HTTPS 画面から HTTP の API を呼ぶ混在も対象。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`, `artifacts/crypto-review.md`, `cmd/padbuster.txt`, `cmd/curl-headers-anon.txt`
- `covers:` — `{id: WSTG-CRYP-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー
- `crypto-review` — 暗号利用のレビュー（パディングオラクル・弱い暗号・平文送出）
- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/03-Testing_for_Sensitive_Information_Sent_via_Unencrypted_Channels
