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

1. ログイン画面を HTTP で開いたときの応答を保存: `curl -s -m 10 -o /dev/null -D - http://target/login | tee evidence/<活動フォルダ>/artifacts/login-http.txt`。30x で `Location: https://` へ飛ぶ＝HTTPS 強制。200 で画面が返る＝平文で資格情報を入力させうる
2. Burp でログイン送信を保存する（手動）: Proxy → Intercept が「Intercept is off」か確認 →「Open browser」でテスト用アカウントでログイン → Proxy → HTTP history で Method 列を押して並べ替え、ログイン送信の行（多くは POST）を右クリック →「Save item」→ 「Base64-encode requests and responses」は✓のまま → evidence/<活動フォルダ>/artifacts/login-item.xml として保存
3. 手順2 の保存から送信先・メソッド・資格情報の位置を抜き出す: `test -s evidence/<活動フォルダ>/artifacts/login-item.xml || exit 75; { grep -oE '<(protocol|method|url)>(<!\[CDATA\[)?[^]<]*' evidence/<活動フォルダ>/artifacts/login-item.xml | sed -E 's/<!\[CDATA\[//; s/^<([a-z]+)>/\1: /'; echo "URL 中の資格情報らしき名前: $(grep -oE '<url>[^>]*>' evidence/<活動フォルダ>/artifacts/login-item.xml | grep -oiE '[?&][^=&]*(user|login|mail|pass|pwd)[^=&]*=' | tr '\n' ' ')"; echo "本文のパラメータ名: $(sed -nE 's/.*<request base64="true"><!\[CDATA\[([^]]*)\]\]>.*/\1/p' evidence/<活動フォルダ>/artifacts/login-item.xml | base64 -d | sed '1,/^\r*$/d' | grep -oE '(^|[&{,])[[:space:]]*"?[A-Za-z0-9_.-]+"?[[:space:]]*[=:]' | tr -d '"=:{,&[:blank:]' | sort -u | tr '\n' ' ')"; } | tee evidence/<活動フォルダ>/artifacts/login-check.txt`。protocol が https・method が POST・URL 中の名前が空・本文のパラメータ名に ID/パスワードがある＝pass
4. HTTPS のログイン画面のフォーム送信先を確認: `curl -s -m 10 https://target/login | grep -oiE '<form[^>]*action=[^ >]*' | tee evidence/<活動フォルダ>/artifacts/login-form-action.txt`。action が `http://` で始まる＝HTTPS 画面から平文へ送信（fail）。0 件は JS で送る画面なので手順3 で判断
5. ログイン後も平文で資格情報を送っていないか見る（手動）: Burp の Proxy → HTTP history 上部のフィルタ欄に手順3 のパスワードのパラメータ名を入れ、Host 列が `http://` の行が無いか、パスワード変更・再認証など別の送信も https・POST 本文かを確認

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: ログイン画面と送信先の両方が HTTPS で、HTTP へのフォールバックがない。
- **fail**: 資格情報が HTTP で送信される、HTTPS 画面から HTTP へ POST している、または GET のクエリに載っている。
- 補足: ログイン URL（`/login`）は対象に合わせて record.html のコマンド編集（run.yaml の cmd_overrides）で直す。手順1 が空（80 番が閉じていて接続できない）は平文で入力させようがないので pass 側。手順2 の「Save item」は URL・protocol（http/https）・method とリクエスト全体を XML で残すので、Raw のコピーより判定に向く（Raw には https かどうかが出ない）。XML には入力したパスワードも入るため evidence の外に出さず、テスト用アカウントを使う。スクリーンショットはパスワードを塗りつぶす。Burp の起動・接続は docs/burp-setup.md、内蔵ブラウザが reCAPTCHA で弾かれるときは同 3 章（普段の Firefox を Burp に通す）。リダイレクト前の最初のリクエストが平文になっていないかは手順1、HTTPS 画面から HTTP への送信は手順3・4 で見る。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/01-Testing_for_Credentials_Transported_over_an_Encrypted_Channel
