# WSTG 実施支援システム

OWASP Web Security Testing Guide (WSTG) **v4.2** を、**収集アクティビティ単位**で
回すための方法論とツール一式。

- WSTG 項目を1件ずつ潰すのではなく、1回の収集（例: 「認証済みクロール」）で
  該当する複数の WSTG-ID にまとめてチェックを入れる。
- 管理は **Web 一本**（`scripts/serve_record.py`）。タスク（指示書＋チェックリスト）・WSTG 索引
  （どこまで完了したか）・所見（CVSS 付き）・実施記録（エビデンス）を1つのサイトで辿る。
  チームで使うときは共用 Kali 上で nginx（TLS＋認証）の後ろに置く。
- 実エビデンスはこのリポジトリに入れない（`evidence/` は `.gitignore` 済み）。

**まず Web を開く:** `uv run scripts/serve_record.py --open` → 「タスク」を上から消化する。
同じ内容のテキスト版が `TASKS.md`、端末での進捗確認は `uv run scripts/tasks.py`。

## 全体像

```
WSTG 原文 ──▶ matrix/wstg_tests.yaml ──┐
(公開情報)                              ├─▶ playbooks/WSTG-*.md（実施カード）
matrix/criteria.yaml（判定基準・手書き）─┘
                                        
matrix/coverage.yaml（アクティビティ定義・実施順）
   │ tasks.py --write ─▶ TASKS.md（実施順チェックリスト）
   │ new_activity.py
   ▼
evidence/<activity>[-<target>]-<date>/
   ├ cmd/ + artifacts/（run_activity.py が手順を実行＝純粋なエビデンス）
   ├ record.html ─(iframe参照)▶ cmd/・artifacts/ の各ファイル（evidence.js はメタデータのみ）
   └ run.yaml（covers に判定＝verdict と判定理由）
evidence/_findings/F-*.md（所見。WSTG と多対多・CVSS ベクトル・エビデンスへのパス）
evidence/_state/checks.yaml（タスクの手動チェック）
   │
   ▼ serve_record.py（127.0.0.1）◀── nginx（TLS＋認証）◀── チーム
   /           ダッシュボード       /tasks      指示書＋チェックリスト
   /wstg/      WSTG 索引（完了状況）/findings/  所見（深刻度は CVSS から自動）
   /<act>/record.html 実施記録      /export.csv 一覧（外に出すとき）
```

## セットアップ

