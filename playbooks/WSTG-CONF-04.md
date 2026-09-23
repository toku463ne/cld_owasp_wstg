# WSTG-CONF-04 — Review Old Backup and Unreferenced Files for Sensitive Information

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

公開ディレクトリに残った旧版・バックアップ・未参照ファイルを探す。

WSTG の Test Objectives:

- Find and analyse unreferenced files that might contain sensitive information.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `ffuf -w wordlist -u https://target/FUZZ -e .bak,.old,.zip,.tar.gz,.swp,~ -o evidence/<活動フォルダ>/artifacts/ffuf-backup.json -of json` で旧版/バックアップを総当り
   > ⚠️ **負荷注意（手順1）**: ffuf のバックアップ総当りは大量リクエスト。`-rate` でレートを制限し、ワードリストを対象に合わせて絞る。
2. 既知ファイルの残骸を狙って取得: `for f in login.php.bak .login.php.swp index.php~ config.php.bak .env.bak web.config.old; do echo "$f -> $(curl -s -o /dev/null -w '%{http_code}' https://target/$f)"; done | tee evidence/<活動フォルダ>/artifacts/backup-residue.txt`。200 で中身が返るものは取得して evidence に、要約のみ finding に
3. リポジトリメタデータ `curl -s https://target/.git/config` `/.svn/entries` を確認（取れたら重大）
4. `.git/` が取れる場合は git-dumper 等で復元可否を検証し、重大度・影響範囲を finding に明記

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: ffuf のバックアップ総当りは大量リクエスト。`-rate` でレートを制限し、ワードリストを対象に合わせて絞る。

## 使用ツール

- ffuf
- curl
- git-dumper

## 判定基準（pass / fail の見分け）

- **pass**: 総当たりでバックアップ・旧版・エディタの一時ファイルが見つからない。
- **fail**: .bak/.old/~/.swp/.zip、リポジトリメタデータ（.git/、.svn/）等が取得できる。
- 補足: .git/config が取れたらリポジトリ全体を復元できる可能性がある。重大度は高く扱う。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/ffuf-backup.txt`, `artifacts/found-files.md`
- `covers:` — `{id: WSTG-CONF-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `backup-unref` — 旧・バックアップ・未参照ファイルの探索

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/02-Configuration_and_Deployment_Management_Testing/04-Review_Old_Backup_and_Unreferenced_Files_for_Sensitive_Information
