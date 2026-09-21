# 実施タスクリスト（上から順に消化する）

> 自動生成: `uv run scripts/tasks.py --write`
> 順序・依存の元データは `matrix/coverage.yaml`。ここを直接編集しない。

アクティビティ 31 本で、WSTG v4.2 の実施対象 94 項目をカバーする。
進捗は `uv run scripts/tasks.py` で確認できる。

## フェーズ0 — 準備（1回だけ）

- [ ] 対象・時間帯・禁止事項・連絡先を合意する（`impact: high` の項目は特に）
- [ ] ロールごとのテストアカウントを入手する
- [ ] `uv sync` — Python 環境を用意（uv が無い会社PCでは `pip install pyyaml`）
- [ ] `./scripts/selftest.sh` — ツールが動くことを確認
- [ ] （原文を読みたいとき）`./scripts/fetch_wstg.sh`
- [ ] プロキシ配下なら外向き疎通を確認: `env | grep -i proxy` と `curl -sI https://crt.sh | head -1`
      - 通らないなら README「プロキシ配下での準備」を先に済ませる（`sudo` は `-E` か `env_keep`、DNS はプロキシを通らない）
- 実施できるアクティビティ ID の一覧: `uv run scripts/new_activity.py`（引数なし）
- 複数サイトを回すときは各アクティビティで `--target <site>` を付ける

Kali のツール準備は各フェーズ冒頭の「準備」に未導入分の `apt` をまとめてある。
まず `sudo apt update`。`pipx` / `npm` / `go` を使う個別導入もフェーズ内に記載。

## フェーズ1 — 受動的収集

対象に触れずに分かることを集め、以降のスコープと入力を確定させる。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- apt: `sudo apt install -y bind9-dnsutils curl subfinder theharvester whois`

### 1. `recon-osint` — 外部 OSINT・公開情報の収集

検索エンジン・証明書透明性ログ・whois から、対象の公開露出面とサブドメインを洗い出す。

- 影響度: 低 / 前提: なし
- カード: [WSTG-INFO-01](playbooks/WSTG-INFO-01.md), [WSTG-CONF-10](playbooks/WSTG-CONF-10.md)

- [ ] `uv run scripts/new_activity.py recon-osint` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・theHarvester, crt.sh, whois, Google/Bing dorking, subfinder）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/recon-osint-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/recon-osint-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## フェーズ2 — 外形調査・構成

外から見えるサービス・設定・残骸を洗い出す。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- apt: `sudo apt install -y awscli bind9-dnsutils curl dirsearch ffuf gobuster httpx-toolkit ncat nikto nmap ripgrep sslyze testssl.sh wget whatweb`
- 個別: `sudo apt install -y npm && sudo npm install -g retire`
- Kali 同梱 / Burp 内（導入不要）: Burp Repeater, Burp Suite

### 2. `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

ポート/サービス/ヘッダ/既知の指紋から、OS・Web サーバ・ミドルウェア・アプリ基盤を特定する。

- 影響度: 低 / 前提: `recon-osint`
- カード: [WSTG-INFO-02](playbooks/WSTG-INFO-02.md), [WSTG-INFO-08](playbooks/WSTG-INFO-08.md), [WSTG-CONF-01](playbooks/WSTG-CONF-01.md), [WSTG-CONF-02](playbooks/WSTG-CONF-02.md)

- [ ] `uv run scripts/new_activity.py fingerprint-stack` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・nmap -sV, whatweb, Wappalyzer, httpx-toolkit）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/fingerprint-stack-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/fingerprint-stack-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 3. `tls-scan` — TLS 設定スキャン

対象の全 TLS ポートに対して暗号スイート・プロトコル・証明書・HSTS を一括検査する。

- 影響度: 低 / 前提: `fingerprint-stack`
- カード: [WSTG-CRYP-01](playbooks/WSTG-CRYP-01.md), [WSTG-CONF-07](playbooks/WSTG-CONF-07.md), [WSTG-CONF-01](playbooks/WSTG-CONF-01.md)

