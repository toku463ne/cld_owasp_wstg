# WSTG-INPV-13 — Testing for Format String Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

入力が書式文字列としてそのまま処理されないかを確認する。

WSTG の Test Objectives:

- Assess whether injecting format string conversion specifiers into user-controlled fields causes undesired behaviour from the application.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 書式指定を扱い得る入力（主にネイティブ実装）に `%s%s%s%s` `%x%x%x` `%n` を入れ、クラッシュ/メモリ露出を確認
2. 応答にスタックの値が漏れる・落ちるかを観察
3. Web アプリでは稀。C/C++ ネイティブ部品を持つ場合に重点確認
4. 成立時はメモリ破壊/情報漏えいとして finding に

## 使用ツール

- Burp Intruder
- sqlmap
- tplmap
- 手動 payload

## 判定基準（pass / fail の見分け）

- **pass**: %s %x 等が単なる文字として扱われる。
- **fail**: 書式指定子がメモリ内容の露出やクラッシュを引き起こす。
- 補足: C/C++ のネイティブ部品を持つアプリで主に該当。Web アプリでは稀。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-13, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/13-Testing_for_Format_String_Injection
