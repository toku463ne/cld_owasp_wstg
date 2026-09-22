# WSTG-ATHZ-01 — Testing Directory Traversal File Include

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

パス・ファイル名を扱う機能で、意図しないファイルを読めないかを確認する。

WSTG の Test Objectives:

- Identify injection points that pertain to path traversal.
- Assess bypassing techniques and identify the extent of path traversal.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ファイル参照パラメータ（`?file=`,`?page=`,`?lang=`）に `../../etc/passwd`・`..\..\` を Burp Repeater で入れて範囲外読取を試す
2. エンコード変種（`%2e%2e%2f`・二重エンコード `%252e`・`....//`）で WAF/フィルタを迂回できるか `dotdotpwn` 等で試す
3. 絶対パス指定・null バイト・拡張子付与（`file=../../etc/passwd%00.png`）も試す
4. LFI で設定ファイル/ソースが読める、または include で任意ファイルを実行できるか確認

## 使用ツール

- Burp Repeater
- DotDotPwn

## 判定基準（pass / fail の見分け）

- **pass**: パス文字列がホワイトリスト等で正規化・検証され、範囲外を指定すると拒否される。
- **fail**: ../ や絶対パス、エンコード変種（%2e%2e/）で範囲外のファイルを読める・インクルードできる。
- 補足: 読み出せた事実だけを記録し、機微ファイルの中身は必要最小限にとどめる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/traversal.txt`, `artifacts/traversal-findings.md`
- `covers:` — `{id: WSTG-ATHZ-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `traversal-probe` — ディレクトリトラバーサル・ファイルインクルードの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/01-Testing_Directory_Traversal_File_Include
