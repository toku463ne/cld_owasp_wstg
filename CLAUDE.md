# CLAUDE.md — このリポジトリでの恒久ルール

このリポジトリは OWASP WSTG (v4.2) の実施を支援する **方法論とツールの置き場** である。
実データ（生エビデンス）はここでは扱わない。人間向けの使い方は `README.md`。

---

## 1. 絶対境界

- `evidence/**` は **読まない・書かない・要約しない**。存在しない前提で作業する。
  - スクリプトの動作確認も `evidence/` では行わない。一時ディレクトリに対して
    `--root <tmp>` / `--out-dir <tmp>` を使う（`scripts/selftest.sh` がその形）。
  - 実案件データらしきもの（`docs/owasp/evidence/**`、`docs/owasp/**/*.xlsx` など）にも
    一切アクセスしない。`scripts/wstg_parse.py` の `BLOCKED_PARTS` / `BLOCKED_SUFFIXES` が
    機械的な歯止め。ここを緩める変更はしない。
- `docs/owasp/**`（WSTG 原文）は公開情報なので **読んでよい**。ただし
  **コミット・追跡しない**（`.gitignore` 済み。`scripts/fetch_wstg.sh` で再取得できる）。
- 実データの分析・所見の作成依頼は **受けない**。担当はローカル手作業または社内 Gemini。
  依頼されたら、その旨を伝えて方法論側（スクリプト・カード・判定基準）の改善に誘導する。
- 外部通信するのは `scripts/fetch_wstg.sh`（WSTG 原文の取得）と
  `export_checklist.py --push`（人間が明示的に指定したときだけ）に限る。
  他のスクリプトからネットワークアクセスを追加しない。

## 2. どのファイルを直すか（最重要）

**手で編集するのはこの4つだけ**:

| ファイル | 中身 |
|---|---|
| `matrix/coverage.yaml` の `phases:` と `activities:` | アクティビティ定義・実施順（唯一の真実） |
| `matrix/criteria.yaml` | カードの目的・pass/fail 判定基準 |
| `scripts/*` | ツール本体 |
| `README.md` / `CLAUDE.md` / `templates/**` | ドキュメントと雛形（`run.yaml`・`artifacts/` の成果物フォーマット） |

**自動生成物（手で直しても次の生成で消える）**:

| 生成物 | 生成元 | 生成コマンド |
|---|---|---|
| `matrix/wstg_tests.yaml` | `docs/owasp/**`（WSTG 原文） | `python scripts/build_wstg_index.py` |
| `matrix/coverage.yaml` の自動生成マーカー以降 | 同ファイルの `activities:` | `python scripts/build_coverage.py` |
| `matrix/coverage.md` | 同上 | 同上 |
| `playbooks/WSTG-*.md`, `playbooks/INDEX.md` | 原文 + `matrix/criteria.yaml` + `coverage.yaml` | `python scripts/gen_playbooks.py` |

カードの文言を直したくなったら、カードではなく `matrix/criteria.yaml` を直して再生成する。
カードの構成そのもの（見出し・抽出ロジック）を変えるときは `scripts/gen_playbooks.py` を直す。

依存の向き:

```
docs/owasp（原文） ─▶ wstg_tests.yaml ─┬─▶ coverage.{yaml,md}（+ coverage.yaml の activities）
                                       └─▶ playbooks/（+ criteria.yaml）
coverage.yaml ─┬─▶ TASKS.md（実施順）
               └─▶ new_activity.py ─▶ evidence/*/{run.yaml, record.html, cmd/, artifacts/}
                     run_activity.py ─▶ criteria.yaml の手順を bash 実行
                        ├─▶ cmd/<WSTG-ID>-s<n>.txt（純粋なエビデンス）
                        ├─▶ run.yaml の commands: に追記
                        └─▶ evidence.js（gen_record.py も同じ）
                     record.html ◀─(表示)─ evidence.js（cmd/・artifacts/ を読む）
                     run.yaml の covers ─(人が verdict/finding を直接記入)
                        └─▶ export_checklist.py ─▶ CSV
                     run.yaml ─▶ tasks.py（進捗表示）
```

`new_activity.py` はフォルダ一式（`run.yaml`・静的ビューア `record.html`・`cmd/`・`artifacts/`・
手動手順の `manual-*.txt` ひな型）を作る。`run_activity.py` は `criteria.yaml` の手順のうち
「コマンド手順」（`backtick` で target/OUTDIR を参照する `$` 実行コマンド）を bash で実行し、
出力を `cmd/<WSTG-ID>-s<n>.txt` に丸ごと残す（＝純粋なエビデンス。ドキュメントには埋め込まない）。
`gen_record.py` は実行せず、`run.yaml` と既存のエビデンスから `record.html`／`evidence.js` を
作り直すだけ。**エビデンスは cmd/・artifacts/、判定は run.yaml にあるので、上流を更新して
手順が変わっても `gen_record.py` で作り直すだけでよく、過去のエビデンスをコピーし直さずに済む。**
判定（`verdict`/`finding`）は `run.yaml` の `covers` に人が直接書く（旧 `record.md`／`capture.py` は廃止）。

