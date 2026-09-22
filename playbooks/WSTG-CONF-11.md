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

1. アプリが参照するストレージ URL を HTML/JS から抽出: `curl -s https://target/ -o evidence/<活動フォルダ>/artifacts/index.html; grep -oiE 'src="[^"]+\.js[^"]*' evidence/<活動フォルダ>/artifacts/index.html | sed -E 's/^src="//I' | while read -r j; do case "$j" in http*) curl -s "$j";; /*) curl -s "https://target$j";; *) curl -s "https://target/$j";; esac; done > evidence/<活動フォルダ>/artifacts/app-js.txt; grep -rhoiE 'https?://[A-Za-z0-9._-]+\.(s3[A-Za-z0-9.-]*\.amazonaws\.com|s3\.amazonaws\.com|blob\.core\.windows\.net|storage\.googleapis\.com)[A-Za-z0-9._~:/?#@!$&*+,;=%-]*' evidence/<活動フォルダ>/artifacts/index.html evidence/<活動フォルダ>/artifacts/app-js.txt | sort -u | tee evidence/<活動フォルダ>/artifacts/storage-urls.txt`。動的生成 URL は取りこぼすので、SPA では Burp/ZAP のサイトマップで補う
2. 抽出した各ストレージのホストルートに匿名アクセスできるか確認: `while read -r u; do b=$(echo "$u" | sed -E 's#(https?://[^/]+).*#\1/#'); echo "===== $b ====="; curl -s -m 10 -o /dev/null -w 'code %{http_code}\n' "$b"; curl -s -m 10 "$b" | head -c 300; echo; done < evidence/<活動フォルダ>/artifacts/storage-urls.txt | tee evidence/<活動フォルダ>/artifacts/storage-anon.txt`。`ListBucketResult`/ディレクトリ一覧が返る、または 200 で中身が見えるものは匿名読取可
3. S3 ホスト名からバケット名を割り出し、匿名で一覧できるか確認: `grep -oiE '[a-z0-9.-]+\.s3[a-z0-9.-]*\.amazonaws\.com' evidence/<活動フォルダ>/artifacts/storage-urls.txt | sed -E 's#\.s3.*##' | sort -u | while read -r b; do echo "===== $b ====="; aws s3 ls --no-sign-request "s3://$b" 2>&1 | head -20; done | tee evidence/<活動フォルダ>/artifacts/s3-list.txt`。書き込み可否（`aws s3 cp` 相当）は破壊的になり得るので、許可範囲を確認してから手動で試す
4. 公開が業務上意図されたものか切り分け、意図しない公開のみ finding にする

## 使用ツール

- curl
- Burp Suite
- OWASP ZAP
- AWS CLI

## 判定基準（pass / fail の見分け）

- **pass**: バケット・コンテナが匿名アクセス不可、または公開すべきファイルのみ公開。
- **fail**: 一覧取得や任意ファイル取得が匿名でできる、または書き込みができる。
- 補足: 書き込み可否の確認は影響が大きい。実施前に許可範囲を確認し、無害なファイル名で検証する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-bucket.txt`, `artifacts/dangling-dns.md`
- `covers:` — `{id: WSTG-CONF-11, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/11-Test_Cloud_Storage
