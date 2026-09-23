# WSTG-CONF-05 — Enumerate Infrastructure and Application Admin Interfaces

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

管理インタフェース（インフラ・アプリ両方）の露出と保護状況を確認する。

WSTG の Test Objectives:

- Identify hidden administrator interfaces and functionality.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `ffuf -w admin-wordlist ${https_proxy:+-x "$https_proxy"} -u https://target/FUZZ -o evidence/<活動フォルダ>/artifacts/ffuf-admin.json -of json`（`/admin /manager /wp-admin /phpmyadmin` 等）で管理画面を探索（ffuf は環境変数のプロキシを見ないので、プロキシ経由で対象に出る環境では `-x` を明示する）
   > ⚠️ **負荷注意（手順1）**: ffuf の管理画面総当りは大量リクエスト。ログイン系パスを叩くとアカウントロックや誤検知アラートを誘発しうる。`-rate` で抑え、ログインを含むパスは慎重に。
2. インフラ側の管理ポートも確認: `nmap -Pn -sV -p8080,8443,9990,10000,7001,8161,9000,9090 -oN evidence/<活動フォルダ>/artifacts/nmap-mgmt.txt target`。open のポートの製品・バージョンを控え、管理コンソールなら手順3の認証確認へ
   > ⚠️ **負荷注意（手順2）**: `nmap` の管理ポート走査。応答の無い機器へ繰り返すと接続数を圧迫しうる。
3. 見つけた管理画面の認証（既定資格情報・接続元制限・MFA）を確認。既定資格情報は必ず試す
4. 「パスを秘匿しているだけ」で列挙で出てくる状態は保護不十分として扱う

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: ffuf の管理画面総当りは大量リクエスト。ログイン系パスを叩くとアカウントロックや誤検知アラートを誘発しうる。`-rate` で抑え、ログインを含むパスは慎重に。
- **手順2**: `nmap` の管理ポート走査。応答の無い機器へ繰り返すと接続数を圧迫しうる。

## 使用ツール

- ffuf
- nmap

## 判定基準（pass / fail の見分け）

- **pass**: 管理画面が外部から到達できない、または接続元制限＋強い認証（MFA 等）で保護されている。
- **fail**: 管理画面が公開ネットワークから到達でき、既定パス・既定資格情報・弱い認証で入れる。
- 補足: パスを秘匿しているだけの状態は fail 寄り。列挙で見つかる時点で保護になっていない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/entry-points.txt`, `artifacts/sitemap.xml`, `notes.md`, `cmd/curl-robots.txt`, `cmd/curl-wellknown.txt`
- `covers:` — `{id: WSTG-CONF-05, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し
- `metafiles-crawl` — メタファイル・公開コンテンツの収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/05-Enumerate_Infrastructure_and_Application_Admin_Interfaces