上流を変えたら下流を必ず再生成し、生成物の差分も一緒にコミットする
（原文の再取得後は `playbooks/` が大量に変わり得る。差分に目を通してからコミットする）。

## 3. 変更後の確認

```bash
./scripts/selftest.sh
```

生成物の鮮度・`matrix/*.yaml` の ID 整合・`new_activity` → `run_activity` → `gen_record` →
`export_checklist` の一連の動作・カード生成・機密境界（`evidence/` と `docs/owasp/` が追跡されていないこと）を
一時ディレクトリだけで検証する。**スクリプトを触ったらこれを通してからコミットする。**
挙動を変えたときは selftest 側のアサーションも更新する。

## 4. 壊してはいけない不変条件

- **`run_cmd.py` と `run_activity.py` は `run.yaml` の `commands:` にテキストとして追記する**。
  PyYAML で読み込んで丸ごと書き戻さない（コメント・並び・空行が消え、手記録の意図が失われる）。
  判定（`covers` の `verdict`/`finding`/`evidence`）は人が手で書く前提なので、スクリプトからは
  書き換えない（`gen_record.py` は `run.yaml` を **読むだけ**で書かない）。
- **エビデンス本体は `cmd/`・`artifacts/` のファイル、`record.html` はそれを読むだけの表示**。
  `record.html` は静的で、中身は同フォルダの `evidence.js`（`run_activity.py`／`gen_record.py` が
  生成）から読む。`file://` では `.txt` の `fetch` が遮断されるので `<script src>` で渡す設計。
  この分離（生エビデンス＝ファイル / 判定＝run.yaml / 表示＝record.html）を崩さない。`record.html`
  に生の出力を埋め込んだり、`evidence.js` を唯一のエビデンスにしたりしない（作り直しで消えるため）。
- **`export_checklist.py` の CSV 列は Google Sheets 側の契約**。
  列名・順序（`wstg_id, category, title, status, activities, evidence_paths,
  finding_summary, updated`）を変えるときは、人間に確認してから。
- **集約ステータスの優先度は `fail > todo > info > pass > na`**。
  全 WSTG-ID を `todo` で初期化する（未実施が一目で分かることが目的）。
- **`finding` は要約のみ**。生トークン・資格情報・生ホスト名を CSV や
  `matrix/`・`playbooks/` に持ち込まない。実物は `evidence:` のパス参照で示す。
- **WSTG は v4.2 にピン留め**。バージョンを上げるときは
  `scripts/fetch_wstg.sh` の `WSTG_VERSION`、`docs/owasp/FETCH.md`、
  `scripts/build_wstg_index.py` の `WSTG_VERSION` を揃えて更新し、全生成物を作り直す。
- **v4.2 で統合された3項目**（`WSTG-INFO-09` / `WSTG-INPV-03` / `WSTG-ERRH-02`）は
  単独実施しない。原文の "merged into" から自動判定しており、CSV では既定 `na`。
- **`docs/owasp` が無くても日常運用は動く**こと。`matrix/wstg_tests.yaml` を
  コミットしているのはそのため。原文を必須にする変更はしない。

## 5. コードの方針

- **Python 環境は uv で管理する**。`pyproject.toml` が依存の定義、`uv.lock` と
  `.python-version`（3.12）がピン留め。依存を変えたら `uv lock` の結果も一緒にコミットする。
  実行は `uv run scripts/xxx.py`。ドキュメントやメッセージでもこの形で案内する。
- ただし **uv が無い環境でも動くこと**（会社PC のフォールバック）。
  `requires-python = ">=3.10"`、依存は **PyYAML のみ**（`gspread` は `--push` のときだけの
  任意依存で遅延 import）。新しい依存を足す前に標準ライブラリで済まないか検討する。
  3.10 で動かない構文（`match` 以降の新機能など）は使わない。
- スクリプトは単体で実行でき、`--help` で用途が分かること。破壊的な既定値を持たない
  （既存ファイルは上書きせず、`--force` を要求する）。
- 出力メッセージは日本語。エラー時は「次に何をすればよいか」を必ず添える。
- コメント・docstring も日本語。既存のトーンに合わせる。

## 6. 設計の背景（変えるときに壊しやすい前提）

- WSTG 項目を1つずつ潰すのではなく、**収集アクティビティ単位**で動き、
  1回の収集で複数の WSTG-ID に一括でチェックを入れる。
  `covers[].role` の `primary`（単独で判定できる）/ `secondary`（入力・補強）の区別が
  カバレッジ評価の要。`coverage.md` の「未割当リスト」が抜け漏れの検知器。
- チェックリスト（`checklist_export.csv`）は **概要のみ**。詳細は各エビデンス
  フォルダを見れば分かる、という前提で書く。
- `playbooks/WSTG-*.md` は **1テスト=1枚・自己完結・小さい**（目安 2KB 前後）。
  社内 Gemini にデータと一緒に貼れること、新人への説明台本に流用できることを満たす。
  機械抽出（手順・ツール・原文リンク）と手書きの判断（目的・pass/fail）を
  分離してあるのが肝。この分離を崩さない。
