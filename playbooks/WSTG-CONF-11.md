# WSTG-CONF-11 — Test Cloud Storage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

クラウドストレージの公開設定が過剰でないかを確認する。

WSTG の Test Objectives:

- Assess that the access control configuration for the storage services is properly in place.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. アプリが参照するストレージ URL を、metafiles-crawl（WSTG-INFO-05 手順1/2）が取得済みの index.html・app-js.txt と、WSTG-INFO-08 手順4 の HAR（あれば）から抽出する（同じ全 JS クロールを繰り返さない）: `grep -rhoiE 'https?://[A-Za-z0-9._-]+\.(s3[A-Za-z0-9.-]*\.amazonaws\.com|s3\.amazonaws\.com|blob\.core\.windows\.net|storage\.googleapis\.com)[A-Za-z0-9._~:/?#@!$&*+,;=%-]*' "$(ls -1d evidence/<活動フォルダ>/artifacts/../../metafiles-crawl-target-*/artifacts | tail -1)"/index.html "$(ls -1d evidence/<活動フォルダ>/artifacts/../../metafiles-crawl-target-*/artifacts | tail -1)"/app-js.txt $(ls -1 evidence/<活動フォルダ>/artifacts/../../fingerprint-stack-target-*/artifacts/site.har 2>/dev/null | tail -1) > evidence/<活動フォルダ>/artifacts/storage-urls.txt; rc=$?; [ $rc -le 1 ] || exit $rc; sort -u -o evidence/<活動フォルダ>/artifacts/storage-urls.txt evidence/<活動フォルダ>/artifacts/storage-urls.txt`。「No such file」で止まったら先に metafiles-crawl を回す（uv run scripts/run_target.py --target target --only metafiles-crawl）
2. 抽出した各ストレージのホストルートに匿名アクセスできるか確認: `while read -r u; do b=$(echo "$u" | sed -E 's#(https?://[^/]+).*#\1/#'); echo "===== $b ====="; curl -s -m 10 -o /dev/null -w 'code %{http_code}\n' "$b"; curl -s -m 10 "$b" | head -c 300; echo; done < evidence/<活動フォルダ>/artifacts/storage-urls.txt | tee evidence/<活動フォルダ>/artifacts/storage-anon.txt`。`ListBucketResult`/ディレクトリ一覧が返る、または 200 で中身が見えるものは匿名読取可
3. S3 ホスト名からバケット名を割り出し、匿名で一覧できるか確認: `grep -oiE '[a-z0-9.-]+\.s3[a-z0-9.-]*\.amazonaws\.com' evidence/<活動フォルダ>/artifacts/storage-urls.txt | sed -E 's#\.s3.*##' | sort -u | while read -r b; do echo "===== $b ====="; aws s3 ls --no-sign-request "s3://$b" 2>&1 | head -20; done | tee evidence/<活動フォルダ>/artifacts/s3-list.txt`。書き込み可否（aws s3 cp での書き込み）は破壊的になり得るので、許可範囲を確認してから手動で試す
4. 公開が業務上意図されたものか切り分け、意図しない公開のみ finding にする

## 使用ツール

- curl
- AWS CLI

## 判定基準（pass / fail の見分け）

- **pass**: バケット・コンテナが匿名アクセス不可、または公開すべきファイルのみ公開。
- **fail**: 一覧取得や任意ファイル取得が匿名でできる、または書き込みができる。
- 補足: 書き込み可否の確認は影響が大きい。実施前に許可範囲を確認し、無害なファイル名で検証する。手順1 は SPA が画面操作で動的に読むストレージ URL を index.html・JS からは拾えないので、WSTG-INFO-08 手順4 の HAR があればそこからも拾う（HAR が無ければ静的に見える分だけ）。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-bucket.txt`, `artifacts/dangling-dns.md`
- `covers:` — `{id: WSTG-CONF-11, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/11-Test_Cloud_Storage
