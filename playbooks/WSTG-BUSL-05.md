# WSTG-BUSL-05 — Test Number of Times a Function Can Be Used Limits

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

回数制限のある機能が実際に制限されているかを確認する。

WSTG の Test Objectives:

- Identify functions that must set limits to the times they can be called.
- Assess if there is a logical limit set on the functions and if it is properly validated.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 回数制限があるべき機能（クーポン適用・投票・出金・OTP 試行）を Burp Intruder で連続実行し、上限を超えられるか確認
   > ⚠️ **負荷注意（手順1）**: 回数制限の検証は意図的な連続実行。出金・OTP など実処理を伴う機能では実際に副作用が起きる。テストデータ・テストアカウントで行う。
2. 並行リクエスト（レースコンディション）で、1回制限を複数回すり抜けられないか試す
3. サーバ側でカウント/ロックしているか、クライアント側制御だけでないか確認
4. 上限超過・二重処理ができた場合、業務影響とともに finding に

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: 回数制限の検証は意図的な連続実行。出金・OTP など実処理を伴う機能では実際に副作用が起きる。テストデータ・テストアカウントで行う。

## 使用ツール

- Burp Intruder

## 判定基準（pass / fail の見分け）

- **pass**: 上限回数がサーバ側で管理され、超過すると拒否される。
- **fail**: クーポン・投票・試行などが無制限に繰り返せる。
- 補足: セッションを変える・並行実行するなど、制限の抜け道も試す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/05-Test_Number_of_Times_a_Function_Can_Be_Used_Limits
