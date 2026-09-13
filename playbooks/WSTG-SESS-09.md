# WSTG-SESS-09 — Testing for Session Hijacking

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

取得したトークンが別環境から再利用できないか（ハイジャック成立性）を確認する。

WSTG の Test Objectives:

- Identify vulnerable session cookies.
- Hijack vulnerable cookies and assess the risk level.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 有効なセッション ID を別ブラウザ/別 IP にコピーし、同時に使えるか（バインドがないか）確認
2. セッションが IP/User-Agent 等の属性に紐づくか、盗んだ ID だけで Burp で成り済ませるか検証
3. XSS/ネットワーク傍受でトークンを取れた場合の悪用可否を、取得済みトークンで確認
4. 同時多重ログインの検知・失効の有無を確認

## 使用ツール

- ブラウザ
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: トークンが盗まれても、再利用時に追加検証（再認証・端末束縛）や短寿命で被害が限定される。
- **fail**: 別 IP・別ブラウザで同じトークンをそのまま使い、完全に成りすませる。
- 補足: 検証は自分のアカウント間で行う。他人のセッションは決して使わない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`, `artifacts/session-trace.burp`, `artifacts/token-samples.txt`, `notes.md`
- `covers:` — `{id: WSTG-SESS-09, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）
- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/09-Testing_for_Session_Hijacking
