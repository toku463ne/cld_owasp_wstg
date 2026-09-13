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

1. ログイン前のセッション ID を控え、ログイン後に同じ ID が使い続けられる（再発行されない）か確認
2. 攻撃者が用意した ID を被害者に食わせてログインさせ、その ID で成り済ませるか検証
3. URL/パラメータでセッション ID を注入できないか確認
4. ログイン成功時に必ず新しい ID が発行されるなら pass。据え置きなら固定攻撃可として fail

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
