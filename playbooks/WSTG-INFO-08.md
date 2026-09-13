# WSTG-INFO-08 — Fingerprint Web Application Framework

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

アプリのフレームワーク・CMS・ライブラリとそのバージョンを特定する。

WSTG の Test Objectives:

- Fingerprint the components being used by the web applications.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `whatweb https://target/` と ブラウザ拡張 Wappalyzer でフレームワーク/CMS を推定
2. Cookie 名（`JSESSIONID`/`ASP.NET_SessionId`/`laravel_session` 等）・URL パス・ヘッダから基盤を特定
3. フロント JS を `retire --js` / Retire.js で走査し、jQuery 等ライブラリのバージョンと既知脆弱性を確認
4. 特定した製品・バージョンを CVE と照合し、finding にバージョン根拠（どこで判ったか）を添える

## 使用ツール

- Website: https://github.com/urbanadventurer/WhatWeb
- Text strings (case sensitive)
- Regular expressions
- Google Hack Database queries (limited set of keywords)
- MD5 hashes
- URL recognition
- HTML tag patterns
- Custom ruby code for passive and aggressive operations

## 判定基準（pass / fail の見分け）

- **pass**: 使用フレームワークが特定できない、または特定できても既知脆弱性のないバージョン。
- **fail**: 既知脆弱性のあるバージョンのフレームワーク・ライブラリを使用している（Cookie 名・パス・ヘッダ・JS から特定）。
- 補足: フロント側のライブラリ（jQuery 等）は Retire.js で確認できる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- `covers:` — `{id: WSTG-INFO-08, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/08-Fingerprint_Web_Application_Framework
