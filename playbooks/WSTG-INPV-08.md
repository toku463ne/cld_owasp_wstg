# WSTG-INPV-08 — Testing for SSI Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

SSI（Server Side Includes）ディレクティブが入力経由で実行されないかを確認する。

WSTG の Test Objectives:

- Identify SSI injection points.
- Assess the severity of the injection.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. SSI を使い得る環境で入力に `<!--#exec cmd="id"-->` `<!--#include file="..."-->` を Burp で注入
2. 反映先が `.shtml` 等 SSI 有効ページか、注入がサーバ側で解釈されるか確認
3. コマンド実行・ファイルインクルードが成立するか、出力で確認
4. レガシー環境で残りがち。成立時は RCE 相当として扱う

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: SSI が無効、または入力中の <!--#exec 等が文字列として扱われる。
- **fail**: SSI ディレクティブが解釈され、ファイル読み出しやコマンド実行に至る。
- 補足: .shtml が有効なレガシー環境で残っていることがある。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/08-Testing_for_SSI_Injection
