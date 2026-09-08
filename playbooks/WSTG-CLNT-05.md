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

1. Code should be analyzed to determine if a user is permitted to inject content in the CSS context.
2. The following is a basic example:
3. `<a id="a1">Click me</a> <b>Hi</b> <script> $("a").click(function(){ $("b").attr("style","color: " + location.hash.slice(1)); }); </script>
4. The above code contains a source location.hash, controlled by the attacker, that can inject directly in the style attribute of an HTML element.
5. The following pages provide examples of CSS injection vulnerabilities:
6. Password "cracker" via CSS and HTML5
7. JavaScript based attacks using CSSStyleDeclaration with unescaped input

## 使用ツール

- ブラウザ開発者ツール
- DOM Invader
- Retire.js
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: スタイル指定に外部入力が渡らない。
- **fail**: 任意 CSS を注入でき、属性セレクタ等で入力値を外部へ送出できる。
- 補足: 影響の説明が難しい項目。PoC を artifacts に残すと伝わりやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/05-Testing_for_CSS_Injection
