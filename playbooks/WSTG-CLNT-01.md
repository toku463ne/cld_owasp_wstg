# WSTG-CLNT-01 — Testing for DOM-Based Cross Site Scripting

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

クライアント側 JS のシンクで XSS が成立しないかを確認する。

WSTG の Test Objectives:

- Identify DOM sinks.
- Build payloads that pertain to every sink type.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. URL フラグメント/パラメータを DOM に書き込む JS（`document.write`,`innerHTML`,`location`,`eval`）をブラウザ開発者ツールの Sources で探す
2. `#<img src=x onerror=alert(1)>` 等をシンクに流し込み、サーバを介さず DOM 上で発火するか確認
3. ソース（`location.hash`,`document.referrer`）→シンクの経路を DevTools や Burp DOM Invader で追跡
4. どのシンクで成立したかを finding に明記（CLNT-01 と INPV-01 の切り分け）

## 使用ツール

- ブラウザ開発者ツール
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: location.hash 等のソースが innerHTML・eval 等のシンクに未処理で渡らない。
- **fail**: URL フラグメントやクエリが DOM シンクへ流れ、スクリプトが実行される。
- 補足: サーバ応答は無害でも成立する。フラグメントはサーバログに残らない点も説明する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/xss-findings.md`, `artifacts/payloads.txt`
- `covers:` — `{id: WSTG-CLNT-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `xss-probe` — XSS・HTML インジェクションの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/11-Client-side_Testing/01-Testing_for_DOM-based_Cross_Site_Scripting
