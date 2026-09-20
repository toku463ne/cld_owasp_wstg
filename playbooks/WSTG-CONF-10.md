# WSTG-CONF-10 — Test for Subdomain Takeover

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

宙に浮いた DNS レコードにより、第三者がサブドメインを乗っ取れないかを確認する。

WSTG の Test Objectives:

- Enumerate all possible domains (previous and current).
- Identify forgotten or misconfigured domains.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. サブドメインの各 CNAME をまとめて引く。手順4で作った evidence/<活動フォルダ>/artifacts/subfinder.txt を入力に `while read -r h; do echo "$h -> $(dig +short CNAME $h | head -1)"; done < evidence/<活動フォルダ>/artifacts/subfinder.txt | tee evidence/<活動フォルダ>/artifacts/cname-check.txt` を実行する（`->` の右が埋まっている行＝CNAME を持つサブドメインが乗っ取り確認の対象。空欄は A/AAAA 直指定なので対象外。crt.sh で拾った分も subfinder.txt に足してから回す）
2. cname-check.txt を乗っ取り可能サービスの CNAME フィンガープリントで絞り込む: `grep -iaE "s3[.-]|\.s3\.amazonaws|\.github\.io|heroku(dns|app)|\.azurewebsites\.net|\.cloudfront\.net|\.fastly\.net|pantheonsite|\.ghost\.io" evidence/<活動フォルダ>/artifacts/cname-check.txt | tee evidence/<活動フォルダ>/artifacts/takeover-candidates.md`。ヒットした行（`サブドメイン -> CNAME`）が要確認。出力が空なら該当なし＝この時点で pass 相当（対象サービス: S3 / GitHub Pages / Heroku / Azure / CloudFront / Fastly / Pantheon / Ghost 等。漏れが心配なら evidence/<活動フォルダ>/artifacts/cname-check.txt 全体も目視する）
3. 要確認リストの各サブドメインの応答をまとめて取得する: `while read -r line; do h=${line%% *}; echo "===== $h ====="; curl -s -m 10 https://$h/ | head -c 800; echo; done < evidence/<活動フォルダ>/artifacts/takeover-candidates.md | tee evidence/<活動フォルダ>/artifacts/takeover-responses.txt`。各応答に、サービス既定の「リソースが存在しない」エラーが出ているか見る。乗っ取り可能な典型応答: S3=`NoSuchBucket`、GitHub Pages=`There isn’t a GitHub Pages site here`、Heroku=`No such app`、Azure=`404 Web Site not found`、Fastly=`Fastly error: unknown domain`。このエラーが出る＝第三者が同名リソースを登録して掌握できる状態（fail）。正常なコンテンツが返る＝実在リソース（この観点は pass）
4. 乗っ取り可能と判断しても、実際の取得（バケット作成・リポジトリ/アプリ登録等）は行わない。CNAME・エラー応答本体・ステータスを証跡（artifacts/）に残し、finding には該当サブドメイン名と「どのサービスの未登録リソースを指すか」を要約で書く（生の CNAME 先ホスト名は evidence 参照に留める）

## 使用ツール

- subfinder
- dig
- crt.sh
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 全サブドメインの向き先が実在し、解放済みクラウドリソースを指す CNAME がない。
- **fail**: 解放済みのホスティング先を指す CNAME/A があり、第三者が同名リソースを取得して掌握できる。
- 補足: 実際の乗っ取りは行わない。到達性とエラー応答（NoSuchBucket 等）で判断し、証拠として記録する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/curl-bucket.txt`, `artifacts/dangling-dns.md`, `artifacts/subdomains.txt`, `artifacts/dorking-hits.md`, `cmd/whois.txt`
- `covers:` — `{id: WSTG-CONF-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認
- `recon-osint` — 外部 OSINT・公開情報の収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/10-Test_for_Subdomain_Takeover