- [ ] `uv run scripts/new_activity.py tls-scan` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・testssl.sh, sslyze, nmap --script ssl-enum-ciphers）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/tls-scan-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/tls-scan-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 4. `http-methods` — HTTP メソッドの列挙と検証

OPTIONS 応答を鵜呑みにせず、実際に各メソッドを投げて許可状況と挙動差を確認する。

- 影響度: 中 / 前提: `fingerprint-stack`
- カード: [WSTG-CONF-06](playbooks/WSTG-CONF-06.md), [WSTG-INPV-03](playbooks/WSTG-INPV-03.md)

- [ ] `uv run scripts/new_activity.py http-methods` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・curl, nmap http-methods NSE, ncat, Burp Repeater）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/http-methods-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/http-methods-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 5. `metafiles-crawl` — メタファイル・公開コンテンツの収集

robots.txt・sitemap・.well-known・security.txt・HTML コメント・JS ソースを機械収集して読み込む。

- 影響度: 低 / 前提: なし
- カード: [WSTG-INFO-03](playbooks/WSTG-INFO-03.md), [WSTG-INFO-05](playbooks/WSTG-INFO-05.md), [WSTG-CONF-05](playbooks/WSTG-CONF-05.md)

- [ ] `uv run scripts/new_activity.py metafiles-crawl` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・curl, wget, grep/ripgrep, Burp Suite）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/metafiles-crawl-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/metafiles-crawl-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 6. `enum-apps` — 仮想ホスト・パスの列挙

DNS/vhost と URL パスをファジングし、同一ホスト上の別アプリ・別インスタンスを洗い出す。

- 影響度: 中 / 前提: `recon-osint`, `fingerprint-stack`
- カード: [WSTG-INFO-04](playbooks/WSTG-INFO-04.md), [WSTG-INFO-06](playbooks/WSTG-INFO-06.md)

- [ ] `uv run scripts/new_activity.py enum-apps` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・ffuf, dirsearch, gobuster, nmap -p-）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/enum-apps-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/enum-apps-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 7. `backup-unref` — 旧・バックアップ・未参照ファイルの探索

拡張子とファイル名のバリエーションを総当たりし、公開されている残骸ファイルを探す。

- 影響度: 中 / 前提: `enum-apps`
- カード: [WSTG-CONF-03](playbooks/WSTG-CONF-03.md), [WSTG-CONF-04](playbooks/WSTG-CONF-04.md)

- [ ] `uv run scripts/new_activity.py backup-unref` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・ffuf, dirsearch, nikto）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/backup-unref-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/backup-unref-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 8. `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認

公開バケット等のストレージ露出と、宙に浮いた DNS レコードによる乗っ取り可能性を確認する。

- 影響度: 中 / 前提: `recon-osint`
- カード: [WSTG-CONF-11](playbooks/WSTG-CONF-11.md), [WSTG-CONF-10](playbooks/WSTG-CONF-10.md)

- [ ] `uv run scripts/new_activity.py cloud-and-takeover` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・dig, curl, grep, aws cli）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/cloud-and-takeover-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/cloud-and-takeover-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 9. `ria-legacy-check` — RIA クロスドメインポリシーとレガシー Flash の確認

crossdomain.xml / clientaccesspolicy.xml と、残存する Flash/Silverlight コンテンツを確認する。

- 影響度: 低 / 前提: `metafiles-crawl`
- カード: [WSTG-CONF-08](playbooks/WSTG-CONF-08.md), [WSTG-CLNT-08](playbooks/WSTG-CLNT-08.md)

- [ ] `uv run scripts/new_activity.py ria-legacy-check` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・curl, 手動レビュー）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/ria-legacy-check-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/ria-legacy-check-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 10. `server-config-review` — サーバ／プラットフォーム構成レビュー

構成ファイル・配置・権限・不要機能を（可能なら読み取り権限を得て）レビューする。ホスト側の情報提供が前提。

- 影響度: 低 / 前提: `fingerprint-stack`
- カード: [WSTG-CONF-01](playbooks/WSTG-CONF-01.md), [WSTG-CONF-02](playbooks/WSTG-CONF-02.md), [WSTG-CONF-09](playbooks/WSTG-CONF-09.md)

- [ ] `uv run scripts/new_activity.py server-config-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・手動レビュー, ls -l / icacls, nikto, CIS Benchmark チェックリスト）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/server-config-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/server-config-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## フェーズ3 — アプリ把握

