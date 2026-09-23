# WSTG-INFO-10 — Map Application Architecture

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

WAF・LB・リバースプロキシ・API GW・DB など、経路上の構成要素を推定する。

WSTG の Test Objectives:

- Generate a map of the application at hand based on the research conducted.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 応答ヘッダを保存して中間装置の印を探す: `curl -sD evidence/<活動フォルダ>/artifacts/resp-headers.txt -o /dev/null https://target/ && grep -iE '^(via|x-cache|x-served-by|server|set-cookie|x-forwarded-for|cf-ray|x-varnish|x-amz-cf-id):' evidence/<活動フォルダ>/artifacts/resp-headers.txt`。ヒットしたヘッダ（`Via`/`X-Cache`=キャッシュ・LB、`cf-ray`=Cloudflare 等）から中間装置を推定
2. 経路上のホップを観測: `traceroute -w2 -q1 target | tee evidence/<活動フォルダ>/artifacts/traceroute.txt`（TTL・応答差から CDN/リバースプロキシの位置を推定）。WAF の有無は後続 INPV 系での不正入力への 403/406 で炙り出す
3. recon で得たホストを evidence/<活動フォルダ>/artifacts/hosts.txt に1行1件で置き（subfinder.txt 等から）、本来内部向けの装置が外から開いていないか一括確認: `while read -r h; do for pp in :9200 :5601 :15672 :8081 :2375 /phpmyadmin/ /adminer/; do echo "$h$pp -> $(curl -s -k -m 8 -o /dev/null -w '%{http_code}' "https://$h$pp")"; done; done < evidence/<活動フォルダ>/artifacts/hosts.txt | tee evidence/<活動フォルダ>/artifacts/internal-exposure.txt`。200/401 が返る＝外部露出（:9200 Elasticsearch・:5601 Kibana・:15672 RabbitMQ・:8081・:2375 Docker・phpmyadmin/adminer=DB管理）。意図しない露出のみ finding に
   > ⚠️ **負荷注意（手順3）**: 多数のホスト×ポートへ順次接続する。ホスト数が多いと接続数と時間がかさみ、内部の装置に想定外の負荷がかかりうる。まず件数を絞って挙動を見る。
4. 推定した構成図を描き、ヒアリング結果と突き合わせて確定（推測のまま報告しない）

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順3**: 多数のホスト×ポートへ順次接続する。ホスト数が多いと接続数と時間がかさみ、内部の装置に想定外の負荷がかかりうる。まず件数を絞って挙動を見る。

## 使用ツール

- curl
- traceroute
- subfinder

## 判定基準（pass / fail の見分け）

- **pass**: 構成が把握でき、防御機構（WAF 等）の有無と位置を説明できる。
- **fail**: 本来内部にあるべき構成要素（管理系 API・キャッシュ・DB 管理画面）が外部から直接見えている。
- 補足: 構成推定はヒアリングと突き合わせる。推測のまま報告しない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/entry-points.txt`, `artifacts/sitemap.xml`, `notes.md`
- `covers:` — `{id: WSTG-INFO-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/10-Map_Application_Architecture
