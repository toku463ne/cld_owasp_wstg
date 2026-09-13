# WSTG-CRYP-04 — Testing for Weak Encryption

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

使用している暗号アルゴリズム・鍵・乱数が十分な強度かを確認する。

WSTG の Test Objectives:

- Provide a guideline for the identification weak encryption or hashing uses and implementations.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 保存/送信データの暗号化方式（弱い ECB、独自暗号、可逆エンコードを暗号と誤認）を確認
2. パスワード保存が平文/MD5/SHA1 等の弱いハッシュ（ソルト無し）でないか、判る範囲で確認
3. ハードコードされた鍵・IV 使い回し・予測可能な乱数が使われていないか確認
4. 暗号化と単なるエンコード（base64）の混同を見抜き、実質無防備な箇所を finding に

## 使用ツール

- padbuster
- testssl.sh
- Burp Suite
- 手動レビュー

## 判定基準（pass / fail の見分け）

- **pass**: 現行標準（AES-GCM 等）・十分な鍵長・安全な乱数源が使われ、パスワードは適切な KDF で保存される。
- **fail**: MD5/SHA1 でのパスワード保存、ECB モード、ハードコードされた鍵、予測可能な乱数を使用。
- 補足: 外部からは判定しにくい。ソース・設計書のレビューまたはヒアリングとセットで行う。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/crypto-review.md`, `cmd/padbuster.txt`
- `covers:` — `{id: WSTG-CRYP-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `crypto-review` — 暗号利用のレビュー（パディングオラクル・弱い暗号・平文送出）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/04-Testing_for_Weak_Encryption