認証済みでアプリ全体を歩き、入力点と構造を地図にする。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- apt: `sudo apt install -y curl ffuf`
- Kali 同梱 / Burp 内（導入不要）: Burp Suite, OWASP ZAP

### 11. `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し

認証済みセッションでアプリ全体をクロールし、エントリポイント・実行パス・アーキテクチャを把握する。

- 影響度: 中 / 前提: `enum-apps`
- カード: [WSTG-INFO-06](playbooks/WSTG-INFO-06.md), [WSTG-INFO-07](playbooks/WSTG-INFO-07.md), [WSTG-INFO-10](playbooks/WSTG-INFO-10.md), [WSTG-CONF-05](playbooks/WSTG-CONF-05.md)

- [ ] `uv run scripts/new_activity.py burp-crawl-authn` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・Burp Suite, OWASP ZAP）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/burp-crawl-authn-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/burp-crawl-authn-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 12. `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

代表エンドポイントについて匿名・認証済みの応答を1セット取得し、セキュリティ関連ヘッダを横断レビューする。

- 影響度: 低 / 前提: `burp-crawl-authn`
- カード: [WSTG-SESS-02](playbooks/WSTG-SESS-02.md), [WSTG-CONF-07](playbooks/WSTG-CONF-07.md), [WSTG-CLNT-09](playbooks/WSTG-CLNT-09.md), [WSTG-ATHN-06](playbooks/WSTG-ATHN-06.md), [WSTG-CLNT-07](playbooks/WSTG-CLNT-07.md), [WSTG-CRYP-03](playbooks/WSTG-CRYP-03.md)

- [ ] `uv run scripts/new_activity.py headers-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（6 項目・curl, Burp Suite, securityheaders.io 相当の手動チェック）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/headers-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/headers-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 13. `error-handling-review` — エラーハンドリングのレビュー

異常系を意図的に起こし、返る情報量（スタックトレース・SQL エラー・内部パス）を確認する。

- 影響度: 低 / 前提: `burp-crawl-authn`
- カード: [WSTG-ERRH-01](playbooks/WSTG-ERRH-01.md), [WSTG-ERRH-02](playbooks/WSTG-ERRH-02.md), [WSTG-INFO-05](playbooks/WSTG-INFO-05.md)

- [ ] `uv run scripts/new_activity.py error-handling-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・Burp Suite, curl, 手動）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/error-handling-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/error-handling-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 14. `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー

ドキュメントとヒアリング＋実機で、ロール定義・アカウント登録・払い出し・ユーザ名ポリシーを確認する。

- 影響度: 低 / 前提: なし
- カード: [WSTG-IDNT-01](playbooks/WSTG-IDNT-01.md), [WSTG-IDNT-02](playbooks/WSTG-IDNT-02.md), [WSTG-IDNT-03](playbooks/WSTG-IDNT-03.md), [WSTG-IDNT-05](playbooks/WSTG-IDNT-05.md)