Python は [uv](https://docs.astral.sh/uv/) で管理する（`pyproject.toml` + `uv.lock` +
`.python-version`。Python 3.12・PyYAML のみ）。

```bash
uv sync                 # .venv を作って依存を入れる（Python も uv が用意する）
./scripts/selftest.sh   # ツールが動くことを確認
./scripts/fetch_wstg.sh # WSTG v4.2 原文を docs/owasp/ へ（任意・追跡されない）
```

以降スクリプトは `uv run scripts/xxx.py` で実行する（仮想環境の有効化は不要）。
uv を入れられない会社PC では `pip install pyyaml` して `python scripts/xxx.py` でも動く
（依存は PyYAML のみ、Python 3.10 以上）。

原文が無くても、`matrix/wstg_tests.yaml` と `playbooks/` は生成済みなので
日々の運用（アクティビティ作成〜CSV 出力）は動く。原文が要るのは再生成のときだけ。

## プロキシ配下での準備

社内プロキシ越しに検査する場合、`amass` / `theHarvester` / `curl` などが外に出られずに
「0 件」と見分けのつかない失敗をする。実施前に環境変数を通しておく。

```bash
PROXY="http://proxy.example.local:3128"   # 認証ありなら http://user:pass@host:port
NOPROXY="localhost,127.0.0.1,::1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,.local"

# 大文字しか見ないツール（Go 製の amass / httpx など）があるので両方入れる
cat >> ~/.bashrc <<EOF
export http_proxy=$PROXY https_proxy=$PROXY ftp_proxy=$PROXY
export HTTP_PROXY=\$http_proxy HTTPS_PROXY=\$https_proxy
export no_proxy=$NOPROXY NO_PROXY=$NOPROXY
EOF
. ~/.bashrc && env | grep -i proxy

# root / apt / git / curl は別に要る
sudo tee /etc/apt/apt.conf.d/95proxy >/dev/null <<EOF
Acquire::http::Proxy "$PROXY";
Acquire::https::Proxy "$PROXY";
EOF
git config --global http.proxy "$PROXY"
printf 'proxy = %s\n' "$PROXY" >> ~/.curlrc

# sudo は既定で環境変数を捨てる（env_reset）。内部で sudo を呼ぶツール用に必須
echo "Defaults env_keep += \"http_proxy https_proxy ftp_proxy no_proxy HTTP_PROXY HTTPS_PROXY NO_PROXY\"" \
  | sudo tee /etc/sudoers.d/proxy
sudo chmod 440 /etc/sudoers.d/proxy
sudo visudo -c                      # 構文チェック（壊すと sudo が使えなくなるので必ず）

# 保険: root 側にも直接持たせる（sudo 経由の curl が env を見ない実装のとき）
printf 'proxy = %s\n' "$PROXY" | sudo tee /root/.curlrc >/dev/null
sudo chmod 600 /root/.curlrc

curl -sI https://crt.sh | head -1   # 疎通確認（一般ユーザ）
sudo env | grep -i proxy            # 疎通確認（sudo に環境変数が渡っているか）
sudo curl -sI https://github.com | head -1
```

- **`sudo` は環境変数を落とす**。`sudo -E nmap ...` で実行するか、上の `env_keep` を入れる
- **amass は内部で `sudo` を呼ぶ**。Kali のラッパーが起動時に libpostal データを
  `sudo curl` で github から取りに行くため、`env_keep` が無いと必ずここで固まる
  （`curl: (28) Failed to connect to github.com:443` + `[sudo] password for ...`）。
  プロキシが github を通さない環境では、ラッパーではなく amass 本体を直接実行して
  このチェックを飛ばす（`head -40 "$(command -v amass)"` で本体のパスを確認）。
  libpostal は住所パース用で `enum -passive` のサブドメイン列挙には要らない
- **theHarvester は環境変数を見ない**（内部の aiohttp が `trust_env` を有効にしていない）。
  `/etc/theHarvester/proxies.yaml` に `http:` のリストでプロキシを書き、**`-p` を付けて実行する**。
  付け忘れると全ソースが0件になり（crtsh は `Expected object or value`）、
  「何も無い」と見分けがつかない。起動時の `Read proxies.yaml from ...` は `-p` の有無に
  関わらず出るので、動作証拠にならない
- **Burp 経由**にするなら `https_proxy=http://127.0.0.1:8080`（Burp CA を入れていなければ `curl -k`）
- **DNS とポートスキャンはプロキシを通らない**。`dig` / `nmap` の名前解決・スキャンは直接出るので、
  そこが塞がっているならプロキシとは別に経路の手当てが要る
- **amass v5 は外向き UDP/53 が無いと起動しない**（このため手順は `subfinder` に差し替えてある。
  subfinder は HTTPS の API 主体で UDP/53 は要らないが、環境変数のプロキシを見ないので
  `-proxy "$https_proxy"` を明示する。付けないと全ソースが timeout して0件になる
  ＝実測で `-proxy` なし0件/約90秒・あり28件/約32秒）。engine が起動時に bgp.tools を
  自前のリゾルバ（公開 DNS）で解決するため、53 が塞がれた社内網では
  `Failed to start the engine: failed to obtain the BGPTools IP address` となり、
  `amass enum` は 60 秒でタイムアウトする（`amass engine` を単体起動すると生のエラーが見える）。
  v5.1.1 にリゾルバを差し替える設定は無い。amass をどうしても使いたい場合以外は
  `subfinder` と crt.sh / hackertarget（`playbooks/WSTG-INFO-01.md` の手順3）で足りる。
  どうしても要るなら公開 DNS 宛を社内 DNS へ DNAT する手はあるが、DNS の挙動を
  歪めるので amass を回す間だけにし、戻したことを記録に残す
- **原則: インターネット接続が要るコマンドはすべてプロキシ経由**にする。どこへ出るかで2種類:
  - 外部の公開ソース（crt.sh / hackertarget / subfinder API、NVD、retire.js の DB 更新）は
    常にプロキシ経由。
  - **検査対象そのものがプロキシ越しにしか届かない**（インターネット公開の対象を社内網から
    検査する）ときは、対象へ出るアクティブスキャンもプロキシ経由にする。逆に**対象が
    社内 IP で直接届く**なら `no_proxy` に入れて直行させる（この場合 `https_proxy` を
    未設定にするか、その対象を回す間だけ外す）。
- **多くのツールは環境変数（`http_proxy`/`https_proxy`）を見ない**ので、明示フラグが要る。
  criteria の手順は `${https_proxy:+<flag>}` で書いてあり、**`https_proxy` が設定されている
  ときだけ**プロキシフラグが付く（未設定なら直行）。対応表:

  | ツール | プロキシ指定 | env を見るか |
  |---|---|---|
  | `curl` / `wget` / `git` | 環境変数 | ○（`~/.curlrc` 併用） |
  | `theHarvester` | `-p`＋`/etc/theHarvester/proxies.yaml` | × |
  | `subfinder` | `-proxy "$https_proxy"` | × |
  | `nikto` | `-useproxy "$https_proxy"` | × |
  | `testssl.sh` | `--proxy=auto`（env を使う）または `--proxy host:port` | ×（auto 指定時のみ） |
  | `sslyze` | `--https_tunnel="$https_proxy"` | × |
  | `ffuf` | `-x "$https_proxy"` | × |
  | `sqlmap` | `--proxy="$https_proxy"` | × |
  | `nmap` | **不可**（下記） | — |

- **`nmap` は HTTP プロキシを通せない**（ポートスキャン/NSE は生ソケット）。対象がプロキシ越しに
  しか届かないなら、`nmap` は経路の手当て（VPN・踏み台・ルーティング）が別途要る。TCP connect
  スキャン（`-sT`）に限れば `proxychains nmap -sT ...` で HTTP CONNECT 経由にできるが遅く、
  UDP/生パケット系（`-sU`・`-sS`・多くの NSE）は通らない。プロキシ越しの対象では
  `nmap` の結果が空でも「閉じている」と即断しない。

ツールが 0 件を返したときは、まず疎通を疑う。「何も無い」と「収集に失敗した」は別で、
後者を `pass` にしてはいけない（`playbooks/WSTG-INFO-01.md` の疎通確認の手順を参照）。

## 対象が非力で落ちる / 504 になるとき（ゆっくり実行）

検証環境が低スペックだと、`nikto` / `ffuf` / `sqlmap` のようなアプリ層スキャナの連打で
CPU 100%・502/503/504 になることがある。**環境変数 `WSTG_PAUSE`（リクエスト間に空ける秒数）**
を設定すると、対象を叩くツールにその待ちが入る（`${WSTG_PAUSE:+...}` で書いてあり、未設定なら
通常速度、設定時だけペースが落ちる）。プロキシの `${https_proxy:+...}` と同じ仕組み。

```bash
export WSTG_PAUSE=2          # まず2秒。まだ落ちるなら 3〜5 に上げる
uv run scripts/run_activity.py evidence/<活動フォルダ> --only WSTG-CONF-01:3   # nikto をゆっくり
```

| ツール | `WSTG_PAUSE` の効き方（設定時） |
|---|---|
| `nikto` | `-Pause <秒>`（各リクエスト間の待ち）。加えて `-maxtime 30m` で打ち切り、`-T` で試験を限定 |
| `ffuf` | `-p <秒>` の待ち＋`-t 1`（並列を1に。既定40並列が飽和の主因） |
| `sqlmap` | `--delay <秒>`（`--threads` は上げない） |
| `nmap` | `WSTG_PAUSE` は未対応。ポートスキャンの負荷は `--max-rate <n>`（例 `--max-rate 100`）や `-T2` で下げる。`-p-` に `--scan-delay` を付けると事実上終わらないので使わない |

- 504 が出始めたら、まず今のスキャンを止めて `WSTG_PAUSE` を上げてから `--only` でその手順だけ回し直す。
- それでも厳しい対象は、ワードリストを小さくする・`-T`（nikto）で試験カテゴリを絞る・実施時間帯を
  ずらす、を併用する。落ちたこと自体（可用性の弱さ）も観察として `notes.md` / finding に残す。

## Burp のブラウザが reCAPTCHA / ボット検知で弾かれるとき

カードの多くは「Burp で捕捉」「Burp Repeater」と書いてあるが、**Burp 内蔵ブラウザは
自動化フラグ付きの使い捨て Chromium** なので、reCAPTCHA やボット検知（Cloudflare 等）に
引っかかってログインすら通らないことがある。Burp を捨てる必要はなく、**「普段のブラウザで
人間として一度通し、その後の中身をツールに渡す」** に切り替える。上流ほど確実:

1. **普段のブラウザ＋プロキシ設定（まずこれ）** — Burp 内蔵ブラウザではなく、日常使いの
   Firefox/Chrome（本物のプロファイル・UA・Cookie）を FoxyProxy 等で Burp（`127.0.0.1:8080`）に
   向ける。Burp の CA 証明書を入れておく（`http://burp` → CA Certificate、Firefox は
   `about:config` の `security.enterprise_roots.enabled=true` かブラウザに手動インポート）。
   本物のブラウザ指紋なので弾かれにくく、通信は今までどおり Burp の Proxy history に溜まる。
   - reCAPTCHA が出る画面（主にログイン）だけこのブラウザで**人間が解く**。解いた後の
     認証済みリクエストは Repeater/Intruder にそのまま送れる。
2. **CAPTCHA は人が一度だけ解き、セッションを引き継ぐ** — ログイン（＋CAPTCHA）を普段の
   ブラウザで済ませ、**発行された Cookie を書き出して以降の検査に使い回す**。Burp を介さず
   `curl` / `run_cmd.py` で回せるので、多くの手順（ATHN-06・ATHZ 系・SESS 系の「認証済みで
   叩く」部分）はこれで自動化できる:

   ```bash
   # 例: ブラウザで手動ログイン（CAPTCHA を解く）→ Cookie をエクスポート（拡張機能や
   #     DevTools→Application→Cookies）→ cookies.txt（Netscape 形式）に保存してから:
   uv run scripts/run_cmd.py evidence/<活動フォルダ> --slug authed-home \
     -- curl -s -b cookies.txt -D - https://target/mypage -o /dev/null
   ```

   Cookie の期限が切れたら、その画面だけブラウザで踏み直して cookies.txt を取り直す。
3. **DevTools「Copy as cURL」で1本だけ持ち出す** — 検査したいリクエストを普段のブラウザで
   起こし、DevTools→Network→対象→右クリック→**Copy as cURL** で丸ごと（Cookie・ヘッダ込み）
   コピーできる。`run_cmd.py <フォルダ> -- <貼り付けた curl>` で実行すれば、Burp ブラウザを
   使わずに Repeater 相当（ヘッダ改変・再送）ができ、出力が `cmd/` に純粋なエビデンスとして残る。
4. **どうしても Burp 内蔵ブラウザを使うなら** — Proxy → Options → **Miscellaneous** で内蔵
   ブラウザの起動オプションを調整する手はあるが、指紋の根本は変わらないので 1〜3 を優先する。

いずれも「対象そのものへの攻撃的入力」ではなく、**人間が正規に取得したセッション/リクエストを
ツールに渡し直す**だけなので、reCAPTCHA を回避（=突破）しているわけではない点に注意。
CAPTCHA そのものの強度・レート制限は別途 `WSTG-ATHN-*` / `WSTG-BUSL-07` の観点で評価する。

## 日々の流れ

Web の「タスク」（テキスト版は `TASKS.md`）を上から消化していく。1本のアクティビティで踏むのは 1〜2c、
区切りのたびに 3〜4 を回す。

### 1. アクティビティを開始する

```bash
uv run scripts/new_activity.py burp-crawl-authn
# -> evidence/burp-crawl-authn-20260908/{run.yaml,record.html,evidence.js,cmd/,artifacts/,notes.md}

# 複数サイトは --target で名前空間を分ける（手順のコマンドの target も置換される）
uv run scripts/new_activity.py recon-osint --target example.com
# -> evidence/recon-osint-example.com-20260913/
```

`burp-crawl-authn` は `matrix/coverage.yaml` に定義された収集アクティビティ ID の一例
（一覧は `uv run scripts/new_activity.py`〈引数なし〉または `matrix/coverage.md`）。

`run.yaml` の `covers:` には、そのアクティビティがカバーする WSTG-ID が
`matrix/coverage.yaml` から自動で入る（`verdict: todo`）。
`artifacts/` には、`coverage.yaml` の `outputs:` にある `.md` 成果物の雛形が
検索しやすいフォーマット（1観察=1行・列固定・`[角括弧]` タグ・WSTG-ID 列）で
用意される。雛形は `templates/artifacts/`（`<basename>` 専用が無ければ `_findings.md`）。
後から `grep -rn "\[creds\]" evidence/` や `grep -rn "WSTG-INFO-01" evidence/` で横断検索できる。

対応するプレイブックカード（`playbooks/WSTG-*.md`）を開きながら進める。
一覧は `playbooks/INDEX.md`、どのアクティビティが何を満たすかは `matrix/coverage.md`。

#### 対象が1つに決まっているなら一括で（`run_target.py`）

サイトを固定して全アクティビティを一気に回すときは `run_target.py` を使う。
`coverage.yaml` の順にフォルダ一式の作成（`new_activity`）とコマンド実行（`run_activity`）を
まとめて行う。**既定は「再開」と「エラーで停止」**なので、そのまま何度でも叩ける。

```bash
uv run scripts/run_target.py --target wwwtest.example.com          # 作成→実行を全部
uv run scripts/run_target.py --target wwwtest.example.com --list   # 実施予定を出すだけ
uv run scripts/run_target.py --target wwwtest.example.com --no-run # フォルダ作成だけ
uv run scripts/run_target.py --target wwwtest.example.com --only recon-osint,metafiles-crawl
```

- **作成済みは作り直さない**（既存フォルダはそのまま）。
- **前回 `exit_code` 0 で終わったコマンドはスキップ**して続きから進む（`--rerun-all` で全再実行）。
- **非0終了が出たらそこで打ち切る**（`--keep-going` で最後まで継続）。
  → エラーは `cmd/*.txt` の末尾と `matrix/criteria.yaml` の該当手順を直し、同じコマンドを
  もう一度叩けば、成功済みを飛ばして途中から再開する。
- 手動手順しか無いアクティビティはフォルダだけ用意される（コマンドは実行しない）。

個別に細かく回したいとき（手順を絞る・ドライラン等）は、下の `run_activity.py` を直接使う。

### 2. コマンド手順を wrapper で実行する（＝純粋なエビデンスを作る）

手順のコマンドは自分で打たず、wrapper に実行させる。手順は `matrix/criteria.yaml` から
毎回組み立て、target は `run.yaml` の対象に、出力先はこのフォルダの `artifacts/` に置換される。

```bash
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913            # コマンド手順を全部実行
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --list     # 手順一覧（実行しない）
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --only WSTG-INFO-02      # ID を絞る
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --only WSTG-INFO-02:4    # 手順を絞る
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --dry-run  # 実行内容の確認だけ
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --skip-done # 前回成功したコマンドは飛ばす（再開）
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --stop-on-error # 非0終了でそこで打ち切り
```

各コマンドは `bash` で1つずつ実行され、その出力が `cmd/<WSTG-ID>-s<n>-c<k>.txt` に残る
（本体コマンドの後に、取得できたかを見る `wc -l`/`head` の確認コマンドも別ファイルで走る）。
これが**純粋なエビデンス**で、ドキュメントには埋め込まない。record.html は手順ごとに
「コマンドの説明 → コマンド → その結果」を1対1で並べて表示する。
非0終了・空・HTML が返っていたら収集失敗なので、`pass` の根拠にしてはいけない。実行のたびに
`run.yaml` の `commands:` に記録が追記され、`evidence.js`（表示データ）が作り直される。

- 手動手順（Burp・ヒアリング・ブラウザ操作）は実行されない。`artifacts/manual-<WSTG-ID>-s<n>.txt`
  に、① 操作した URL・手順 ② 確認できたこと（無ければ「該当なし」）③ スクショのパス ④ 件数を書く。
- スクショは `save_shot.py` で `artifacts/` に保存する。`--wid` を付けると record.html の
  そのカードに `<img>` 参照で出る（差し替えはリロードで反映）。
  ```bash
  # 推奨: その場で範囲選択してキャプチャ（クリップボード不要・環境差に強い）
  uv run scripts/save_shot.py evidence/recon-osint-example.com-20260913 --wid WSTG-INFO-01 --grab
  # クリップボードの画像から（X11=xclip / Wayland=wl-paste を自動判定）
  uv run scripts/save_shot.py evidence/recon-osint-example.com-20260913 --wid WSTG-INFO-01
  ```
  スクショは WSTG-ID のカード上部に出る。`--step <n>` を付けるとその手順の直下に出る。
  端末が前面でブラウザが隠れるときは `--delay 3` で、待つ間に Alt+Tab で対象を前面へ。
  `--grab` は X11=maim/scrot/xfce4-screenshooter、Wayland=grim+slurp を自動判定
  （flameshot は選択画面が出ないことがあるので後回し。`--list-tools` で確認、`--tool` で指定）。
  クリップボード経由（`--grab` なし）は空のとき入っている型を表示して `--grab` を案内する
  （DE のスクショがファイル保存だとクリップボードには入らない）。
- 動的入力が要る手順（`hosts.txt`・`cookies.txt` を用意してからのループ等）は、先に入力を置いてから
  `--only` でその手順だけ回す。
- 単発の CLI を回して `cmd/` に残すだけなら、従来どおりロガーも使える:
  ```bash
  uv run scripts/run_cmd.py evidence/tls-scan-20260908 -- testssl.sh --quiet target.example
  ```

### 2b. Web で判定を書き、所見を作る

```bash
uv run scripts/serve_record.py --open        # http://127.0.0.1:8765/（127.0.0.1 のみ待受）
```

トップ（ダッシュボード）から、**タスク**・**WSTG 索引**・**所見**・各アクティビティの
**実施記録（record.html）** を辿る。ページは GET のたびにファイルから作り直すので、
`run.yaml` や所見ファイルをエディタで直してもリロードで反映される。

**record.html（WSTG-ID ごとのタブ）でできること**

- **判定**: 各タブの verdict（pass|fail|info|na|todo）と**判定理由**（1行。`run.yaml` の `finding`）を
  『保存』。`run.yaml` の該当ブロックだけをテキスト置換する（手で直接書いてもよい）。
- **所見**: タブ内の『＋ 所見を作成』、または各出力・スクショの『📎 所見に添付』（新規 or 既存の所見に追加）。
- **画像**: 手順ごとの枠をクリックして Ctrl+V（クリップボードのスクショを貼る）、ダブルクリックでファイル選択、
  ドラッグ＆ドロップ。`artifacts/shot-<WSTG-ID>-s<n>-<日時>.png` として保存され、その手順の直下に出る。
  ローカルモードでは『📷 この手順のスクショを撮る』（サーバ機の画面を範囲選択）も使える。
- **結果の貼り付け**: 各コマンド結果の『✎ 結果を貼る/編集』で `cmd/…txt` を直接編集できる
  （会社で network error になったコマンドを別環境で実行して貼る等。`cmd/`・`artifacts/` 直下の `.txt` のみ）。
- **深いリンク**: `record.html#WSTG-INFO-02/s5` で、そのタブのその手順に飛ぶ（所見・WSTG 索引からのリンクはこれ）。

`record.html` はファイルをダブルクリック（`file://`）でも閲覧だけはできる（編集・添付・画像追加は Web のみ）。
エビデンス本体（各コマンドの出力）は evidence.js に複製せず `cmd/`・`artifacts/` のファイルを `<iframe>` で
直接参照する。上流（`criteria.yaml` 等）を更新して手順が変わっても `gen_record.py` で作り直すだけでよく、
過去のエビデンスをコピーし直す必要はない。

**判定理由（`finding`）は要約のみ**。生トークン・資格情報・生ホスト名は書かず、エビデンスのパスで示す。
複数行にすると `run.yaml` では YAML ブロック（`finding: |`）、CSV では1行に畳まれる。

### 2c. 所見（Finding）と深刻度（CVSS v3.1）

所見は **1件 = 1ファイル**（`evidence/_findings/F-001.md`）。WSTG-ID とは**多対多**で、
1つの WSTG に複数の所見を、1つの所見に複数の WSTG・複数アクティビティのエビデンスを紐づけられる。
中身は front matter（タイトル・状態・CVSS ベクトル・指標ごとの判断理由・WSTG・エビデンスのパス）＋本文
（概要・再現手順・影響・対策案）。

- **深刻度は人が選ばない。** 所見フォームの 8 問（起こりやすさ＝攻撃元・複雑さ・権限・ユーザ関与、
  影響＝スコープ・機密性・完全性・可用性）に答えると CVSS v3.1 の基本スコアを計算し、
  Critical ≥9.0 / High ≥7.0 / Medium ≥4.0 / Low ≥0.1 / 情報 0.0 を自動で付ける。
  各問に「判断理由」を書いておくと、レビューで何を根拠に選んだかが分かる。
  迷ったら「最悪ならこうなるかも」ではなく**検査で確認できた事実**で選ぶ。
  代表例（反射型 XSS・IDOR・CSRF 等）から始めて選び直すこともできる。
- **状態**: 下書き（要レビュー）→ 確定（報告対象）/ 取り下げ（誤検知）/ 解消（再テストで直った）。
  タスクの自動チェックは「下書きが残っていない」「CVSS 未評価が無い」を見る。
- 所見の詳細ページから、各エビデンスの**実施記録の該当手順**（深いリンク）とファイル自体に飛べる。
- WSTG 詳細ページは、確定所見があるのにどのアクティビティでも `fail` になっていなければ警告する。
- 同時編集: 保存時に読み込んだ版と違えば拒否する（他の人の更新を上書きしない）。
- CLI でも扱える:
  ```bash
  uv run scripts/findings.py list
  uv run scripts/findings.py new --title "…" --wstg WSTG-ATHZ-01 --evidence <フォルダ>/cmd/x.txt
  uv run scripts/cvss31.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N"   # 6.1 Medium
  ```
- 旧形式（各アクティビティの `findings.md`）が残っていれば `uv run scripts/findings.py migrate` で
  所見ファイル（下書き）に移す（元は `findings.md.migrated` に改名して残す）。

### 3. 進捗を確認する

```bash
uv run scripts/tasks.py
#   [x]  1. recon-osint          完了   2/2 判定済み
#   [~]  2. fingerprint-stack    実施中  2/4 判定済み
#   [ ]  3. tls-scan             未着手  前提未完: fingerprint-stack
#   次にやること: 2. fingerprint-stack — …
```

`evidence/*/run.yaml` の `verdict` を見て、アクティビティ単位の進捗と「次にやること」
（前提が終わっていて着手できるもの）を出す。

Web の「タスク」ページでも同じ進捗が見られる。各アクティビティの✓は実施状況から自動で付く
（フォルダ・コマンド出力・手動観察・判定・所見）。「合意した」「リーダー確認済み」などは人が押し、
誰がいつ押したかが `evidence/_state/checks.yaml` に残る。

### 4. 一覧（CSV）を取り出す

日常の確認は Web の **WSTG 索引**（カテゴリ別の完了数・未実施/FAIL/所見ありの絞り込み）で行う。
報告書に添付する等で一覧を外に出すときだけ CSV にする:

```bash
uv run scripts/export_checklist.py --summary
# -> checklist_export.csv（全 97 項目。未実施は todo のまま）
```

Web の「CSV」（`/export.csv`）からも同じものをダウンロードできる。集約ステータスは
`fail > todo > info > pass > na` の優先度。`finding_summary` には判定理由に続けて、
その WSTG に紐づく所見が `[F-003 High 8.1] タイトル` の形で入る（取り下げは除く）。
**外に出す前に目視レビュー**（生値・資格情報が混じっていないか）。

## チームで共有する（nginx）

共用の Kali 1台にリポジトリと `evidence/` を置き、コマンドは各自がそこへ SSH して実行する。
Web は同じ機械で動かし、nginx から公開する（`serve_record.py` 自体は 127.0.0.1 でしか待ち受けない）。

```bash
uv run scripts/serve_record.py --behind-proxy     # 常駐は templates/nginx/wstg-web.service
sudo apt install -y nginx apache2-utils
sudo htpasswd -c /etc/nginx/wstg.htpasswd alice    # 2人目以降は -c なし
sudo cp templates/nginx/wstg.conf /etc/nginx/sites-available/wstg   # 証明書・許可ネットワークを直す
sudo ln -s /etc/nginx/sites-available/wstg /etc/nginx/sites-enabled/wstg
sudo nginx -t && sudo systemctl reload nginx
```

- `--behind-proxy` では、nginx の認証ユーザ（`X-Remote-User`）が所見・チェックの編集者名になる。
  サーバ機の画面を撮る『📷 スクショを撮る』は無効になり、各自の PC で撮って**貼り付け**る。
- 書き込み API は独自ヘッダと Origin を検査する（他サイトからの書き込みを弾く）。書き込みは直列化される。
- **evidence がそのまま見えるので、社内ネットワーク限定・TLS・認証を外さない**（設定例はその前提）。

## リポジトリ構成

| パス | 中身 | 追跡 |
|------|------|------|
| `scripts/` | 取得・生成・実行ログ・集約のスクリプト | ✅ |
| `matrix/coverage.yaml` | アクティビティ定義（**手編集**）＋自動生成の双方向インデックス | ✅ |
| `matrix/coverage.md` | 同・人間可読（自動生成） | ✅ |
| `matrix/criteria.yaml` | pass/fail の判定基準（**手編集**・育てる） | ✅ |
| `matrix/wstg_tests.yaml` | WSTG v4.2 のテスト一覧（自動生成） | ✅ |
| `playbooks/` | 1テスト=1枚のカード（自動生成） | ✅ |
| `TASKS.md` | 実施順のタスクリスト（自動生成） | ✅ |
| `templates/run.yaml` | run.yaml のスキーマ兼雛形 | ✅ |
| `templates/artifacts/` | `.md` 成果物の検索用フォーマット雛形（**手編集**） | ✅ |
| `templates/nginx/` | チーム共有用の nginx 設定・systemd ユニットの例 | ✅ |
| `pyproject.toml` / `uv.lock` / `.python-version` | uv による環境定義 | ✅ |
| `docs/owasp/` | WSTG 原文（`FETCH.md` 以外は追跡しない） | ❌ |
| `evidence/` | 生エビデンス（共用 Kali のみ）。`_findings/` に所見、`_state/` に手動チェック | ❌ |
| `checklist_export.csv` | 集約 CSV（レビュー用の一時物） | ❌ |

## 生成物を作り直すとき

```bash
uv run scripts/build_wstg_index.py    # 原文 -> matrix/wstg_tests.yaml
uv run scripts/build_coverage.py      # coverage.yaml の activities -> 索引 + coverage.md
uv run scripts/gen_playbooks.py       # 原文 + criteria.yaml -> playbooks/
uv run scripts/tasks.py --write       # coverage.yaml の phase/order -> TASKS.md
```

`--check` を付けると（`gen_playbooks.py` 以外）書き換えずに差分の有無だけ確認できる。
まとめて確認するなら `./scripts/selftest.sh`。

### アクティビティを増やす

1. `matrix/coverage.yaml` の `activities:` に追記（`covers:` の `role` は
   `primary`＝単独で判定できる / `secondary`＝入力・補強）。
2. `python scripts/build_coverage.py` で索引と `coverage.md` を再生成。
3. `python scripts/gen_playbooks.py` でカード側の「カバーするアクティビティ」も更新。

### 判定基準を育てる

現場で「ここが分かれ目だった」と思ったら `matrix/criteria.yaml` の該当 ID に
`pass` / `fail` / `note` を書き足し、`gen_playbooks.py` を再実行する。
カードがそのまま新人への説明台本になる。

## 機密境界

- `evidence/**` は共用 Kali（または社内PC）のローカルのみ。コミットしない。AI にも渡さない。
- 共有は nginx 経由の社内ネットワーク限定・TLS・認証あり（`templates/nginx/wstg.conf`）。
  `serve_record.py` を 127.0.0.1 以外で待ち受けさせない（起動時に拒否する）。
- 会社PC では repo を pull → スクリプト実行 → 生成物とカードを参照、で回す。
- 実データの分析はローカル手作業または社内 Gemini。カードは「データと一緒に貼る
  前提の説明文」として使える粒度で作ってある。
- 詳細は `CLAUDE.md`（AI 向けの恒久ルール）を参照。
