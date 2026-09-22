# WSTG-CRYP-02 — Testing for Padding Oracle

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

暗号文の改変に対する応答差から平文を復元できないか（パディングオラクル）を確認する。

WSTG の Test Objectives:

- Identify encrypted messages that rely on padding.
- Attempt to break the padding of the encrypted messages and analyze the returned error messages for further analysis.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 暗号化トークン/Cookie を1バイトずつ改変して送り（Burp/`padbuster`）、パディングエラーと復号エラーで応答差が出るか確認
2. CBC モードの復号を伴うパラメータ（暗号化された ViewState/Cookie）を対象に選ぶ
3. 応答差・エラーメッセージ・応答時間からパディングオラクルの兆候を確認
4. 成立時は平文復元/改ざんの可能性。実証は最小限に留め finding に

## 使用ツール

- Burp Suite
- padbuster

## 判定基準（pass / fail の見分け）

- **pass**: 復号失敗時の応答が一様で、パディング誤りと内容誤りを区別できない。
- **fail**: 応答内容・ステータス・時間差で復号可否が判別でき、平文を復元できる。
- 補足: 対象は Cookie・ViewState・URL 中の暗号化トークン。実行前に負荷と件数を合意する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/crypto-review.md`, `cmd/padbuster.txt`
- `covers:` — `{id: WSTG-CRYP-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `crypto-review` — 暗号利用のレビュー（パディングオラクル・弱い暗号・平文送出）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/02-Testing_for_Padding_Oracle
