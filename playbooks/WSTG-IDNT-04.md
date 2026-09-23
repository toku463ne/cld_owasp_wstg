# WSTG-IDNT-04 — Testing for Account Enumeration and Guessable User Account

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

ログイン・登録・リセットの応答差から、有効なユーザ名を推測できないかを確認する。

WSTG の Test Objectives:

- Review processes that pertain to user identification (e.g. registration, login, etc.).
- Enumerate users where possible through response analysis.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ログイン失敗メッセージの差（「該当ユーザなし」vs「パスワード誤り」）を Burp Repeater で比較
2. パスワードリセット・登録・ログインの各画面で、存在/非存在ユーザの応答差・応答時間差を確認
3. 存在するユーザ名の列挙が可能か（連番 ID・メール総当り）を少量で検証
   > ⚠️ **負荷注意（手順3）**: ユーザ名列挙の総当りは大量リクエストに加えロックの恐れがある。手順の「少量で」を厳守し、挙動確認に留める。
4. 差分が出る箇所を全て挙げ、応答本文・ステータス・時間のどれで判別できるか finding に記す

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順3**: ユーザ名列挙の総当りは大量リクエストに加えロックの恐れがある。手順の「少量で」を厳守し、挙動確認に留める。

## 使用ツール

- Burp Repeater

## 判定基準（pass / fail の見分け）

- **pass**: 存在するユーザと存在しないユーザで、メッセージ・ステータス・応答時間に有意差がない。
- **fail**: 「パスワードが違います」「該当ユーザなし」等でユーザの存在が判別できる、または応答時間に差がある。
- 補足: 応答時間差はハッシュ計算の有無で出やすい。数十回計測して平均で比較する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/enum-responses.txt`, `artifacts/response-diff.md`
- `covers:` — `{id: WSTG-IDNT-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `account-enum-probe` — アカウント列挙とロックアウトの検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/03-Identity_Management_Testing/04-Testing_for_Account_Enumeration_and_Guessable_User_Account
