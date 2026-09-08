# WSTG-INPV-10 — Testing for IMAP SMTP Injection

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

1. **Identifying Vulnerable Parameters** — In order to detect vulnerable parameters, the tester has to analyze the application's ability in handling input
2. **Understanding the Data Flow and Deployment Structure of the Client** — After identifying all vulnerable parameters (for example, passed_id), the tester needs to determine what level of injection is possible and …
3. **IMAP/SMTP Command Injection** — Once the tester has identified vulnerable parameters and has analyzed the context in which they are executed, the next stage is exploiting t …

## 使用ツール

- Burp Intruder
- sqlmap
- tplmap
- 手動 payload

## 判定基準（pass / fail の見分け）

- **pass**: 改行（CR/LF）が除去・拒否され、ヘッダを追加できない。
- **fail**: 件名・宛先欄に改行を入れてヘッダ追加や第三者中継ができる。
- 補足: 問い合わせフォームが典型。スパム踏み台化の観点でも重大。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-10, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/10-Testing_for_IMAP_SMTP_Injection
