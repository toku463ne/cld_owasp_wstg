# WSTG-SESS-03 — Testing for Session Fixation

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ログイン前のセッション ID が継続利用されないか（セッション固定）を確認する。

WSTG の Test Objectives:

- Analyze the authentication mechanism and its flow.
- Force cookies and assess the impact.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. In this section we give an explanation of the testing strategy that will be shown in the next section.
2. The first step is to make a request to the site to be tested (e.g. www.example.com). If the tester requests the following:
3. `GET / HTTP/1.1 Host: www.example.com
4. They will obtain the following response:
5. `HTTP/1.1 200 OK Date: Wed, 14 Aug 2008 08:45:11 GMT Server: IBM_HTTP_Server Set-Cookie: JSESSIONID=0000d8eyYq3L0z2fgq10m4v-rt4:-1; Path=/; secure Cache-Control: no-cache="set-cookie,set-coo …
6. The application sets a new session identifier, JSESSIONID=0000d8eyYq3L0z2fgq10m4v-rt4:-1, for the client.
7. Next, if the tester successfully authenticates to the application with the following POST to https://www.example.com/authentication.php:

## 使用ツール

- OWASP ZAP

## 判定基準（pass / fail の見分け）

- **pass**: 認証成功時にセッション ID が再発行され、旧 ID は無効になる。
- **fail**: ログイン前後で同じセッション ID が使え、事前に仕込んだ ID で認証済みセッションを乗っ取れる。
- 補足: 権限が変わる操作（昇格・切替）でも再発行されるかを見る。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/session-trace.burp`, `artifacts/token-samples.txt`, `notes.md`
- `covers:` — `{id: WSTG-SESS-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/03-Testing_for_Session_Fixation
