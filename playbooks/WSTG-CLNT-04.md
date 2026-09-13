# WSTG-CLNT-04 — Testing for Client-side URL Redirect

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

リダイレクト先をクライアント側入力で任意指定できないかを確認する。

WSTG の Test Objectives:

- Identify injection points that handle URLs or paths.
- Assess the locations that the system could redirect to.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. リダイレクト先を決めるパラメータ（`?next=`,`?url=`,`?return=`）に外部 URL を `curl`/Burp で入れて飛ぶか確認
2. `//evil.example`・`https:evil.example`・`\/\/evil` などスキーム相対/変種で迂回を試す
3. オープンリダイレクトがフィッシング・OAuth トークン奪取に使えないか確認
4. 外部ドメインへ誘導できた場合はオープンリダイレクトとして finding に

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 遷移先が許可リストまたは相対パスに限定される。
- **fail**: ?next=//evil.example のような指定で外部サイトへ遷移させられる。
- 補足: フィッシングの踏み台になる。ログイン後遷移が典型的な入口。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- `covers:` — `{id: WSTG-CLNT-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/04-Testing_for_Client-side_URL_Redirect