- [ ] `uv run scripts/new_activity.py identity-model-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・手動レビュー, ヒアリング, Burp Suite）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/identity-model-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/identity-model-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## フェーズ4 — 認証・セッション

認証まわりとセッションの生成・維持・破棄を検証する。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- apt: `sudo apt install -y curl ffuf`
- Kali 同梱 / Burp 内（導入不要）: Burp Intruder, Burp Sequencer, Burp Suite

### 15. `authn-flow-review` — 認証フロー一括レビュー

認証の入口をひと通り触り、経路暗号化・既定資格情報・スキーマ迂回・記憶機能・パスワードポリシー・代替チャネルをまとめて確認する。

- 影響度: 中 / 前提: `burp-crawl-authn`, `identity-model-review`
- カード: [WSTG-ATHN-01](playbooks/WSTG-ATHN-01.md), [WSTG-ATHN-02](playbooks/WSTG-ATHN-02.md), [WSTG-ATHN-04](playbooks/WSTG-ATHN-04.md), [WSTG-ATHN-05](playbooks/WSTG-ATHN-05.md), [WSTG-ATHN-06](playbooks/WSTG-ATHN-06.md), [WSTG-ATHN-07](playbooks/WSTG-ATHN-07.md), [WSTG-ATHN-10](playbooks/WSTG-ATHN-10.md), [WSTG-CRYP-03](playbooks/WSTG-CRYP-03.md)

- [ ] `uv run scripts/new_activity.py authn-flow-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（8 項目・Burp Suite, curl, ブラウザ開発者ツール）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/authn-flow-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/authn-flow-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 16. `account-enum-probe` — アカウント列挙とロックアウトの検証

ログイン・登録・パスワードリセットの応答差（本文・ステータス・応答時間）を比較し、ロックアウト挙動も測る。

- 影響度: 高（要事前合意） / 前提: `authn-flow-review`
- カード: [WSTG-IDNT-04](playbooks/WSTG-IDNT-04.md), [WSTG-ATHN-03](playbooks/WSTG-ATHN-03.md), [WSTG-IDNT-05](playbooks/WSTG-IDNT-05.md)

- [ ] `uv run scripts/new_activity.py account-enum-probe` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・Burp Intruder, ffuf, curl）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/account-enum-probe-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/account-enum-probe-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 17. `password-reset-review` — パスワード変更・リセット機能のレビュー

リセットトークンの強度・有効期限・所有確認、秘密の質問の強度を通しで確認する。

- 影響度: 中 / 前提: `authn-flow-review`
- カード: [WSTG-ATHN-08](playbooks/WSTG-ATHN-08.md), [WSTG-ATHN-09](playbooks/WSTG-ATHN-09.md)

- [ ] `uv run scripts/new_activity.py password-reset-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・Burp Suite, メールクライアント, 手動レビュー）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/password-reset-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/password-reset-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 18. `session-capture` — セッション取得とログイン/ログアウト解析

ログイン〜操作〜ログアウトを1本のトレースとして取得し、トークンの生成・維持・破棄を追う。

- 影響度: 低 / 前提: `authn-flow-review`
- カード: [WSTG-SESS-01](playbooks/WSTG-SESS-01.md), [WSTG-SESS-02](playbooks/WSTG-SESS-02.md), [WSTG-SESS-03](playbooks/WSTG-SESS-03.md), [WSTG-SESS-06](playbooks/WSTG-SESS-06.md), [WSTG-SESS-07](playbooks/WSTG-SESS-07.md), [WSTG-SESS-09](playbooks/WSTG-SESS-09.md)

- [ ] `uv run scripts/new_activity.py session-capture` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（6 項目・Burp Suite, Burp Sequencer, curl）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/session-capture-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/session-capture-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 19. `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）

取得済みセッションを使って、トークンの露出経路・CSRF 防御・状態の取り違え・再利用可否を検証する。

- 影響度: 中 / 前提: `session-capture`
- カード: [WSTG-SESS-04](playbooks/WSTG-SESS-04.md), [WSTG-SESS-05](playbooks/WSTG-SESS-05.md), [WSTG-SESS-08](playbooks/WSTG-SESS-08.md), [WSTG-SESS-09](playbooks/WSTG-SESS-09.md)

- [ ] `uv run scripts/new_activity.py session-abuse-tests` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・Burp Suite, curl, ブラウザ2枚）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/session-abuse-tests-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/session-abuse-tests-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## フェーズ5 — 認可

