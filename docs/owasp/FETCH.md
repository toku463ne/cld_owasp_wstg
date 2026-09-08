# WSTG 原文の取得元とバージョン

このディレクトリの中身（この `FETCH.md` を除く）は **追跡しない**。
公開情報かつ大容量のため、必要なら下記の手順で再取得する。

## ピン留めしているバージョン

| 項目 | 値 |
|------|-----|
| ガイド | OWASP Web Security Testing Guide |
| バージョン | **v4.2**（stable） |
| 取得元（正） | `https://github.com/OWASP/wstg` タグ `v4.2` のソース tarball |
| 取得 URL | `https://codeload.github.com/OWASP/wstg/tar.gz/refs/tags/v4.2` |
| 展開先 | `docs/owasp/wstg-4.2/`（Markdown 原文） |
| 取得元（副） | `https://owasp.org/www-project-web-security-testing-guide/stable/` |
| 展開先（副） | `docs/owasp/stable/`（HTML ミラー） |

WSTG のテスト本体は `document/4-Web_Application_Security_Testing/` 配下にあり、
各ファイルの先頭に `WSTG-XXXX-NN` 形式の ID 表が入っている。
本リポジトリのスクリプトは **Markdown 版・HTML ミラー版のどちらでも** 解析できる。

## 取得コマンド

```bash
# 既定：v4.2 の Markdown 原文をピン留め取得
./scripts/fetch_wstg.sh

# 参考：公開サイトの HTML ミラー（wget が必要。任意）
./scripts/fetch_wstg.sh --html-mirror
```

取得後、テスト一覧を再生成する場合：

```bash
uv run scripts/build_wstg_index.py     # -> matrix/wstg_tests.yaml
uv run scripts/gen_playbooks.py        # -> playbooks/WSTG-*.md
```

## 注意

- 原文は公開情報だが、**このリポジトリにはコミットしない**（`.gitignore` 済み）。
- `docs/owasp/` 配下に実案件のデータ（評価シート・エビデンス等）を置かないこと。
  置いてしまった場合も、AI にはそのパスを読ませない。
