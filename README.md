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
evidence/<activity>-<date>/run.yaml ─┬─▶ export_checklist.py ─▶ checklist_export.csv
   ▲                                  │                                │
   └ run_cmd.py（実行ログを自動追記）  └─▶ tasks.py（進捗表示）  目視レビュー ▼
                                                              Google Sheets
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

## 日々の流れ

`TASKS.md` を上から消化していく。1本のアクティビティで踏むのは 1〜3、
区切りのたびに 4〜5 を回す。

### 1. アクティビティを開始する

```bash
uv run scripts/new_activity.py burp-crawl-authn
# -> evidence/burp-crawl-authn-20260908/{run.yaml,worksheet.md,cmd/,artifacts/,notes.md}

# 複数サイトは --target で名前空間を分ける（コマンド中の target も置換される）
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

### 2. コマンドを実行し、出力を集める

やり方は2通り。どちらも `cmd/<slug>.txt` と `run.yaml` の `commands:` に残る。

**(a) 貼付ワークシート方式**（ツールを別環境で回すとき・複数サイトで効率化したいとき）

`worksheet.md` にカードの実コマンドが target 置換済みで並ぶ。各コマンドを実行し、
出力を直後の ` ```paste ` ブロックに貼り、WSTG-ID ごとに `@verdict` / `@finding` を記入する。

```bash
# 記入後、まとめて取り込み（コマンドごとに別ファイル＝ツール別フォーマットで残る）
uv run scripts/capture.py evidence/recon-osint-example.com-20260913
# -> cmd/whois.txt, cmd/theHarvester-...txt などを生成し、run.yaml の covers も更新
```

**(b) ロガー経由で直接実行**（このリポジトリ上でそのまま走らせるとき）

```bash
uv run scripts/run_cmd.py evidence/burp-crawl-authn-20260908 -- nmap -sV -p- target.example
uv run scripts/run_cmd.py evidence/tls-scan-20260908 --note "本番のみ" -- testssl.sh --quiet target.example
```

- **GUI ツール（Burp / ZAP など）は対象外**。何をしたかを `run.yaml` の `steps:` に手記録する。
  ここが再現メモになるので、スコープ設定・使った機能・エクスポート先まで書く。

### 3. 判定を書く

`run.yaml` の `covers:` を埋める。

```yaml
covers:
  - id: WSTG-INFO-06
    verdict: pass          # pass | fail | info | na | todo
    finding: "エントリポイントを列挙。認証必須の管理系2件を確認（生値は artifacts 参照）"
    evidence: artifacts/entry-points.txt
```

`finding` は **要約のみ**。生トークン・資格情報・生ホスト名は書かず、`evidence:` の
パスで実物を参照させる。

### 4. 進捗を確認する

```bash
uv run scripts/tasks.py
#   [x]  1. recon-osint          完了   2/2 判定済み
#   [~]  2. fingerprint-stack    実施中  2/4 判定済み
#   [ ]  3. tls-scan             未着手  前提未完: fingerprint-stack
#   次にやること: 2. fingerprint-stack — …
```

`evidence/*/run.yaml` の `verdict` を見て、アクティビティ単位の進捗と「次にやること」
（前提が終わっていて着手できるもの）を出す。

### 5. チェックリストを出力する

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
