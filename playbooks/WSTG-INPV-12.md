# WSTG-INPV-12 — Testing for Command Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が OS コマンドの一部として実行されないかを確認する。

WSTG の Test Objectives:

- Identify and assess the command injection points.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. OS コマンドを組み立てる入力に `; id` `| id` `$(id)` `` `id` `` `&& id` を注入して実行されるか確認
2. 出力が返らない場合は時間差（`; sleep 5`）・アウトオブバンド（`; nslookup me.oob`）で確認
3. Windows 系は `& whoami` `| whoami` も試す
4. 成立時は RCE として最優先。実行は無害コマンド（id/whoami）に留め finding に要約

## 使用ツール

- nslookup

## 判定基準（pass / fail の見分け）

- **pass**: シェルを介さない実行、または引数のホワイトリスト検証がされている。
- **fail**: ; | && $() 等でコマンドを連結・実行できる（時間差やアウトオブバンドで確認）。
- 補足: 破壊的コマンドは絶対に使わない。id・sleep など無害なもので証明する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-12, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/12-Testing_for_Command_Injection
