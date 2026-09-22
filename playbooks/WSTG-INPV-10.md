# WSTG-INPV-10 — Testing for IMAP SMTP Injection

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

メール送信機能経由で IMAP/SMTP コマンドを注入できないかを確認する。

WSTG の Test Objectives:

- Identify IMAP/SMTP injection points.
- Understand the data flow and deployment structure of the system.
- Assess the injection impacts.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. メール送信/検索機能の入力に CRLF（`%0d%0a`）やコマンド区切りを Burp で注入し、ヘッダ/コマンドを追加できるか確認
2. IMAP/SMTP コマンド（`\r\nHELO`・追加 `To:`/`Bcc:`）を注入して迷惑メール中継等ができないか試す
3. メールヘッダインジェクション（件名/宛先の改ざん・追加）が成立するか確認
4. 成立時は迷惑メール踏み台・情報漏えいリスクとして finding に

## 使用ツール

- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 改行（CR/LF）が除去・拒否され、ヘッダを追加できない。
- **fail**: 件名・宛先欄に改行を入れてヘッダ追加や第三者中継ができる。
- 補足: 問い合わせフォームが典型。スパム踏み台化の観点でも重大。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/10-Testing_for_IMAP_SMTP_Injection
