# WSTG-CLNT-09 — Testing for Clickjacking

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

画面を iframe に埋め込ませ、クリックを誘導できないかを確認する。

WSTG の Test Objectives:

- Understand security measures in place.
- Assess how strict the security measures are and if they are bypassable.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. WSTG-CONF-07 手順1 で保存した応答ヘッダから確認する（再取得しない）: `grep -iE '^(x-frame-options|content-security-policy):' evidence/<活動フォルダ>/artifacts/root-headers.txt`。CSP は `frame-ancestors` ディレクティブの有無を見る。単独実行で root-headers.txt が無いときは先に WSTG-CONF-07 を回す
2. 対象ページを `<iframe src=...>` で自作 HTML に埋め込み、実際に表示されるか（枠に出るか）確認
3. 重要操作（送金・設定変更）画面がフレーム内で操作可能なら Clickjacking 可
4. 防御ヘッダが無い/緩い重要画面を finding に。PoC の iframe HTML を artifacts に

## 使用ツール

- ブラウザ

## 判定基準（pass / fail の見分け）

- **pass**: 機微画面に X-Frame-Options: DENY/SAMEORIGIN か CSP frame-ancestors がある。
- **fail**: 任意サイトから iframe 埋め込みでき、操作を誘導できる（PoC の HTML で確認）。
- 補足: 対象は「状態を変える操作がある画面」。静的ページのみなら影響は限定的。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`
- `covers:` — `{id: WSTG-CLNT-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/09-Testing_for_Clickjacking