ロール横断・識別子差し替えで権限制御を検証する。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- apt: `sudo apt install -y curl ffuf`
- Kali 同梱 / Burp 内（導入不要）: Autorize / AuthMatrix, Burp Suite

### 20. `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

各ロールで採取した代表リクエストを、他ロール・未認証で再送して差分を見る。IDOR は識別子を差し替えて確認。

- 影響度: 中 / 前提: `session-capture`, `identity-model-review`
- カード: [WSTG-ATHZ-02](playbooks/WSTG-ATHZ-02.md), [WSTG-ATHZ-03](playbooks/WSTG-ATHZ-03.md), [WSTG-ATHZ-04](playbooks/WSTG-ATHZ-04.md), [WSTG-SESS-08](playbooks/WSTG-SESS-08.md)

- [ ] `uv run scripts/new_activity.py authz-matrix` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・Burp Suite, Autorize / AuthMatrix, curl）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/authz-matrix-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/authz-matrix-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 21. `traversal-probe` — ディレクトリトラバーサル・ファイルインクルードの検証

パス・ファイル名を扱うパラメータを洗い出し、トラバーサルと LFI/RFI を確認する。

- 影響度: 中 / 前提: `burp-crawl-authn`
- カード: [WSTG-ATHZ-01](playbooks/WSTG-ATHZ-01.md), [WSTG-CONF-03](playbooks/WSTG-CONF-03.md)

- [ ] `uv run scripts/new_activity.py traversal-probe` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・Burp Suite, ffuf, 手動 payload）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/traversal-probe-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/traversal-probe-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## フェーズ6 — 入力検証・クライアントサイド

洗い出した入力点に対して注入系・クライアント側の検証を行う。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- apt: `sudo apt install -y curl padbuster sqlmap testssl.sh`
- 個別: `sudo apt install -y npm && sudo npm install -g retire`
- 個別: `sudo apt install -y npm && sudo npm install -g wscat`
- 個別: `sudo apt install -y golang-go && go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest && export PATH="$PATH:$(go env GOPATH)/bin"`
- Kali 同梱 / Burp 内（導入不要）: Burp Collaborator, Burp HTTP Request Smuggler, Burp Intruder, Burp Suite, DOM Invader, InQL

### 22. `xss-probe` — XSS・HTML インジェクションの検証

反射・保存・DOM の各経路について、代表入力点にペイロードを流して出力エンコーディングを確認する。

- 影響度: 中 / 前提: `burp-crawl-authn`
- カード: [WSTG-INPV-01](playbooks/WSTG-INPV-01.md), [WSTG-INPV-02](playbooks/WSTG-INPV-02.md), [WSTG-CLNT-01](playbooks/WSTG-CLNT-01.md), [WSTG-CLNT-03](playbooks/WSTG-CLNT-03.md)

- [ ] `uv run scripts/new_activity.py xss-probe` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・Burp Suite, DOM Invader, 手動 payload）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/xss-probe-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/xss-probe-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 23. `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

JS のソース/シンクを追い、URL リダイレクト・CSS/リソース操作・postMessage・ブラウザストレージ・XSSI をまとめて確認する。

- 影響度: 低 / 前提: `burp-crawl-authn`
- カード: [WSTG-CLNT-02](playbooks/WSTG-CLNT-02.md), [WSTG-CLNT-04](playbooks/WSTG-CLNT-04.md), [WSTG-CLNT-05](playbooks/WSTG-CLNT-05.md), [WSTG-CLNT-06](playbooks/WSTG-CLNT-06.md), [WSTG-CLNT-11](playbooks/WSTG-CLNT-11.md), [WSTG-CLNT-12](playbooks/WSTG-CLNT-12.md), [WSTG-CLNT-13](playbooks/WSTG-CLNT-13.md)

- [ ] `uv run scripts/new_activity.py clientside-js-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（7 項目・ブラウザ開発者ツール, DOM Invader, Retire.js, Burp Suite）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/clientside-js-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/clientside-js-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 24. `cors-websocket-check` — CORS と WebSocket の検証

