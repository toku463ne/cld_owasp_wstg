# WSTG-INPV-01 — Testing for Reflected Cross Site Scripting

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

URL・フォームの入力がそのまま応答に反映され、スクリプトが実行されないかを確認する。

WSTG の Test Objectives:

- Identify variables that are reflected in responses.
- Assess the input they accept and the encoding that gets applied on return (if any).

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 各パラメータに `<script>alert(1)</script>` や `"><img src=x onerror=alert(1)>` を入れ、応答に無害化されず反映されるか確認
2. 反映位置（HTML本文/属性値/JS内/URL）ごとに文脈に合ったペイロードを使い分ける
3. Burp で全パラメータを一括テスト、フィルタは大小文字・エンコード・イベントハンドラ変種で迂回を試す
4. 実際にブラウザで JS が実行されるか（アラート表示）まで確認して finding にする

## 使用ツール

- Burp Suite
- ブラウザ

## 判定基準（pass / fail の見分け）

- **pass**: 入力が文脈に応じてエスケープされ、ペイロードが文字列として表示される。
- **fail**: 反射した入力がスクリプトとして実行される（HTML・属性・JS・URL いずれの文脈でも）。
- 補足: 出力文脈ごとにペイロードを変える。WAF による部分ブロックは緩和であって修正ではない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/xss-findings.md`, `artifacts/payloads.txt`
- `covers:` — `{id: WSTG-INPV-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `xss-probe` — XSS・HTML インジェクションの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/01-Testing_for_Reflected_Cross_Site_Scripting
