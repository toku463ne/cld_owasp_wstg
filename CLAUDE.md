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
- 外部通信するのは `scripts/fetch_wstg.sh`（WSTG 原文の取得）だけ。
  他のスクリプトからネットワークアクセスを追加しない（Google Sheets 連携は廃止済み。戻さない）。
- Web（`scripts/serve_record.py`）は `evidence/` をチームに見せる唯一の経路。
  **127.0.0.1 でしか待ち受けない**（`--host` に非 loopback を渡すと起動を拒否する）。共有は同じ機械の
  nginx（社内ネットワーク限定・TLS・認証。`templates/nginx/wstg.conf`）経由だけ。
  この制限・書き込み API の CSRF 検査（`X-WSTG-Request` ヘッダ＋Origin/Host 一致）・
  `X-Remote-User` を `--behind-proxy` のときだけ信用する挙動を緩める変更はしない。

## 2. どのファイルを直すか（最重要）

**手で編集するのはこの4つだけ**:

| ファイル | 中身 |
|---|---|
| `matrix/coverage.yaml` の `phases:` と `activities:` | アクティビティ定義・実施順（唯一の真実） |
| `matrix/criteria.yaml` | カードの目的・pass/fail 判定基準 |
| `scripts/*` | ツール本体 |
| `README.md` / `CLAUDE.md` / `templates/**` | ドキュメントと雛形（`run.yaml`・`artifacts/` の成果物フォーマット・`nginx/` の共有設定例） |

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
coverage.yaml ─┬─▶ TASKS.md（実施順・テキスト版）
               └─▶ new_activity.py ─▶ evidence/*/{run.yaml, record.html, cmd/, artifacts/}
                     run_activity.py ─▶ criteria.yaml の手順を bash 実行
                        ├─▶ cmd/<WSTG-ID>-s<n>-c<k>.txt（コマンドごとの純粋なエビデンス）
                        ├─▶ run.yaml の commands: に追記
                        └─▶ evidence.js（gen_record.py も同じ。所見の要約も載る）
                     save_shot.py / Web の画像貼り付け ─▶ artifacts/shot-<WID>[-s<n>]-*.png
                     record.html（WSTG-ID タブ）◀─(iframe/img 参照)─ cmd/・artifacts/（evidence.js はメタデータ）
evidence/_findings/F-*.md（所見。findings.py が読み書き）─ WSTG と多対多・cvss ベクトル・evidence パス
   └─ 深刻度は cvss31.py がベクトルから毎回計算（保存しない）
evidence/_state/checks.yaml（タスクの手動チェック。Web が書く）
serve_record.py（127.0.0.1）＋ web_pages.py（描画）─ nginx の後ろでチーム共有
   ├─ GET  / /tasks /wstg/ /wstg/<ID> /findings/ /findings/<F> /playbooks/<ID> /export.csv /<act>/record.html
   ├─ POST /<act>/api/save ─▶ update_cover(run.yaml)（verdict / finding=判定理由のテキスト部分置換）
   ├─ POST /<act>/api/{save_output,upload_shot,delete_shot,capture} ─▶ cmd/・artifacts/
   ├─ POST /api/finding/{save,attach} ─▶ _findings/（版 rev の不一致は 409）
   └─ POST /api/check ─▶ _state/checks.yaml
run.yaml の covers ＋ _findings ─▶ export_checklist.py ─▶ CSV（/export.csv も同じ）
run.yaml ─▶ tasks.py（端末の進捗表示）
```

`new_activity.py` はフォルダ一式（`run.yaml`・静的ビューア `record.html`・`cmd/`・`artifacts/`・
手動手順の `manual-*.txt` ひな型）を作る。`run.yaml` の `finding` は**判定理由の1行**（CSV に載る。
複数行は `finding: |`、CSV では `one_line` で畳む）。問題の中身は**所見**（`evidence/_findings/F-*.md`）に書き、
1つの WSTG に複数の所見を紐づける（旧 `findings.md` は廃止。`findings.py migrate` で移行）。
`run_activity.py` は `criteria.yaml` の手順のうち「コマンド手順」（`backtick` で target/OUTDIR を参照する
`$` 実行コマンド）を bash で実行し、出力をコマンドごとに `cmd/<WSTG-ID>-s<n>-c<k>.txt` に残す
（＝純粋なエビデンス。ドキュメントには埋め込まない）。
`gen_record.py` は実行せず、`run.yaml` と既存のエビデンスから `record.html`／`evidence.js` を
作り直すだけ。**エビデンスは cmd/・artifacts/、判定は run.yaml、所見は _findings/ にあるので、上流を更新して
手順が変わっても `gen_record.py` で作り直すだけでよく、過去のエビデンスをコピーし直さずに済む。**

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

- **`run.yaml` は必ずテキストで部分編集する（PyYAML で丸ごと書き戻さない）**。
  コメント・並び・空行・手記録の意図が消えるため。`run_cmd.py`／`run_activity.py` は `commands:` に
  追記、`update_cover`（serve_record の `/api/save` が呼ぶ）は `covers` の該当 id ブロックの
  `verdict`/`finding` 行だけを部分置換する（`finding` は複数行ならブロックスカラー）。
  `gen_record.py` は `run.yaml` を **読むだけ**。判定を書く経路はこの2つ（人手の直接編集 / `/api/save`）だけ。
- **所見ファイルの front matter は `findings.py` の `render_text` が決まった順で書く**（Web 保存時は丸ごと
  書き直すので front matter 内のコメントは残らない。補足は本文へ）。**深刻度はファイルに保存しない**。
  `cvss` ベクトルから `cvss31.py` で毎回計算する（人が High/Medium を選ぶ UI・フィールドを足さない。
  根拠が残らなくなるため）。CVSS の計算式を JS に二重実装しない（Web は `/api/cvss` を呼ぶ）。
- **Web の書き込みは `serve_record.WRITE_LOCK` で直列化**し、所見の更新は読み込み時の `rev` と
  一致しなければ 409 にする（チームの同時編集で他人の更新を潰さない）。新しい書き込み API を足すときも
  `do_POST` の CSRF 検査とロックを通す。
- **エビデンス本体は `cmd/`・`artifacts/` のファイル、`record.html` はそれを参照するだけの表示**。
  `record.html` は静的で、手順・コマンド・判定などの**メタデータ**を `evidence.js`
  （`run_activity.py`／`gen_record.py` が生成）から読み、**各コマンドの出力は evidence.js に
  複製せず `<iframe>` で `cmd/`・`artifacts/` のファイルを直接参照する**（`file://` では `fetch`
  が遮断されるが iframe は同フォルダのファイルを表示できる）。だから `.txt` を手で編集したら
  リロードだけで反映される。この分離（生エビデンス＝ファイル / 判定＝run.yaml / 表示＝record.html）
  を崩さない。`build_evidence` で出力の中身を evidence.js に載せない（参照＝output_path のまま保つ）。
- **`export_checklist.py` の CSV 列は外部に渡す一覧の契約**（報告書への添付など。Sheets 連携は廃止）。
  列名・順序（`wstg_id, category, title, status, activities, evidence_paths,
  finding_summary, updated`）を変えるときは、人間に確認してから。`/export.csv` も同じ関数（`to_csv`）を使う。
- **集約ステータスの優先度は `fail > todo > info > pass > na`**。
  全 WSTG-ID を `todo` で初期化する（未実施が一目で分かることが目的）。
- **`finding`・所見タイトルは要約のみ**。生トークン・資格情報・生ホスト名を CSV や
  `matrix/`・`playbooks/` に持ち込まない。実物はエビデンスのパス参照で示す。
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
  `requires-python = ">=3.10"`、依存は **PyYAML のみ**（Web も標準ライブラリの `http.server`。
  Flask 等を足さない）。新しい依存を足す前に標準ライブラリで済まないか検討する。
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
- 管理は **Web 一本**（タスク＝指示書＋チェックリスト、WSTG 索引＝完了状況、所見、実施記録）。
  タスクの✓はできるだけ実施状況（run.yaml・cmd/・所見）から自動で付け、人が押すのは合意・レビュー
  のような「ファイルに現れない事実」だけにする（押し忘れで実態とずれるのを防ぐ）。
- 所見の深刻度は新人が判断するので、CVSS の設問（平易な質問＋判断理由）から機械的に出す。
  設問の文言は `cvss31.py` の `METRICS`、参考例は `web_pages.py` の `CVSS_EXAMPLES`。
- CSV（`checklist_export.csv`）は **概要のみ**。詳細は Web（各エビデンス・所見）を見れば分かる前提。
- `playbooks/WSTG-*.md` は **1テスト=1枚・自己完結・小さい**（目安 2KB 前後）。
  社内 Gemini にデータと一緒に貼れること、新人への説明台本に流用できることを満たす。
  機械抽出（手順・ツール・原文リンク）と手書きの判断（目的・pass/fail）を
  分離してあるのが肝。この分離を崩さない。
