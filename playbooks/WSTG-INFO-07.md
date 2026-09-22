# WSTG-INFO-07 — Map Execution Paths Through Application

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

アプリ内の実行経路（画面遷移・状態遷移）を地図にし、未検査の領域を残さないようにする。

WSTG の Test Objectives:

- Map the target application and understand the principal workflows.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 認証済みアカウントでアプリの全機能を手動で歩き（walkthrough）、画面遷移・状態遷移を記録
2. Burp の Target→Site map と Content discovery、または ZAP Spider で自動クロールを併用
3. 多段フォーム・ウィザード・JS 遷移など自動クロールが追えない経路を手動で補完
4. 業務フロー図（正常系・分岐・キャンセル/戻る）を artifacts に描き、未検査領域を明示

## 使用ツール

- Burp Suite
- OWASP ZAP

## 判定基準（pass / fail の見分け）

- **pass**: 主要な業務フローと分岐が把握でき、テスト対象の網羅率を説明できる。
- **fail**: クロールから漏れる隠し機能・直リンクでしか到達できない画面が見つかり、そこに保護がない。
- 補足: 自動クロールだけでは多段フォームや JS 遷移を追えない。手動walkthroughと併用する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/entry-points.txt`, `artifacts/sitemap.xml`, `notes.md`
- `covers:` — `{id: WSTG-INFO-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/07-Map_Execution_Paths_Through_Application
