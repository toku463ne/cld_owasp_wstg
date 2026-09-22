# WSTG-INFO-01 — Conduct Search Engine Discovery Reconnaissance for Information Leakage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

検索エンジンや公開アーカイブに、対象組織が意図せず晒した情報が残っていないかを確認する。

WSTG の Test Objectives:

- Identify what sensitive design and configuration information of the application, system, or organization is exposed directly (on the organization's website) or indirectly (via third-party services).

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `whois target.co.jp` で組織名・登録者・ネームサーバを確認し、名寄せの起点にする
2. `theHarvester -d target.co.jp -b duckduckgo,crtsh,otx,hackertarget -p -f theharvester.xml && mv theharvester.xml theharvester.json evidence/<活動フォルダ>/artifacts/` で露出メール・サブドメイン・ホストを収集（`-p` は /etc/theHarvester/proxies.yaml のプロキシを使う指定。プロキシ不要の環境では外す。4.11 は -f のパスを無視してカレントに .xml/.json を書くので mv で artifacts/ へ移す。`-b all` で全ソース）
3. theHarvester が 0 件だったら、各ソースの疎通を単体で確認して「本当に何も無い」のか「収集に失敗した」のかを切り分ける: `curl -s 'https://crt.sh/?q=%25.target.co.jp&output=json' -o evidence/<活動フォルダ>/artifacts/crtsh.json` と `curl -s 'https://api.hackertarget.com/hostsearch/?q=target.co.jp' -o evidence/<活動フォルダ>/artifacts/hackertarget-hosts.txt`。JSON やホスト一覧が返るならソースは生きている＝theHarvester 側の問題なので、この2ファイルを収集結果として採用する（OTX は `https://otx.alienvault.com/api/v1/indicators/domain/target.co.jp/passive_dns` だが匿名アクセス不可で API キーが要る）
4. crt.sh（`https://crt.sh/?q=%25.target.co.jp`）と `subfinder -d target.co.jp -all -proxy "$https_proxy" -o evidence/<活動フォルダ>/artifacts/subfinder.txt` で公開・失念サブドメインを列挙（`-all` は無料ソースを総当り。subfinder は環境変数のプロキシを見ないので `-proxy` を明示する。プロキシ不要の環境では `-proxy` を外す）
5. dork① 業務/設定ファイルの露出: `site:target.co.jp ext:xls OR ext:pdf OR ext:conf` をブラウザで検索（.doc/.docx/.xlsx/.csv/.bak/.sql 等も同様に）。Google と Bing の両方で検索し、結果（件数 or `該当なし`）とスクショを記録する（`did not match any documents` = このdorkでは露出なし＝問題なし）。ヒットがあれば URL・スニペットを artifacts/dorking-hits.md に記録し [creds]/[internal] 等のタグを付ける
6. dork② ディレクトリ一覧（オープンディレクトリ）の露出: `intitle:index.of site:target.co.jp` を検索。Google と Bing の両方で検索し、結果（件数 or `該当なし`）とスクショを記録する（`did not match any documents` = このdorkでは露出なし＝問題なし）。ヒットがあれば URL・スニペットを artifacts/dorking-hits.md に記録し [creds]/[internal] 等のタグを付ける
7. dork③ 管理画面・管理系パスの露出: `inurl:admin site:target.co.jp` を検索（`login`/`phpmyadmin`/`wp-admin` 等でも同様に）。Google と Bing の両方で検索し、結果（件数 or `該当なし`）とスクショを記録する（`did not match any documents` = このdorkでは露出なし＝問題なし）。ヒットがあれば URL・スニペットを artifacts/dorking-hits.md に記録し [creds]/[internal] 等のタグを付ける
8. dork④ エラー/スタックトレースの露出: `site:target.co.jp "error" OR "exception" OR "stack trace"` を検索。Google と Bing の両方で検索し、結果（件数 or `該当なし`）とスクショを記録する（`did not match any documents` = このdorkでは露出なし＝問題なし）。ヒットがあれば URL・スニペットを artifacts/dorking-hits.md に記録し [creds]/[internal] 等のタグを付ける
9. dork①〜④の総合判定と過去分の確認: 4本すべて `該当なし` なら dork 観点は pass、1本でも機微なヒットがあれば fail 側の材料。加えて Wayback Machine（web.archive.org）で、今は消えている旧版に①〜④の露出が残っていないか確認する（過去に出ていたものは削除依頼の対象）

## 使用ツール

- whois
- theHarvester
- curl
- crt.sh
- subfinder
- Google/Bing dorking
- ブラウザ
- Wayback Machine

## 判定基準（pass / fail の見分け）

- **pass**: 検索結果に機微情報（資格情報・内部URL・設定ファイル・個人情報）が出てこない。
- **fail**: dork でヒットした結果に、内部ホスト名・エラーメッセージ・認証情報・非公開ドキュメントが含まれる。
- 補足: キャッシュにしか残っていない場合も指摘対象。削除依頼（Search Console 等）まで助言する。theHarvester は -f を付けないと画面と ~/.local/share/theHarvester/stash.sqlite にしか残らない。4.11 は -f のパスを os.path.basename で切ってカレントに書く（サブフォルダ指定は無視）ため、上の手順は生成後に mv で artifacts/ へ移す。crt.sh は API 不調で "Expected object or value" が出ることがある（その時はブラウザで https://crt.sh/?q=%25.target.co.jp を確認）。「何も出ない」ことと「スキャンに失敗した」ことは別。ソースごとの成否（例: crtsh の例外）を見て、成功した上で無ければ pass、失敗しているなら再実行する。theHarvester は環境変数（http_proxy/https_proxy）のプロキシを見ない（内部の aiohttp が trust_env を有効にしていない）。プロキシ配下で `-p` を忘れると全ソースが直接通信に失敗し、crtsh は空レスポンスをパースして "Expected object or value"、他は黙って0件になる。実測（同一対象・同一ソース）では、`-p` なしは0件で XML 149 バイト、`-p` ありはホストが取れて XML 1249 バイトだった。0件を見たらまず `-p` と proxies.yaml（`http: - <host>:<port>`）を疑う。同じ理由で theHarvester が0件でも crt.sh / hackertarget は curl だと普通に返ることがある（上の疎通確認の手順）。その場合は curl の結果を収集結果として採用し、theHarvester の空 XML/JSON を「情報なし」の根拠にしない。hackertarget は無料枠の日次上限に当たると本文が API count exceeded になる。OTX は匿名アクセス不可なので、使うなら /etc/theHarvester/api-keys.yaml に API キーを入れる。サブドメイン列挙は amass から subfinder に差し替えてある。amass v5 は engine 常駐型で、起動時に bgp.tools を自前のリゾルバ（公開 DNS）で解決するため、外向き UDP/53 が塞がれた環境（プロキシ必須の社内網など）では "failed to obtain the BGPTools IP address" で engine が起動せず、enum は 60 秒でタイムアウトする（v5.1.1 の config.yaml にリゾルバ指定は無く、amass engine -h にも -r は無い）。subfinder はこの UDP/53 制約は受けない（HTTPS の API 主体）が、theHarvester と同様に環境変数（http_proxy/https_proxy）を見ないため、プロキシ配下では `-proxy "$https_proxy"` を明示しないと全ソースが timeout して0件になる。実測（同一対象）では、`-proxy` なしは0件で約90秒（全ソース timeout）、`-proxy` ありは28件で約32秒だった。それでも取れないときは手順3の crt.sh / hackertarget を採用してよい。record.md にはエラーをそのまま貼り、「<ツール名> はエラーのため未使用」と理由を残す（ツールが動かないことは所見ではない）。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/subdomains.txt`, `artifacts/dorking-hits.md`, `cmd/whois.txt`
- `covers:` — `{id: WSTG-INFO-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `recon-osint` — 外部 OSINT・公開情報の収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/01-Conduct_Search_Engine_Discovery_Reconnaissance_for_Information_Leakage
