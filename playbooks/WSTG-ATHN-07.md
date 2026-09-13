# WSTG-ATHN-07 — Testing for Weak Password Policy

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

パスワードポリシーが十分な強度を要求しているかを確認する。

WSTG の Test Objectives:

- Determine the resistance of the application against brute force password guessing using available password dictionaries by evaluating the length, complexity, reuse, and aging requirements of passwords.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. パスワード変更/登録で短い・単純な値（`1234`・`password`・辞書語）が通るか Burp Repeater で試す
2. 最小長・文字種・使い回し/過去パスワード禁止・よくあるパスワード拒否の有無を確認
3. 最大長制限が短すぎ（例: 16 未満）でパスフレーズが使えないか確認
4. 強度要件を満たさない値が実際に登録できた場合は finding に（画面表記でなく実挙動で判定）

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: 最低長（12文字以上が目安）と使い回し・既知漏えいパスワードの抑止があり、上限が極端に短くない。
- **fail**: 4〜6文字や辞書語が通る、最大長が短すぎる、文字種強制のみで長さを要求していない。
- 補足: 現行 NIST SP 800-63B は「長さ重視・複雑さ強制は不要・漏えいリスト照合」を推奨。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- `covers:` — `{id: WSTG-ATHN-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authn-flow-review` — 認証フロー一括レビュー

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/07-Testing_for_Weak_Password_Policy
