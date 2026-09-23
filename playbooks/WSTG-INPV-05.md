# WSTG-INPV-05 — Testing for SQL Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が SQL 文の構造に影響しないかを確認する。

WSTG の Test Objectives:

- Identify SQL injection points.
- Assess the severity of the injection and the level of access that can be achieved through it.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 各パラメータに `'` `"` を入れ、SQL エラー・応答差・500 が出るか確認
2. `' OR '1'='1' -- ` や `1 AND 1=1`/`1 AND 1=2` の真偽差でブラインド SQLi を確認
3. 時間差（`' OR SLEEP(5)-- `）で盲目的注入を確認。文脈（数値/文字列）に応じて調整
4. `sqlmap -u "https://target/x?id=1" ${WSTG_PAUSE:+--delay "$WSTG_PAUSE"} ${https_proxy:+--proxy="$https_proxy"} --batch --output-dir=evidence/<活動フォルダ>/artifacts`（許可範囲で）で確証。取得データは要約のみ finding に。sqlmap は多数の試行を送るので、非力な対象では `export WSTG_PAUSE=2` でリクエスト間に待ちを入れる（既定 `--threads 1` のまま上げない）。sqlmap は環境変数のプロキシを見ないので、プロキシ経由なら `--proxy` を明示する
   > ⚠️ **負荷注意（手順4）**: sqlmap は多数の試行リクエストを送り、time-based 検出では遅延も伴う。`--batch` でも重い。非力な対象は `export WSTG_PAUSE=2` でリクエスト間に待ちを入れ、`--threads` は上げない。許可範囲・時間帯を守る。

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順4**: sqlmap は多数の試行リクエストを送り、time-based 検出では遅延も伴う。`--batch` でも重い。非力な対象は `export WSTG_PAUSE=2` でリクエスト間に待ちを入れ、`--threads` は上げない。許可範囲・時間帯を守る。

## 使用ツール

- sqlmap

## 判定基準（pass / fail の見分け）

- **pass**: 入力を変えてもエラー・応答時間・件数に構造的な変化がなく、プレースホルダ利用が確認できる。
- **fail**: エラーベース・ブーリアン・時間差のいずれかで SQL の挙動を制御できる。
- 補足: sqlmap は許可範囲と負荷に注意。--risk/--level を上げる前に合意を取る。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection
