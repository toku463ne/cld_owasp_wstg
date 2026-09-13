# WSTG-ATHN-03 — Testing for Weak Lock Out Mechanism

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

総当たり攻撃に対するロックアウト等の抑止が機能しているかを確認する。

WSTG の Test Objectives:

- Evaluate the account lockout mechanism's ability to mitigate brute force password guessing.
- Evaluate the unlock mechanism's resistance to unauthorized account unlocking.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 同一アカウントに誤ったパスワードで連続ログインし、ロックされる閾値を確認（少数から）
2. ロック後の解除方法（時間経過・管理者解除）と、ロック中の応答差を確認
3. ロックがユーザ名基準か IP 基準か、API/別チャネルで回避できないか確認
4. ロックアウトがないか極端に緩い場合は総当りリスクとして finding に。DoS を招く強すぎる設定も併記

## 使用ツール

- Burp Intruder
- ffuf
- curl

## 判定基準（pass / fail の見分け）

- **pass**: 一定回数の失敗でロックまたは段階的遅延・CAPTCHA が働き、自動化が現実的でない。
- **fail**: 失敗回数に制限がなく、高速な総当たりが可能。
- 補足: ロックアウトは DoS にもなる。解除条件（時間経過か管理者解除か）まで記録する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `cmd/enum-responses.txt`, `artifacts/response-diff.md`
- `covers:` — `{id: WSTG-ATHN-03, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `account-enum-probe` — アカウント列挙とロックアウトの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/04-Authentication_Testing/03-Testing_for_Weak_Lock_Out_Mechanism
