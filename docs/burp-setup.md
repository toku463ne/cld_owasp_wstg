# Burp Suite の準備（初めての人向け）

カードの「Burp で捕捉」「Burp Repeater」を実施できる状態にするまでの手順。
画面名は Kali の `burpsuite`（Community 版・2024 年以降の UI）に合わせている。

- [1. Burp を起動して対象に届くか確かめる](#1-burp-を起動して対象に届くか確かめる)
- [2. 内蔵ブラウザで使う（まずこれ）](#2-内蔵ブラウザで使うまずこれ)
- [3. 普段のブラウザを Burp に通す（reCAPTCHA / ボット検知で弾かれるとき）](#3-普段のブラウザを-burp-に通すrecaptcha--ボット検知で弾かれるとき)
- [4. 例: WSTG-ATHN-01 の「認証情報送信リクエストを捕捉」](#4-例-wstg-athn-01-の認証情報送信リクエストを捕捉)
- [困ったとき](#困ったとき)

仕組み: ブラウザの通信を Burp（`127.0.0.1:8080`）に通し、Burp が中継しながら全部を
**Proxy → HTTP history** に記録する。HTTPS も Burp がいったん復号するので中身が見える。

```
ブラウザ ──▶ Burp (127.0.0.1:8080) ──▶ （社内プロキシ）──▶ 対象サイト
               └ HTTP history に全部記録される
```

## 1. Burp を起動して対象に届くか確かめる

### 1-1. 起動

```bash
burpsuite
```

「Temporary project in memory」→ **Next** →「Use Burp defaults」→ **Start Burp**。

### 1-2. 待ち受けの確認

右上の歯車 **Settings** → **Tools** → **Proxy** の「Proxy listeners」に `127.0.0.1:8080` があり、
**Running** に✓が入っていること（既定で入っている）。

### 1-3. 社内プロキシが要る場合（上流プロキシ）

対象に社内プロキシ経由でしか届かないなら、**ブラウザではなく Burp に**設定する。

**Settings** → **Network** → **Connections** →「Upstream proxy servers」→ **Add**:

| 項目 | 値 |
|---|---|
| Destination host | `*` |
| Proxy host | `<社内プロキシのホスト>` |
| Proxy port | `3128` など |

- 対象が社内 IP で直接届く（`no_proxy` に入れている）なら不要。
- 混在するなら、対象ホストの行を**上**に置き Proxy host を**空欄**にする（そのホストだけ直接接続）。
  ルールは上から照合される。

### 1-4. curl で疎通確認（ブラウザより先に）

```bash
curl -x http://127.0.0.1:8080 -k -sI https://<target>/
```

応答ヘッダが返り、Burp の **Proxy → HTTP history** に行が増えれば Burp 経由の接続はできている。
`502` や `Unknown host` なら 1-3 を見直す。

## 2. 内蔵ブラウザで使う（まずこれ）

1. **Proxy → Intercept** タブで「**Intercept is off**」になっていることを確認する。
   on のままだとリクエストが Burp で止まり、ページが読み込み中のままになる（一番つまずく所）。
   HTTP history は off でも記録される。
2. 同じ画面の **Open browser** を押す。プロキシ設定・CA 証明書が済んだ Chromium が開く。
3. 対象を開き、HTTP history に行が増えれば準備完了。

root で使っていて内蔵ブラウザが起動しない場合は、**Settings → Tools → Burp's browser** の
「Allow Burp's browser to run without a sandbox」に✓を入れる。

## 3. 普段のブラウザを Burp に通す（reCAPTCHA / ボット検知で弾かれるとき）

内蔵ブラウザは「作ったばかりで履歴のない、自動操作の印が付いたブラウザ」なので、
reCAPTCHA やボット検知（Cloudflare 等）にボットと判定されてログインできないことがある。
そのときは**本物の Firefox の通信を Burp に通し、CAPTCHA は人が解く**。

ブラウザ側で要る準備は2つ:

- **(A) 通信の行き先を Burp にする**（プロキシ設定）
- **(B) Burp の CA 証明書を信頼させる**（入れないと HTTPS のサイトが証明書エラーで開けない）

Chrome はブラウザ単独のプロキシ設定がなく Windows 全体の設定を使うので、**Firefox を使う**のが簡単。

### 3-1. 検査専用の Firefox プロファイルを作る（推奨）

Burp の CA 証明書を普段使いのプロファイルに入れっぱなしにしないため、専用のプロファイルを作る。

1. アドレスバーに `about:profiles` →「**新しいプロファイルを作成**」→ 名前（例: `wstg`）を付けて完了。
2. 一覧の `wstg` の「**新しいブラウザーでプロファイルを起動**」で開く。以下はこのウィンドウで行う。

本物の Firefox なので大抵はこれで reCAPTCHA を通る。それでも弾かれるときだけ普段のプロファイルで試す。

### 3-2. (A) 行き先を Burp にする

#### 方法1: Firefox 標準の設定（拡張機能なし・おすすめ）

1. ≡ メニュー → **設定** →「一般」の一番下「ネットワーク設定」の **接続設定...**
2. 「**手動でプロキシーを設定する**」を選ぶ。
   - HTTP プロキシー: `127.0.0.1`　ポート: `8080`
   - 「**このプロキシーを HTTPS でも使用する**」に✓
3. **OK**。

検査専用プロファイルなら戻す必要はない（普段のプロファイルは影響を受けない）。

#### 方法2: FoxyProxy（切り替えを楽にしたいとき）

**FoxyProxy は、ブラウザのプロキシ設定をワンクリックで切り替える拡張機能**。必須ではない。
普段のプロファイルで Burp 経由と直接を行き来するなら、設定画面を往復せずに済む。

1. Firefox のアドオンサイトで「**FoxyProxy Standard**」を追加。
2. ツールバーの FoxyProxy アイコン → **Options** → **Proxies** → **Add**:
   Title `Burp` / Type `HTTP` / Hostname `127.0.0.1` / Port `8080` → **Save**。
3. 以後はアイコンから `Burp`（Burp 経由）と `Disable`（元に戻す）を選ぶだけ。

### 3-3. (B) Burp の CA 証明書を入れる

1. Burp を起動した状態で、3-2 の Firefox で `http://burp` を開く。
2. 右上の **CA Certificate** を押し、`cacert.der` を保存する。
3. **設定** → **プライバシーとセキュリティ** →「証明書」の **証明書を表示...** →
   **認証局証明書** タブ → **読み込む...** → `cacert.der` を選ぶ。
4. 「**この認証局によるウェブサイトの識別を信頼する**」に✓ → **OK**。

確認: `https://<target>` を開いて証明書エラーが出ず、Burp の **Proxy → HTTP history** に
行が増えれば成功。

### 3-4. reCAPTCHA があるログインでの流れ

1. Burp の **Proxy → Intercept** が **off** であることを確認。
2. 3-2 の Firefox でログイン画面を開き、**reCAPTCHA を自分で解いて**ログインする。
3. Burp の HTTP history にログインの `POST` が残る（本文には ID・パスワードと
   `g-recaptcha-response=...` が入っている）。

できること・できないこと:

| | 可否 | 理由 |
|---|---|---|
| ログイン POST を**見て判定**（ATHN-01 等） | ✅ | 記録を見るだけ |
| ログイン**後**のリクエストを Repeater / Intruder で再送 | ✅ | セッション Cookie で認証されている |
| ログイン POST そのものを Repeater で再送 | ❌ | reCAPTCHA のトークンは1回限り・約2分で失効 |
| ログインの連続試行（ATHN-03 のロックアウト等） | ❌ | CAPTCHA があること自体を観察として記録する |

Burp を介さず curl で回したいときは、README「Burp のブラウザが reCAPTCHA / ボット検知で
弾かれるとき」の 2・3（Cookie の書き出し / Copy as cURL）を使う。

これは**人が正規に取得したセッションをツールに渡し直すだけ**で、reCAPTCHA を突破しているわけではない。
CAPTCHA そのものの強度・レート制限は `WSTG-ATHN-*` / `WSTG-BUSL-07` の観点で別に評価する。

## 4. 例: WSTG-ATHN-01 の「認証情報送信リクエストを捕捉」

1. 2 または 3 のブラウザで、**テスト用アカウント**でログインする。
2. **Proxy → HTTP history** で **Method** 列の見出しを押して並べ替え、ログイン直後の `POST`
   （`/login`・`/api/auth` など）を選ぶ。見つけにくければ上部の Filter 欄に `password` 等の
   パラメータ名を入れて絞り込む。
3. 下の **Request** ペインを **Raw** 表示にして確認する:

| 確認項目 | 見る場所 | pass | fail |
|---|---|---|---|
| 送信先 | 一覧の **Host** 列 | `https://…` | `http://…` |
| メソッド | Raw の1行目 | `POST /login HTTP/…` | `GET /login?user=…&password=…` |
| 資格情報の位置 | Raw の空行より下（本文） | `username=…&password=…` や JSON | URL のクエリに載っている |

4. 直前の行も見て、ログイン画面自体が `https` で配信されているか確認する。
5. 判定の証跡を残す: その行を右クリック →「**Save item**」→「Base64-encode requests and responses」は
   ✓のまま → 活動フォルダの `artifacts/login-item.xml` として保存する。Raw のコピーには https かどうかが
   出ないので、URL・protocol まで残る Save item を使う。保存後に
   `uv run scripts/run_activity.py <フォルダ> --only WSTG-ATHN-01:3` を実行すると、protocol・method・
   URL と本文のパラメータ名が `artifacts/login-check.txt` に抜き出される（値は出さない）。
   XML にはパスワードも入るので evidence の外に出さない。スクリーンショットを貼るときは
   パスワードを塗りつぶす。`run.yaml` の `finding` には要約だけ書く（例:「ログインは https の POST 本文で送信」）。

## 困ったとき

| 症状 | 原因と対処 |
|---|---|
| ページがずっと読み込み中 | **Proxy → Intercept** が on。off にする |
| Burp を閉じたらネットにつながらない | ブラウザのプロキシ設定が Burp のまま。3-2 の設定を戻す（FoxyProxy なら `Disable`） |
| 「接続は安全ではありません」 | CA 証明書が入っていない。3-3 をやり直す |
| HTTP history に何も出ない | ブラウザが Burp を通っていない。1-4 の curl が記録されるか、3-2 の設定を確認 |
| `502` / `Unknown host` | Burp から対象に届いていない。1-3 の上流プロキシを確認 |
| 内蔵ブラウザが起動しない | 2 の「without a sandbox」を有効にする |
| Windows のブラウザから `http://burp` が開けない（Burp は WSL 内） | 通常は `127.0.0.1:8080` で届く。届かなければ Burp を Kali 側の Firefox で使う |
| 会社 PC で拡張機能・証明書を入れられない | ポリシーの制限。README の Cookie 書き出し / Copy as cURL の方法に切り替える |
