# WSTG 実施支援システム

OWASP Web Security Testing Guide (WSTG) **v4.2** を、**収集アクティビティ単位**で
回すための方法論とツール一式。

- WSTG 項目を1件ずつ潰すのではなく、1回の収集（例: 「認証済みクロール」）で
  該当する複数の WSTG-ID にまとめてチェックを入れる。
- チェックリスト（`checklist_export.csv`）は **概要のみ**。詳細は各エビデンス
  フォルダを見れば分かる、という前提で運用する。
- 実エビデンスはこのリポジトリに入れない（`evidence/` は `.gitignore` 済み）。

**まず `TASKS.md` を開く。** 実施順に並んだチェックリストがそこにある。
今どこまで進んだかは `uv run scripts/tasks.py`。

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
   ├ cmd/ + artifacts/（run_activity.py が手順を実行＝純粋なエビデンス）─┐
   ├ record.html ─(iframe参照)▶ cmd/・artifacts/ の各ファイル（evidence.js はメタデータのみ）
   └ run.yaml（covers に判定を直接記入）─┬─▶ export_checklist.py ─▶ checklist_export.csv ─ 目視 ─▶ Sheets
                                         └─▶ tasks.py（進捗表示）
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
- **検査対象が社内 IP のときは `no_proxy` に入れる**（入れないとプロキシに飛んで失敗する）
- **プロキシが要るのは外部の公開ソースへ出るときだけ**（crt.sh / hackertarget / subfinder の
  API、retire.js の脆弱性DB更新など）。`nmap` / `nikto` / `ffuf` / `testssl.sh` / `sqlmap` の
  ようなアクティブスキャンは**検査対象ホストに直接**つなぐので、対象が社内 IP なら
  `no_proxy` に入れてプロキシを経由させない（TLS/生ソケットは HTTP プロキシを通らない）

ツールが 0 件を返したときは、まず疎通を疑う。「何も無い」と「収集に失敗した」は別で、
後者を `pass` にしてはいけない（`playbooks/WSTG-INFO-01.md` の疎通確認の手順を参照）。

## 日々の流れ

`TASKS.md` を上から消化していく。1本のアクティビティで踏むのは 1〜2、
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

### 2. コマンド手順を wrapper で実行する（＝純粋なエビデンスを作る）

手順のコマンドは自分で打たず、wrapper に実行させる。手順は `matrix/criteria.yaml` から
毎回組み立て、target は `run.yaml` の対象に、出力先はこのフォルダの `artifacts/` に置換される。

```bash
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913            # コマンド手順を全部実行
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --list     # 手順一覧（実行しない）
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --only WSTG-INFO-02      # ID を絞る
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --only WSTG-INFO-02:4    # 手順を絞る
uv run scripts/run_activity.py evidence/recon-osint-example.com-20260913 --dry-run  # 実行内容の確認だけ
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

### 2b. 判定を `run.yaml` に書き、`record.html` で見る

判定は `run.yaml` の `covers:` に**直接**書く（唯一の判定置き場。旧 `record.md` / `capture.py` は廃止）:

```yaml
covers:
  - id: WSTG-INFO-02
    verdict: fail          # pass | fail | info | na | todo
    finding: "2.4.49 に既知 CVE。詳細は evidence 参照"   # 要約のみ
    evidence: "cmd/WSTG-INFO-02-s5.txt"                 # 生値はこのファイルを見る
```

書いたら表示を最新化して、ブラウザで `record.html` を開いて確認する:

```bash
uv run scripts/gen_record.py evidence/recon-osint-example.com-20260913
```

`record.html` は WSTG-ID ごとの**タブ**で表示する（長い縦スクロールを畳む。選択タブはブラウザに記憶）。
静的なビューアで、手順の説明・各コマンド・WSTG-ID ごとの判定/finding という
**メタデータ**を同フォルダの `evidence.js` から読む（`file://` では `.txt` の `fetch` が遮断されるため
`<script src>` で渡す）。**エビデンス本体（各コマンドの出力）は evidence.js に複製せず、
`cmd/`・`artifacts/` のファイルを `<iframe>` で直接参照する**。したがって `.txt` を手で編集
（別環境で取った結果を貼る等）したら、`gen_record.py` を回さなくてもブラウザのリロードだけで反映される。
`gen_record.py` が要るのは、手順の変更・判定の記入・新しいコマンドの追加を反映するときだけ。

- Firefox は `file://` の `<iframe>` で同フォルダのファイルを表示できる（Kali 既定）。
  Chromium 系で枠が空になる場合や、**手順ごとの『スクショを撮る』ボタンを使いたい場合**は、
  ローカルサーバ経由で開く:
  ```bash
  uv run scripts/serve_record.py evidence/recon-osint-example.com-20260913 --open
  # -> http://127.0.0.1:8765/record.html（127.0.0.1 のみ待受）
  ```
  http 配信になるので Chrome でも iframe/img が確実に表示され、各手順の
  『📷 この手順のスクショを撮る』が有効になる（サーバが save_shot --grab を実行→その手順の直下に画像）。
  待ち時間（秒）を上部の入力で指定し、その間に対象ウィンドウを前面へ出して範囲選択する。

**エビデンス本体は `cmd/`・`artifacts/` の各ファイルに、判定は `run.yaml` にあるので、
上流（`criteria.yaml` 等）を更新して手順が変わっても、`gen_record.py` で作り直すだけでよく、
過去のエビデンスを別ファイルからコピーし直す必要がない。**

- **`finding` は要約のみ**。生トークン・資格情報・生ホスト名は書かず、`evidence:` のパス参照で示す。

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

### 4. チェックリストを出力する

```bash
uv run scripts/export_checklist.py --summary
# -> checklist_export.csv（全 97 項目。未実施は todo のまま）
```

集約ステータスは `fail > todo > info > pass > na` の優先度。同じ WSTG-ID を複数の
アクティビティが触っていれば、最も注意すべきものが採用される。

出力後は **目視レビュー** し、Google Sheets で
「ファイル → インポート → アップロード → 現在のシートを置換」で取り込む。

（任意）`--push --sheet-id <ID>` でシートへ直接反映もできる。既定は CSV 出力のみ。
機密が混じっていないか自分で確認してから使うこと。

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
| `pyproject.toml` / `uv.lock` / `.python-version` | uv による環境定義 | ✅ |
| `docs/owasp/` | WSTG 原文（`FETCH.md` 以外は追跡しない） | ❌ |
| `evidence/` | 生エビデンス（社内PCのローカルのみ） | ❌ |
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

- `evidence/**` は社内PCのローカルのみ。コミットしない。AI にも渡さない。
- 会社PC では repo を pull → スクリプト実行 → 生成物とカードを参照、で回す。
- 実データの分析はローカル手作業または社内 Gemini。カードは「データと一緒に貼る
  前提の説明文」として使える粒度で作ってある。
- 詳細は `CLAUDE.md`（AI 向けの恒久ルール）を参照。
