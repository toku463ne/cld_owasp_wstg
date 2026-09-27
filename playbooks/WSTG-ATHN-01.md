# WSTG-ATHN-01 — Testing for Credentials Transported over an Encrypted Channel

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

資格情報が暗号化された経路でのみ送信されているかを確認する。

WSTG の Test Objectives:

- Assess whether any use case of the web site or application causes the server or the client to exchange credentials without encryption.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ログイン画面を HTTP で開いたときの応答を保存: `curl -s -m 10 -o /dev/null -D - http://target/login | tee evidence/<サイト>/<活動フォルダ>/artifacts/login-http.txt`。30x で `Location: https://` へ飛ぶ＝HTTPS 強制。200 で画面が返る＝平文で資格情報を入力させうる
2. ログイン送信を HAR に保存する（手動）: 検査用の Firefox でログイン画面を開く → F12 → Network タブの「Preserve log」に✓（リダイレクトで消えないように）→ テスト用アカウントで（reCAPTCHA は自分で解いて）ログイン → ログイン送信の行（多くは POST）が出たら一覧のどれかを右クリック →「Save all as HAR」（Firefox は「すべてを HAR 形式で保存」）→ evidence/<サイト>/<活動フォルダ>/artifacts/login.har として保存。値も入るので evidence の外に出さない
3. 手順2 の HAR からログイン送信の送信先・メソッド・資格情報の位置を抜き出す: `test -s evidence/<サイト>/<活動フォルダ>/artifacts/login.har || exit 75; jq -r '[ .log.entries[] | select(.request.method=="POST") | .request | (.postData.params // [] | map(.name)) as $pn | select( (($pn + [(.postData.text // "")]) | join(" ")) | test("pass|pwd|login|user|mail";"i")) ] as $c | if ($c|length)==0 then "ログイン POST が HAR に無い（Preserve log を付けて撮り直す）" else $c[0] as $r | "protocol: " + ($r.url | capture("^(?<s>[a-z]+)://").s), "method: POST", "URL: " + ($r.url | sub("[?].*$";"")), "URL 中の資格情報らしき名前: " + (($r.queryString // []) | map(.name) | map(select(test("user|login|mail|pass|pwd";"i"))) | join(" ")), "本文のパラメータ名: " + ((($r.postData.params // []) | map(.name)) + (($r.postData.text // "") | [scan("[\"&,{]\\s*\"?([A-Za-z0-9_.-]+)\"?\\s*[=:]")] | flatten) | unique | join(" ")) end' evidence/<サイト>/<活動フォルダ>/artifacts/login.har | tee evidence/<サイト>/<活動フォルダ>/artifacts/login-check.txt`。protocol が https・method が POST・URL 中の名前が空・本文のパラメータ名に ID/パスワードがある＝pass
4. HTTPS のログイン画面のフォーム送信先を確認: `curl -s -m 10 https://target/login | grep -oiE '<form[^>]*action=[^ >]*' | tee evidence/<サイト>/<活動フォルダ>/artifacts/login-form-action.txt`。action が `http://` で始まる＝HTTPS 画面から平文へ送信（fail）。0 件は JS で送る画面なので手順3 で判断
5. ログイン後も平文で資格情報を送っていないか見る（手動）: F12 → Network タブのフィルタ欄に手順3 で出たパスワードのパラメータ名を入れ、Domain/URL 列が `http://`（暗号化なし）の行が無いか、パスワード変更・再認証など別の送信も https・POST 本文かを確認する

## 使用ツール

- curl
- ブラウザ開発者ツール
- jq

## 判定基準（pass / fail の見分け）

- **pass**: ログイン画面と送信先の両方が HTTPS で、HTTP へのフォールバックがない。
- **fail**: 資格情報が HTTP で送信される、HTTPS 画面から HTTP へ POST している、または GET のクエリに載っている。
- 補足: ログイン URL（`/login`）は対象に合わせて record.html のコマンド編集（run.yaml の cmd_overrides）で直す。手順1 が空（80 番が閉じていて接続できない）は平文で入力させようがないので pass 側。手順2 は Burp を使わず検査用ブラウザの F12（Network → Save all as HAR）で撮る。Burp をプロキシに挟むと reCAPTCHA/ボット検知に弾かれてログインできない対象があるため（Burp を使うなら内蔵ブラウザの F12 でも同じ HAR が撮れる）。HAR には URL・method・本文がそのまま入るので、手順3 は protocol/method/URL と本文のパラメータ「名」だけを抜き出す（値は出さない）。HAR にはパスワードも入るため evidence の外に出さず、テスト用アカウントを使う。スクリーンショットはパスワードを塗りつぶす。Burp の起動・接続や F12 の詳しい手順は docs/burp-setup.md。リダイレクト前の最初のリクエストが平文かは手順1、HTTPS 画面から HTTP への送信は手順3・4 で見る。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/01-Testing_for_Credentials_Transported_over_an_Encrypted_Channel
