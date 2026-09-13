# WSTG-INFO-01 — Conduct Search Engine Discovery Reconnaissance for Information Leakage

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

検索エンジンや公開アーカイブに、対象組織が意図せず晒した情報が残っていないかを確認する。

WSTG の Test Objectives:

- Identify what sensitive design and configuration information of the application, system, or organization is exposed directly (on the organization's website) or indirectly (via third-party services).

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. `whois target.co.jp` で組織名・登録者・ネームサーバを確認し、名寄せの起点にする
2. `theHarvester -d target.co.jp -b duckduckgo,crtsh,otx,hackertarget -f evidence` で露出メール・サブドメイン・ホストを収集（-f で結果も保存。`-b all` で全ソース）
3. crt.sh（`https://crt.sh/?q=%25.target.co.jp`）と `amass enum -passive -d target.co.jp` で公開・失念サブドメインを列挙
4. Google/Bing で dork を回す: `site:target.co.jp ext:xls OR ext:pdf OR ext:conf`・`intitle:index.of`・`inurl:admin`・`"error"|"exception"`。Wayback Machine（web.archive.org）で消えた旧版も確認
5. ヒットした URL・スニペットを artifacts/dorking-hits.md に記録し、機微情報を含む行に [creds]/[internal] 等のタグを付ける

## 使用ツール

- whois
- theHarvester
- crt.sh
- amass
- Google/Bing dorking
- Wayback Machine

## 判定基準（pass / fail の見分け）

- **pass**: 検索結果に機微情報（資格情報・内部URL・設定ファイル・個人情報）が出てこない。
- **fail**: dork でヒットした結果に、内部ホスト名・エラーメッセージ・認証情報・非公開ドキュメントが含まれる。
- 補足: キャッシュにしか残っていない場合も指摘対象。削除依頼（Search Console 等）まで助言する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/subdomains.txt`, `artifacts/dorking-hits.md`, `cmd/whois.txt`
- `covers:` — `{id: WSTG-INFO-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `recon-osint` — 外部 OSINT・公開情報の収集

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/01-Information_Gathering/01-Conduct_Search_Engine_Discovery_Reconnaissance_for_Information_Leakage
