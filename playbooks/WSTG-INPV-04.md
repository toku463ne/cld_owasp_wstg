# WSTG-INPV-04 — Testing for HTTP Parameter Pollution

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

同名パラメータを複数送ったときの解釈揺れを悪用できないかを確認する。

WSTG の Test Objectives:

- Identify the backend and the parsing method used.
- Assess injection points and try bypassing input filters using HPP.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Server-Side HPP** — To test for HPP vulnerabilities, identify any form or action that allows user-supplied input
2. **Client-Side HPP** — Similarly to server-side HPP, manual testing is the only reliable technique to audit web applications in order to detect parameter pollution …

## 使用ツール

- OWASP ZAP Passive/Active Scanners

## 判定基準（pass / fail の見分け）

- **pass**: 重複パラメータが拒否されるか、経路上のすべての要素で同じ解釈になる。
- **fail**: WAF とアプリで解釈が異なり、検証を通過して別の値が使われる。
- 補足: フロント（WAF/LB）とバックエンドの解釈差が本質。両方の応答を並べて記録する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- `covers:` — `{id: WSTG-INPV-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `http-request-tamper` — HTTP リクエスト改変系の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/04-Testing_for_HTTP_Parameter_Pollution
