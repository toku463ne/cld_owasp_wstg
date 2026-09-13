# WSTG-INFO-02 — Fingerprint Web Server

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

Web サーバの種類とバージョンがどこまで外部から判別できるかを確認する。

WSTG の Test Objectives:

- Determine the version and type of a running web server to enable further discovery of any known vulnerabilities.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `curl -sI https://target/` で Server / X-Powered-By / Via ヘッダを確認
2. `nmap -sV -p80,443 target` と `whatweb https://target/` で製品名・バージョンを突き合わせる
3. 存在しないパス（`curl -s https://target/nope123`）を叩き、404 ページの体裁からも製品を推定
4. 特定できたバージョンを CVE（NVD 等）と照合し、既知脆弱性の有無を finding に書く

## 使用ツール

- nmap -sV
- whatweb
- Wappalyzer
- httpx

## 判定基準（pass / fail の見分け）

- **pass**: バナー・ヘッダ・エラーページから製品名とバージョンが特定できない、または既知脆弱性のないバージョン。
- **fail**: Server ヘッダ等でバージョンまで特定でき、そのバージョンに既知の脆弱性がある。
- 補足: バージョン秘匿だけでは対策にならない。パッチ状況とセットで報告する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-02, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server
