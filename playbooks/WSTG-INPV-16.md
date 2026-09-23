# WSTG-INPV-16 — Testing for HTTP Incoming Requests

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

リバースプロキシ等が受け取るリクエストの扱いに、迂回や露出がないかを確認する。

WSTG の Test Objectives:

- Monitor all incoming and outgoing HTTP requests to the Web Server to inspect any suspicious requests.
- Monitor HTTP traffic without changes of end user Browser proxy or client-side application.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. サーバが受け付ける生リクエスト（異常メソッド・巨大ヘッダ・不正 Host）を `ncat`/`curl` で送り挙動を確認
   > ⚠️ **負荷注意（手順1）**: 巨大ヘッダ・異常リクエストはサーバのパースでリソースを食い、終端によっては不安定化しうる。サイズは段階的に上げる。
2. リクエスト解析の甘さ（不正な行終端・重複ヘッダ）で異常応答が出ないか確認
3. 監視・WAF が生の異常リクエストを取りこぼさないか確認
4. 他の注入系（INPV-15/17）と併せて解釈差を検証

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: 巨大ヘッダ・異常リクエストはサーバのパースでリソースを食い、終端によっては不安定化しうる。サイズは段階的に上げる。

## 使用ツール

- ncat
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 内部向けパス・管理系へのリクエストが前段で確実に遮断される。
- **fail**: パス正規化の差やヘッダ細工で、前段の制限を越えて内部へ到達できる。
- 補足: 前段機器の設定ヒアリングと突き合わせないと誤判定しやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- `covers:` — `{id: WSTG-INPV-16, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-request-tamper` — HTTP リクエスト改変系の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/16-Testing_for_HTTP_Incoming_Requests
