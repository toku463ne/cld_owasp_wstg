# WSTG-SESS-01 — Testing for Session Management Schema

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

セッション管理方式（トークンの生成・保管・検証）が健全かを確認する。

WSTG の Test Objectives:

- Gather session tokens, for the same user and for different users where possible.
- Analyze and ensure that enough randomness exists to stop session forging attacks.
- Modify cookies that are not signed and contain information that can be manipulated.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. ログインで発行されるセッション ID を Burp で捕捉し、長さ・文字種・予測可能性を確認
2. Burp Sequencer で多数のトークンを収集し、ランダム性（エントロピー）を測定
   > ⚠️ **負荷注意（手順2）**: Burp Sequencer は統計に足る数（数千〜）のトークンを集めるため、大量のセッション発行リクエストを送る。セッションテーブルやログを圧迫しうる。
3. セッション ID が URL に載る・JS から読める・複数同時ログインを許すか確認
4. ログイン/権限変更時に ID が再発行されるか（固定でないか）確認。サンプルは artifacts に保存

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順2**: Burp Sequencer は統計に足る数（数千〜）のトークンを集めるため、大量のセッション発行リクエストを送る。セッションテーブルやログを圧迫しうる。

## 使用ツール

- Burp Sequencer

## 判定基準（pass / fail の見分け）

- **pass**: トークンが十分ランダムで予測不能、サーバ側で失効管理され、識別子として推測できない。
- **fail**: トークンが連番・時刻由来・ユーザ情報のエンコードなどで予測可能、または改ざん検知がない。
- 補足: Burp Sequencer 等でランダム性を測り、サンプルは artifacts に保存する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/session-trace.burp`, `artifacts/token-samples.txt`, `notes.md`
- `covers:` — `{id: WSTG-SESS-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `session-capture` — セッション取得とログイン/ログアウト解析

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/06-Session_Management_Testing/01-Testing_for_Session_Management_Schema
