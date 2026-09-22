# WSTG-INFO-03 — Review Webserver Metafiles for Information Leakage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

robots.txt・sitemap・security.txt・.well-known 配下から情報が漏れていないかを確認する。

WSTG の Test Objectives:

- Identify hidden or obfuscated paths and functionality through the analysis of metadata files.
- Extract and map other information that could lead to better understanding of the systems at hand.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 主要な公開ファイルを保存: `curl -s https://target/robots.txt -o evidence/<活動フォルダ>/artifacts/robots.txt; curl -s https://target/sitemap.xml -o evidence/<活動フォルダ>/artifacts/sitemap.xml; curl -s https://target/.well-known/security.txt -o evidence/<活動フォルダ>/artifacts/security.txt`
2. `curl -s https://target/.well-known/` 配下、`humans.txt`、`crossdomain.xml` も確認
3. robots.txt の Disallow 行が指す領域が認証なしで開くか確認: `grep -i '^Disallow:' evidence/<活動フォルダ>/artifacts/robots.txt | awk '{print $2}' | while read -r pth; do echo "$pth -> $(curl -s -o /dev/null -w '%{http_code}' https://target$pth)"; done | tee evidence/<活動フォルダ>/artifacts/robots-disallow-check.txt`。200 が返る行＝認証なしで到達可能なので中身を精査（非公開のはずの領域なら finding）
4. sitemap の URL が認証なしで開けるか確認: `grep -oiE '<loc>[^<]+' evidence/<活動フォルダ>/artifacts/sitemap.xml | sed -E 's#</?loc>##gI' | while read -r u; do echo "$u -> $(curl -s -o /dev/null -w '%{http_code}' "$u")"; done | tee evidence/<活動フォルダ>/artifacts/sitemap-check.txt`。非公開のはずの画面が 200 で列挙されていれば finding

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: メタファイルに非公開領域のパスや内部情報が書かれていない。
- **fail**: robots.txt の Disallow が管理画面・バックアップ等の場所を教えている、または sitemap に非公開 URL が載っている。
- 補足: Disallow はクロール抑止であってアクセス制御ではない、という説明を必ず添える。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/curl-robots.txt`, `cmd/curl-wellknown.txt`, `artifacts/comments-grep.txt`
- `covers:` — `{id: WSTG-INFO-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `metafiles-crawl` — メタファイル・公開コンテンツの収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/03-Review_Webserver_Metafiles_for_Information_Leakage
