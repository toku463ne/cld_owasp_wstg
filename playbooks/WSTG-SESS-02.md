# WSTG-SESS-02 — Testing for Cookies Attributes

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

セッション Cookie の属性が適切に設定されているかを確認する。

WSTG の Test Objectives:

- Ensure that the proper security configuration is set for cookies.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ログイン応答のヘッダを evidence/<活動フォルダ>/artifacts/login-headers.txt に保存（curl -i -c evidence/<活動フォルダ>/artifacts/cookies.txt でログインを実行してヘッダを残すか、Burp/DevTools の応答からコピー）した上で、発行 Cookie の属性を抽出: `test -s evidence/<活動フォルダ>/artifacts/login-headers.txt || exit 75; grep -iE '^set-cookie:' evidence/<活動フォルダ>/artifacts/login-headers.txt || [ $? -eq 1 ]`（保存前に一括実行すると「入力待ち」で飛ばし、保存後の再実行で走る）。出てきた Set-Cookie 行を1つずつ下の属性で確認する
2. 手順1で保存した Set-Cookie の属性欠落を自動抽出する: `grep -iE '^set-cookie:' evidence/<活動フォルダ>/artifacts/login-headers.txt | while read -r c; do for a in Secure HttpOnly SameSite; do echo "$c" | grep -qi "$a" || echo "[要確認] $a なし: $(echo "$c" | cut -c1-70)"; done; done | tee evidence/<活動フォルダ>/artifacts/cookie-attrs.txt`。出力が空＝全 Cookie に3属性あり。行が出たセッション/認証系 Cookie は `Secure`（HTTPS 限定）・`HttpOnly`（JS 遮断）・`SameSite`（Lax/Strict）のいずれかが欠けている（CSRF/その他の非機微 Cookie は SameSite 無しでも許容の場合があるので finding では Cookie 名で区別する）
3. `Domain`/`Path` が過度に広くないか、`__Host-`/`__Secure-` prefix の適否を確認
4. セッション Cookie と CSRF/その他 Cookie で属性が適切に分かれているか確認

## 使用ツール

- curl
- Burp Suite
- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: Secure・HttpOnly が付き、SameSite が Lax 以上、Domain/Path が必要最小限。
- **fail**: Secure か HttpOnly が欠けている、SameSite=None なのに用途上不要、Domain が広すぎる。
- 補足: 認証済みで発行される Cookie を対象にする。トラッキング用 Cookie と混同しない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`, `artifacts/session-trace.burp`, `artifacts/token-samples.txt`
- `covers:` — `{id: WSTG-SESS-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）
- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/02-Testing_for_Cookies_Attributes
