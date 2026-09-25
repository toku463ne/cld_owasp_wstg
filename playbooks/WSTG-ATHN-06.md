# WSTG-ATHN-06 — Testing for Browser Cache Weaknesses

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

認証済み画面がブラウザキャッシュに残り、後から閲覧されないかを確認する。

WSTG の Test Objectives:

- Review if the application stores sensitive information on the client-side.
- Review if access can occur without authorization.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 認証済みの機微画面 URL を evidence/<活動フォルダ>/artifacts/auth-urls.txt に1行1件で置き、ログイン後の Cookie を evidence/<活動フォルダ>/artifacts/cookies.txt に用意（ブラウザからエクスポート、または curl -c で保存）した上で、キャッシュ抑止ヘッダを一括確認（2つが揃うまで一括実行では「入力待ち」で飛ばす）: `test -s evidence/<活動フォルダ>/artifacts/auth-urls.txt -a -s evidence/<活動フォルダ>/artifacts/cookies.txt || exit 75; while read -r u; do echo "== $u =="; curl -sI -b evidence/<活動フォルダ>/artifacts/cookies.txt "$u" | grep -iE '^(cache-control|pragma|expires):'; done < evidence/<活動フォルダ>/artifacts/auth-urls.txt | tee evidence/<活動フォルダ>/artifacts/cache-headers.txt`。`no-store`（理想）/`no-cache`/`private` が無い・`max-age>0`＝ディスクにキャッシュされ得る
2. ログアウト後にブラウザの「戻る」で認証済み画面が再表示されないか確認
3. 機微画面をディスクキャッシュから復元できないか確認する: 認証済みで機微画面を開いた後、DevTools→Network で当該レスポンスを再読込し `(from disk cache)` と出るか、または about:cache（Firefox）/ ブラウザのキャッシュ保存先に当該 URL のエントリが残るか。残る＝ログアウトや別ユーザでもディスクから中身を復元され得る（共用端末で漏えい）
4. 機微画面でキャッシュ抑止がない場合、共用端末での漏えいリスクとして finding に

## 使用ツール

- curl
- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: 機微画面の応答に Cache-Control: no-store（必要なら no-cache, must-revalidate）が付いている。
- **fail**: 認証後の画面がキャッシュされ、ログアウト後に戻るボタンや履歴から内容を再表示できる。
- 補足: 実機で「ログアウト→戻る」を試すのが最も伝わる証拠になる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`, `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-06, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）
- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/06-Testing_for_Browser_Cache_Weaknesses
