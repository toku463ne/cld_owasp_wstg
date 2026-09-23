# WSTG-CLNT-07 — Testing Cross Origin Resource Sharing

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

CORS 設定が過剰に緩くないかを確認する。

WSTG の Test Objectives:

- Identify endpoints that implement CORS.
- Ensure that the CORS configuration is secure or harmless.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 任意 Origin を送って CORS 応答ヘッダを保存する: `curl -s -D - -o /dev/null -H 'Origin: https://evil.example' https://target/api | tee evidence/<活動フォルダ>/artifacts/cors.txt`（HEAD だと CORS ヘッダが返らない実装があるので GET でヘッダのみ取得。`/api` は実際の API パスに置き換える）
2. 手順1の応答から危険な組合せを自動判定する: `grep -iE 'access-control-allow-(origin|credentials):' evidence/<活動フォルダ>/artifacts/cors.txt | tee evidence/<活動フォルダ>/artifacts/cors-verdict.txt; grep -qiE 'access-control-allow-origin:[[:space:]]*(https://evil\.example|\*)' evidence/<活動フォルダ>/artifacts/cors.txt && grep -qiE 'access-control-allow-credentials:[[:space:]]*true' evidence/<活動フォルダ>/artifacts/cors.txt && echo '危険: 反射/ワイルドカード Origin + credentials=true（他サイトが認証付きで機微データを読める）'`。この行が出たら fail 側の材料。`*` 単独（credentials 無し）や個別の正規 Origin 許可は、許可先の妥当性を手順3で確認する
3. 任意/緩いオリジンからの認証付きリクエストで機微データを読めないか検証
4. 過度に緩い CORS（旧指示の CONF-12 相当）を finding に

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: Access-Control-Allow-Origin が許可オリジンのみ、認証付きリクエストでワイルドカードや Origin 反射がない。
- **fail**: 任意の Origin を反射しつつ Allow-Credentials: true、または null オリジンを許可している。
- 補足: プリフライトだけでなく、実リクエストの応答ヘッダで確認する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`, `cmd/curl-cors.txt`, `artifacts/ws-trace.md`
- `covers:` — `{id: WSTG-CLNT-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）
- `cors-websocket-check` — CORS と WebSocket の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/07-Testing_Cross_Origin_Resource_Sharing
