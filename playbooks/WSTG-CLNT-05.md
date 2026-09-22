# WSTG-CLNT-05 — Testing for CSS Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が CSS として解釈され、情報の抜き出しや表示改変ができないかを確認する。

WSTG の Test Objectives:

- Identify CSS injection points.
- Assess the impact of the injection.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. スタイルに反映される入力に CSS 注入（`}body{background:url(...)}` や属性セレクタ）ができるか確認
2. CSS で入力値を推測・外部送信（属性セレクタ + 背景画像リクエスト）できないか確認
3. `style` 属性/`<style>` へのユーザ入力反映をブラウザ開発者ツールで確認
4. 情報漏えい・画面改ざんにつながる注入を finding に

## 使用ツール

- ブラウザ開発者ツール

## 判定基準（pass / fail の見分け）

- **pass**: スタイル指定に外部入力が渡らない。
- **fail**: 任意 CSS を注入でき、属性セレクタ等で入力値を外部へ送出できる。
- 補足: 影響の説明が難しい項目。PoC を artifacts に残すと伝わりやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/05-Testing_for_CSS_Injection
