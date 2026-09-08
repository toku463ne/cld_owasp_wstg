# WSTG-CRYP-04 — Testing for Weak Encryption

## 目的

使用している暗号アルゴリズム・鍵・乱数が十分な強度かを確認する。

WSTG の Test Objectives:

- Provide a guideline for the identification weak encryption or hashing uses and implementations.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Basic Security Checklist** — When using AES128 or AES256, the IV (Initialization Vector) must be random and unpredictable
2. **Source Code Review** — Search for the following keywords to identify use of weak algorithms: MD4, MD5, RC4, RC2, DES, Blowfish, SHA-1, ECB

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
