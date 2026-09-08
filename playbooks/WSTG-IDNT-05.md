# WSTG-IDNT-05 — Testing for Weak or Unenforced Username Policy

## 目的

ユーザ名のポリシーが推測を助長していないかを確認する。

WSTG の Test Objectives:

- Determine whether a consistent account name structure renders the application vulnerable to account enumeration.
- Determine whether the application's error messages permit account enumeration.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. Determine the structure of account names.
2. Evaluate the application's response to valid and invalid account names.
3. Use different responses to valid and invalid account names to enumerate valid account names.
4. Use account name dictionaries to enumerate valid account names.

## 使用ツール

- 手動レビュー
- ヒアリング
- Burp Suite
- Burp Intruder
- ffuf
- curl

## 判定基準（pass / fail の見分け）

- **pass**: ユーザ名が推測しにくい、または推測できても他の対策（MFA・ロックアウト）で守られている。
- **fail**: 社員番号やメールの規則的な組み合わせで有効アカウントを大量に作れる、かつ列挙も可能。
- 補足: IDNT-04 とセットで報告すると影響が伝わりやすい。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/role-matrix.md`, `notes.md`, `cmd/enum-responses.txt`, `artifacts/response-diff.md`
- `covers:` — `{id: WSTG-IDNT-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー
- `account-enum-probe` — アカウント列挙とロックアウトの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/05-Testing_for_Weak_or_Unenforced_Username_Policy
