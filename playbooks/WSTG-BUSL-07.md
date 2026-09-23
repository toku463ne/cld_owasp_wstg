# WSTG-BUSL-07 — Test Defenses Against Application Misuse

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

想定外の使い方をされたときにアプリが検知・防御するかを確認する。

WSTG の Test Objectives:

- Generate notes from all tests conducted against the system.
- Review which tests had a different functionality based on aggressive input.
- Understand the defenses in place and verify if they are enough to protect the system against bypassing techniques.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 異常な使い方（高速連打・想定外の順序・大量リクエスト）を Burp Intruder で行い、検知/抑止する仕組みがあるか確認
   > ⚠️ **負荷注意（手順1）**: 高速連打・大量リクエストは事実上の負荷試験になる。検知/抑止の確認が目的なので、対象が耐えられる範囲で段階的に。
2. 不正操作に対する監視・アラート・レート制限・アカウント制限の有無を確認
3. 自動化ツールでの操作をアプリが検知/妨害するか確認
4. 誤用に対する能動的防御が無い場合、悪用容易性として finding に

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: 高速連打・大量リクエストは事実上の負荷試験になる。検知/抑止の確認が目的なので、対象が耐えられる範囲で段階的に。

## 使用ツール

- Burp Intruder

## 判定基準（pass / fail の見分け）

- **pass**: 異常な利用（大量リクエスト・不正パラメータ連発）を検知し、記録・遮断・通知が行われる。
- **fail**: 明らかな攻撃パターンを繰り返しても検知も抑止もされない。
- 補足: 検知の有無は顧客側のログ確認が必要。ヒアリング結果も evidence に残す。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/logic-scenarios.md`, `notes.md`
- `covers:` — `{id: WSTG-BUSL-07, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `business-logic-walkthrough` — 業務ロジックの通し検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/10-Business_Logic_Testing/07-Test_Defenses_Against_Application_Misuse
