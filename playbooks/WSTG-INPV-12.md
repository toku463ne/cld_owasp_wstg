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

1. When viewing a file in a web application, the filename is often shown in the URL. Perl allows piping data from a process into an open statement.
2. Example URL before alteration:
3. http://sensitive/cgi-bin/userData.pl?doc=user1.txt
4. http://sensitive/cgi-bin/userData.pl?doc=/bin/ls|
5. This will execute the command /bin/ls.
6. Appending a semicolon to the end of a URL for a .PHP page followed by an operating system command, will execute the command. %3B is URL encoded and decodes to semicolon
7. http://sensitive/something.php?dir=%3Bcat%20/etc/passwd

## 使用ツール

- OWASP WebGoat
- Commix

## 判定基準（pass / fail の見分け）

- **pass**: シェルを介さない実行、または引数のホワイトリスト検証がされている。
- **fail**: ; | && $() 等でコマンドを連結・実行できる（時間差やアウトオブバンドで確認）。
- 補足: 破壊的コマンドは絶対に使わない。id・sleep など無害なもので証明する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-INPV-12, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/07-Input_Validation_Testing/12-Testing_for_Command_Injection
