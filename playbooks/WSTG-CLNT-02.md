# WSTG-CLNT-02 — Testing for JavaScript Execution

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が JS の実行文脈に入り込まないかを確認する。

WSTG の Test Objectives:

- Identify sinks and possible JavaScript injection points.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `javascript:` スキームや DOM 経由でユーザ入力が `eval`/`setTimeout`/`Function` に渡らないか確認
2. 入力から JS 実行に至る経路をブラウザ開発者ツール（DevTools）のブレークポイントで追う
3. フレームワークのテンプレート評価（`ng-`,`v-` バインド等）で式が実行されないか確認
4. 実行が成立するシンクを finding に。DOM XSS（CLNT-01）と重なる点に注意

## 使用ツール

- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: JS 文字列に埋め込まれる値がエスケープされ、文脈を抜け出せない。
- **fail**: eval / setTimeout / Function に外部由来の値が渡り実行される。
- 補足: CLNT-01 と重なる。どのシンクで成立したかを finding に明記する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/02-Testing_for_JavaScript_Execution