Origin を差し替えた応答差と、WebSocket ハンドシェイク・認可・暗号化を確認する。

- 影響度: 低 / 前提: `burp-crawl-authn`
- カード: [WSTG-CLNT-07](playbooks/WSTG-CLNT-07.md), [WSTG-CLNT-10](playbooks/WSTG-CLNT-10.md)

- [ ] `uv run scripts/new_activity.py cors-websocket-check` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・curl, Burp Suite, wscat）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/cors-websocket-check-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/cors-websocket-check-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 25. `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

収集済みエントリポイントに対し、SQL/LDAP/XML/SSI/XPath/IMAP-SMTP/コード/コマンド/書式文字列/SSTI を横断的に試す。

- 影響度: 高（要事前合意） / 前提: `burp-crawl-authn`
- カード: [WSTG-INPV-05](playbooks/WSTG-INPV-05.md), [WSTG-INPV-06](playbooks/WSTG-INPV-06.md), [WSTG-INPV-07](playbooks/WSTG-INPV-07.md), [WSTG-INPV-08](playbooks/WSTG-INPV-08.md), [WSTG-INPV-09](playbooks/WSTG-INPV-09.md), [WSTG-INPV-10](playbooks/WSTG-INPV-10.md), [WSTG-INPV-11](playbooks/WSTG-INPV-11.md), [WSTG-INPV-12](playbooks/WSTG-INPV-12.md), [WSTG-INPV-13](playbooks/WSTG-INPV-13.md), [WSTG-INPV-18](playbooks/WSTG-INPV-18.md), [WSTG-ERRH-01](playbooks/WSTG-ERRH-01.md)

- [ ] `uv run scripts/new_activity.py injection-fuzz-server` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（11 項目・Burp Intruder, sqlmap, 手動 payload）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/injection-fuzz-server-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/injection-fuzz-server-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 26. `http-request-tamper` — HTTP リクエスト改変系の検証

パラメータ汚染・ヘッダ分割/スマグリング・Host ヘッダ・受信リクエストの扱いをまとめて検証する。

- 影響度: 高（要事前合意） / 前提: `burp-crawl-authn`
- カード: [WSTG-INPV-04](playbooks/WSTG-INPV-04.md), [WSTG-INPV-15](playbooks/WSTG-INPV-15.md), [WSTG-INPV-16](playbooks/WSTG-INPV-16.md), [WSTG-INPV-17](playbooks/WSTG-INPV-17.md)

- [ ] `uv run scripts/new_activity.py http-request-tamper` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（4 項目・Burp Suite, Burp HTTP Request Smuggler, curl）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/http-request-tamper-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/http-request-tamper-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 27. `ssrf-probe` — SSRF の検証

URL・ホスト名・ファイル参照を受けるパラメータを列挙し、外向き/内向きの到達性を確認する。

- 影響度: 中 / 前提: `burp-crawl-authn`
- カード: [WSTG-INPV-19](playbooks/WSTG-INPV-19.md)

- [ ] `uv run scripts/new_activity.py ssrf-probe` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（1 項目・curl, interactsh-client, Burp Collaborator）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/ssrf-probe-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/ssrf-probe-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 28. `file-upload-tests` — ファイルアップロードの検証

想定外の拡張子・MIME・内容のファイルを投入し、保存先・実行可否・スキャンの有無を確認する。

- 影響度: 中 / 前提: `burp-crawl-authn`
- カード: [WSTG-BUSL-08](playbooks/WSTG-BUSL-08.md), [WSTG-BUSL-09](playbooks/WSTG-BUSL-09.md), [WSTG-CONF-03](playbooks/WSTG-CONF-03.md)

- [ ] `uv run scripts/new_activity.py file-upload-tests` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・Burp Suite, EICAR テストファイル, 手動）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/file-upload-tests-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/file-upload-tests-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 29. `crypto-review` — 暗号利用のレビュー（パディングオラクル・弱い暗号・平文送出）

暗号化された値の改変応答差、暗号アルゴリズム・鍵管理、平文チャネルでの機微情報送出を確認する。

- 影響度: 高（要事前合意） / 前提: `tls-scan`, `session-capture`
- カード: [WSTG-CRYP-02](playbooks/WSTG-CRYP-02.md), [WSTG-CRYP-03](playbooks/WSTG-CRYP-03.md), [WSTG-CRYP-04](playbooks/WSTG-CRYP-04.md)

- [ ] `uv run scripts/new_activity.py crypto-review` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（3 項目・padbuster, testssl.sh, Burp Suite, 手動レビュー）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/crypto-review-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/crypto-review-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

### 30. `api-graphql-test` — API / GraphQL の検証

スキーマ内省・バッチクエリ・深い入れ子・認可のかかり方を確認する。REST API も同じ枠で扱う。

- 影響度: 中 / 前提: `burp-crawl-authn`
- カード: [WSTG-APIT-01](playbooks/WSTG-APIT-01.md), [WSTG-ATHZ-02](playbooks/WSTG-ATHZ-02.md)

- [ ] `uv run scripts/new_activity.py api-graphql-test` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（2 項目・Burp Suite, GraphQL Voyager, InQL, curl）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/api-graphql-test-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/api-graphql-test-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## フェーズ7 — 業務ロジック

業務フローの逸脱と誤用を、実装ではなく業務の観点で検証する。

**準備（このフェーズで使う Kali ツール。未導入のものだけ）**
- Kali 同梱 / Burp 内（導入不要）: Burp Suite

### 31. `business-logic-walkthrough` — 業務ロジックの通し検証

業務フローを正常系→逸脱系で通し、データ妥当性・リクエスト偽造・整合性・時間・回数制限・順序・誤用防御を確認する。

- 影響度: 高（要事前合意） / 前提: `authz-matrix`
- カード: [WSTG-BUSL-01](playbooks/WSTG-BUSL-01.md), [WSTG-BUSL-02](playbooks/WSTG-BUSL-02.md), [WSTG-BUSL-03](playbooks/WSTG-BUSL-03.md), [WSTG-BUSL-04](playbooks/WSTG-BUSL-04.md), [WSTG-BUSL-05](playbooks/WSTG-BUSL-05.md), [WSTG-BUSL-06](playbooks/WSTG-BUSL-06.md), [WSTG-BUSL-07](playbooks/WSTG-BUSL-07.md), [WSTG-INPV-14](playbooks/WSTG-INPV-14.md)

- [ ] `uv run scripts/new_activity.py business-logic-walkthrough` で `record.md`（実施記録）を作る（複数サイトは `--target <site>`）
- [ ] `record.md` の各手順（8 項目・Burp Suite, 手動操作, 業務仕様書）を実施し、コマンド出力や画面の観察を「結果:」に貼る ← このファイルがエビデンス本体
      - `[コマンド]` は `$` 行を実行、`[手動/ブラウザ]` は指示どおり操作
      - 直接実行して `cmd/` にも残したいときは `uv run scripts/run_cmd.py evidence/business-logic-walkthrough-<yyyymmdd> -- <コマンド>`
- [ ] `record.md` に WSTG-ID ごとの `@verdict`（pass|fail|info|na|todo）と `@finding`（要約のみ）を記入
- [ ] `uv run scripts/capture.py evidence/business-logic-walkthrough-<yyyymmdd>` で判定を `run.yaml`（→CSV）に反映

## 仕上げ

- [ ] `uv run scripts/tasks.py` で todo の残りが無いことを確認
- [ ] `uv run scripts/export_checklist.py --summary` で CSV を出力
- [ ] CSV を目視レビュー（機密が混じっていないか）
- [ ] Google Sheets へ取り込み（ファイル → インポート → 現在のシートを置換）
- [ ] `fail` の項目について報告書とカードの判定基準を見直す
