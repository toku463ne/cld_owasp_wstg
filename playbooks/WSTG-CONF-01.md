# WSTG-CONF-01 — Test Network Infrastructure Configuration

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ネットワーク構成として、公開すべきでないサービス・ポート・管理経路が外部に出ていないかを確認する。

WSTG の Test Objectives:

- Review the applications' configurations set across the network and validate that they are not vulnerable.
- Validate that used frameworks and systems are secure and not susceptible to known vulnerabilities due to unmaintained software or default settings and credentials.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `nmap -sV -p- --open -oN evidence/<活動フォルダ>/artifacts/nmap-allports.txt target` で公開ポート/サービスを洗い出す
   > ⚠️ **負荷注意（手順1）**: `nmap -p-` は全ポート走査で重い。IDS/IPS や機器を刺激しうるので時間帯に注意（`--max-rate` で調整）。
2. 公開が危険なポート（SSH/RDP/DB/管理系）を手順1のスキャン結果から抽出する（再スキャンせず既存結果を grep するので追加負荷なし）: `grep -E '^(22|23|3389|3306|5432|1433|1521|6379|27017|9200|5601|8080|8443|9000|9090|9990|10000|7001|8161|15672|2375|5900)/(tcp|udp)' evidence/<活動フォルダ>/artifacts/nmap-allports.txt | tee evidence/<活動フォルダ>/artifacts/sensitive-ports.txt`。1行でも出たら、そのポートが本来アクセスできるべき範囲（社内のみ等）を超えて開いていないか手順4の FW/セキュリティグループ設定と突き合わせる。管理コンソールは製品ごとにポートが違うので、ヒットが無くても手順1の全開放ポート一覧に見慣れないサービスが無いか併せて目視する
3. `nikto -h https://target ${WSTG_PAUSE:+-Pause "$WSTG_PAUSE"} ${https_proxy:+-useproxy "$https_proxy"} -o evidence/<活動フォルダ>/artifacts/nikto.txt` と特定製品の既知脆弱性・既定資格情報を照合。nikto は既定でリクエスト間の待ちが無く、非力な対象は CPU 100%・504 になりやすい。`WSTG_PAUSE`（秒）を設定するとリクエスト間にその秒数だけ空ける（例: `export WSTG_PAUSE=2`。落ちるなら 3〜5 に上げる）。さらに絞るなら `-maxtime 30m` で打ち切り、`-T` で試験カテゴリを限定する。nikto は環境変数のプロキシを見ないので、プロキシ経由で対象に出る環境では `-useproxy` を明示する（`${...:+}` は各変数が設定されているときだけ付く）
   > ⚠️ **負荷注意（手順3）**: nikto は既知パスへ大量のリクエストを送る非常に騒がしいスキャン。既定はリクエスト間の待ちが無く、非力な対象は CPU 100%・504 になりやすい。`export WSTG_PAUSE=2`（落ちるなら 3〜5）でリクエスト間に待ちを入れる。さらに `-maxtime` で打ち切り、対象は1つずつ。
4. クラウドのセキュリティグループ/FW 設定（ヒアリング）と実スキャン結果を突き合わせ、差分を指摘

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: `nmap -p-` は全ポート走査で重い。IDS/IPS や機器を刺激しうるので時間帯に注意（`--max-rate` で調整）。
- **手順3**: nikto は既知パスへ大量のリクエストを送る非常に騒がしいスキャン。既定はリクエスト間の待ちが無く、非力な対象は CPU 100%・504 になりやすい。`export WSTG_PAUSE=2`（落ちるなら 3〜5）でリクエスト間に待ちを入れる。さらに `-maxtime` で打ち切り、対象は1つずつ。

## 使用ツール

- nmap
- nikto

## 判定基準（pass / fail の見分け）

- **pass**: 公開ポートが業務上必要なものだけで、管理系は接続元制限がかかっている。
- **fail**: SSH・RDP・DB・管理コンソール等が無制限に公開されている、またはサポート切れの製品が動いている。
- 補足: クラウドのセキュリティグループ設定と実際のスキャン結果を突き合わせる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/config-review.md`, `notes.md`, `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-CONF-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `server-config-review` — サーバ／プラットフォーム構成レビュー
- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント
- `tls-scan` — TLS 設定スキャン

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/01-Test_Network_Infrastructure_Configuration
