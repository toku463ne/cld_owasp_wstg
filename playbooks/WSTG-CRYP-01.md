# WSTG-CRYP-01 — Testing for Weak Transport Layer Security

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

TLS の構成（プロトコル・暗号スイート・証明書）が現行水準を満たすかを確認する。

WSTG の Test Objectives:

- Validate the service configuration.
- Review the digital certificate's cryptographic strength and validity.
- Ensure that the TLS security is not bypassable and is properly implemented across the application.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. 全 TLS ポートを testssl（`testssl ${https_proxy:+--proxy=auto} --logfile evidence/<活動フォルダ>/artifacts/testssl.log https://target`）か sslyze（`sslyze ${https_proxy:+--https_tunnel="$https_proxy"} --json_out evidence/<活動フォルダ>/artifacts/sslyze.json target:443 || [ $? -eq 1 ]`）で一括検査する
   > ⚠️ **負荷注意（手順1）**: testssl / sslyze は多数の TLS ハンドシェイクを張る。低スペックな終端やロードバランサに負荷がかかることがある。
2. SSLv3/TLS1.0/1.1・弱い暗号スイート（RC4/3DES/EXPORT）・弱い鍵長が有効でないか確認
3. 証明書の有効期限・発行者・ホスト名一致、既知脆弱性（Heartbleed/ROBOT 等）を確認
4. TLS のバージョンごとの受理/拒否を curl で裏取りする: `for v in 1.0 1.1 1.2 1.3; do curl -sk -o /dev/null -m 10 --tlsv$v --tls-max $v --ciphers 'DEFAULT@SECLEVEL=0' https://target/; rc=$?; case $rc in 0) echo "TLS$v: 受理";; 35) echo "TLS$v: 拒否（ハンドシェイク失敗 curl=35）";; *) echo "TLS$v: 不明（curl=$rc）";; esac; done | tee evidence/<活動フォルダ>/artifacts/tls-versions.txt; grep -q '受理' evidence/<活動フォルダ>/artifacts/tls-versions.txt || { echo "どの TLS バージョンでも接続できない＝対象に届いていない。プロキシ配下なら https_proxy が設定されているか確認する（curl -sI https://target/ で疎通確認）" >&2; exit 3; }`。TLS1.0/1.1 が「受理」なら fail 材料

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順1**: testssl / sslyze は多数の TLS ハンドシェイクを張る。低スペックな終端やロードバランサに負荷がかかることがある。

## 使用ツール

- testssl.sh
- sslyze
- curl

## 判定基準（pass / fail の見分け）

- **pass**: TLS1.2/1.3 のみ、弱い暗号スイートなし、証明書が有効で信頼チェーンが正しい。
- **fail**: SSLv3/TLS1.0/1.1 が有効、RC4/3DES/NULL/EXPORT が有効、証明書が期限切れ・自己署名・名前不一致。
- 補足: 対象は Web だけでなく、メール・API・管理ポートの TLS も含める。手順1: sslyze v5 は引数なしで標準スキャン（`--regular` は廃止）。Mozilla intermediate に不適合だと exit 1 を返すが判定材料なので成功扱い（理由は出力末尾の COMPLIANCE 節）。プロキシ経由では testssl は `--proxy=auto`、sslyze は `--https_tunnel`。Kali の apt 版のコマンド名は testssl（git 版しか無ければ `sudo ln -s "$(command -v testssl.sh)" /usr/local/bin/testssl`）。手順4 の「拒否」は手元の OpenSSL が古い版を無効にしている場合もあるので testssl/sslyze を正とする。社内プロキシが TLS インスペクションをしていると結果はプロキシの TLS になるので、証明書の発行者で確かめる。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `cmd/testssl.txt`, `artifacts/tls-summary.md`
- `covers:` — `{id: WSTG-CRYP-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `tls-scan` — TLS 設定スキャン

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/09-Testing_for_Weak_Cryptography/01-Testing_for_Weak_Transport_Layer_Security
