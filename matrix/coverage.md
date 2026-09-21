# カバレッジマトリクス（アクティビティ × WSTG）

> 自動生成: `uv run scripts/build_coverage.py`（元データは `matrix/coverage.yaml` の `activities:`）

- アクティビティ数: **31**
- WSTG 実施対象: **94** 件（v4.2 全 97 件 − 統合済み 3 件）
- primary でカバー済み: **94** 件

`primary` はそのアクティビティ単独で判定まで到達できるもの、`secondary` は入力・補強にとどまるもの。

## 1. アクティビティ → WSTG-ID

| activity_id | 概要 | 主なツール | primary | secondary |
|---|---|---|---|---|
| `recon-osint` | 外部 OSINT・公開情報の収集 | theHarvester, crt.sh, whois, Google/Bing dorking, subfinder | WSTG-INFO-01 | WSTG-CONF-10 |
| `fingerprint-stack` | サーバ・フレームワークのフィンガープリント | nmap -sV, whatweb, Wappalyzer, httpx | WSTG-INFO-02, WSTG-INFO-08 | WSTG-CONF-01, WSTG-CONF-02 |
| `tls-scan` | TLS 設定スキャン | testssl.sh, sslyze, nmap --script ssl-enum-ciphers | WSTG-CRYP-01, WSTG-CONF-07 | WSTG-CONF-01 |
| `http-methods` | HTTP メソッドの列挙と検証 | curl, nmap http-methods NSE, ncat, Burp Repeater | WSTG-CONF-06 | WSTG-INPV-03 |
| `headers-review` | レスポンスヘッダ一括精査（匿名 + 認証済み） | curl, Burp Suite, securityheaders.io 相当の手動チェック | WSTG-SESS-02, WSTG-CONF-07, WSTG-CLNT-09, WSTG-ATHN-06, WSTG-CLNT-07 | WSTG-CRYP-03 |
| `metafiles-crawl` | メタファイル・公開コンテンツの収集 | curl, wget, grep/ripgrep, Burp Suite | WSTG-INFO-03, WSTG-INFO-05 | WSTG-CONF-05 |
| `enum-apps` | 仮想ホスト・パスの列挙 | ffuf, dirsearch, gobuster, nmap -p- | WSTG-INFO-04 | WSTG-INFO-06 |
| `burp-crawl-authn` | 認証済みクロールとエントリポイント洗い出し | Burp Suite, OWASP ZAP | WSTG-INFO-06, WSTG-INFO-07, WSTG-INFO-10, WSTG-CONF-05 | — |
| `session-capture` | セッション取得とログイン/ログアウト解析 | Burp Suite, Burp Sequencer, curl | WSTG-SESS-01, WSTG-SESS-02, WSTG-SESS-03, WSTG-SESS-06, WSTG-SESS-07 | WSTG-SESS-09 |
| `backup-unref` | 旧・バックアップ・未参照ファイルの探索 | ffuf, dirsearch, nikto | WSTG-CONF-03, WSTG-CONF-04 | — |
| `server-config-review` | サーバ／プラットフォーム構成レビュー | 手動レビュー, ls -l / icacls, nikto, CIS Benchmark チェックリスト | WSTG-CONF-01, WSTG-CONF-02, WSTG-CONF-09 | — |
| `cloud-and-takeover` | クラウドストレージ・サブドメイン乗っ取りの確認 | dig, curl, grep, aws cli | WSTG-CONF-11, WSTG-CONF-10 | — |
| `ria-legacy-check` | RIA クロスドメインポリシーとレガシー Flash の確認 | curl, 手動レビュー | WSTG-CONF-08, WSTG-CLNT-08 | — |
| `identity-model-review` | ロール定義・登録・払い出しプロセスのレビュー | 手動レビュー, ヒアリング, Burp Suite | WSTG-IDNT-01, WSTG-IDNT-02, WSTG-IDNT-03, WSTG-IDNT-05 | — |
| `account-enum-probe` | アカウント列挙とロックアウトの検証 | Burp Intruder, ffuf, curl | WSTG-IDNT-04, WSTG-ATHN-03 | WSTG-IDNT-05 |
| `authn-flow-review` | 認証フロー一括レビュー | Burp Suite, curl, ブラウザ開発者ツール | WSTG-ATHN-01, WSTG-ATHN-02, WSTG-ATHN-04, WSTG-ATHN-05, WSTG-ATHN-07, WSTG-ATHN-10, WSTG-CRYP-03 | WSTG-ATHN-06 |
| `password-reset-review` | パスワード変更・リセット機能のレビュー | Burp Suite, メールクライアント, 手動レビュー | WSTG-ATHN-08, WSTG-ATHN-09 | — |
| `authz-matrix` | 権限マトリクス試験（ロール横断リクエスト再送） | Burp Suite, Autorize / AuthMatrix, curl | WSTG-ATHZ-02, WSTG-ATHZ-03, WSTG-ATHZ-04 | WSTG-SESS-08 |
| `traversal-probe` | ディレクトリトラバーサル・ファイルインクルードの検証 | Burp Suite, ffuf, 手動 payload | WSTG-ATHZ-01 | WSTG-CONF-03 |
| `session-abuse-tests` | セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック） | Burp Suite, curl, ブラウザ2枚 | WSTG-SESS-04, WSTG-SESS-05, WSTG-SESS-08, WSTG-SESS-09 | — |
| `xss-probe` | XSS・HTML インジェクションの検証 | Burp Suite, DOM Invader, 手動 payload | WSTG-INPV-01, WSTG-INPV-02, WSTG-CLNT-01, WSTG-CLNT-03 | — |
| `clientside-js-review` | クライアントサイド JS のシンク・ストレージレビュー | ブラウザ開発者ツール, DOM Invader, Retire.js, Burp Suite | WSTG-CLNT-02, WSTG-CLNT-04, WSTG-CLNT-05, WSTG-CLNT-06, WSTG-CLNT-11, WSTG-CLNT-12, WSTG-CLNT-13 | — |
| `cors-websocket-check` | CORS と WebSocket の検証 | curl, Burp Suite, wscat | WSTG-CLNT-07, WSTG-CLNT-10 | — |
| `injection-fuzz-server` | サーバサイド・インジェクション系の一括ファジング | Burp Intruder, sqlmap, tplmap, 手動 payload | WSTG-INPV-05, WSTG-INPV-06, WSTG-INPV-07, WSTG-INPV-08, WSTG-INPV-09, WSTG-INPV-10, WSTG-INPV-11, WSTG-INPV-12, WSTG-INPV-13, WSTG-INPV-18 | WSTG-ERRH-01 |
| `http-request-tamper` | HTTP リクエスト改変系の検証 | Burp Suite, Burp HTTP Request Smuggler, curl | WSTG-INPV-04, WSTG-INPV-15, WSTG-INPV-16, WSTG-INPV-17 | — |
| `ssrf-probe` | SSRF の検証 | Burp Collaborator, interactsh, curl | WSTG-INPV-19 | — |
| `error-handling-review` | エラーハンドリングのレビュー | Burp Suite, curl, 手動 | WSTG-ERRH-01 | WSTG-ERRH-02, WSTG-INFO-05 |
| `crypto-review` | 暗号利用のレビュー（パディングオラクル・弱い暗号・平文送出） | padbuster, testssl.sh, Burp Suite, 手動レビュー | WSTG-CRYP-02, WSTG-CRYP-03, WSTG-CRYP-04 | — |
| `business-logic-walkthrough` | 業務ロジックの通し検証 | Burp Suite, 手動操作, 業務仕様書 | WSTG-BUSL-01, WSTG-BUSL-02, WSTG-BUSL-03, WSTG-BUSL-04, WSTG-BUSL-05, WSTG-BUSL-06, WSTG-BUSL-07, WSTG-INPV-14 | — |
| `file-upload-tests` | ファイルアップロードの検証 | Burp Suite, EICAR テストファイル, 手動 | WSTG-BUSL-08, WSTG-BUSL-09 | WSTG-CONF-03 |
| `api-graphql-test` | API / GraphQL の検証 | Burp Suite, GraphQL Voyager, InQL, curl | WSTG-APIT-01 | WSTG-ATHZ-02 |

## 2. WSTG-ID → アクティビティ


### INFO — Information Gathering

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-INFO-01 | Conduct Search Engine Discovery Reconnaissance for Information Leakage | `recon-osint` | — |
| WSTG-INFO-02 | Fingerprint Web Server | `fingerprint-stack` | — |
| WSTG-INFO-03 | Review Webserver Metafiles for Information Leakage | `metafiles-crawl` | — |
| WSTG-INFO-04 | Enumerate Applications on Webserver | `enum-apps` | — |
| WSTG-INFO-05 | Review Webpage Content for Information Leakage | `metafiles-crawl` | `error-handling-review` |
| WSTG-INFO-06 | Identify Application Entry Points | `burp-crawl-authn` | `enum-apps` |
| WSTG-INFO-07 | Map Execution Paths Through Application | `burp-crawl-authn` | — |
| WSTG-INFO-08 | Fingerprint Web Application Framework | `fingerprint-stack` | — |
| WSTG-INFO-10 | Map Application Architecture | `burp-crawl-authn` | — |

### CONF — Configuration and Deployment Management

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-CONF-01 | Test Network Infrastructure Configuration | `server-config-review` | `fingerprint-stack`, `tls-scan` |
| WSTG-CONF-02 | Test Application Platform Configuration | `server-config-review` | `fingerprint-stack` |
| WSTG-CONF-03 | Test File Extensions Handling for Sensitive Information | `backup-unref` | `traversal-probe`, `file-upload-tests` |
| WSTG-CONF-04 | Review Old Backup and Unreferenced Files for Sensitive Information | `backup-unref` | — |
| WSTG-CONF-05 | Enumerate Infrastructure and Application Admin Interfaces | `burp-crawl-authn` | `metafiles-crawl` |
| WSTG-CONF-06 | Test HTTP Methods | `http-methods` | — |
| WSTG-CONF-07 | Test HTTP Strict Transport Security | `tls-scan`, `headers-review` | — |
| WSTG-CONF-08 | Test RIA Cross Domain Policy | `ria-legacy-check` | — |
| WSTG-CONF-09 | Test File Permission | `server-config-review` | — |
| WSTG-CONF-10 | Test for Subdomain Takeover | `cloud-and-takeover` | `recon-osint` |
| WSTG-CONF-11 | Test Cloud Storage | `cloud-and-takeover` | — |

### IDNT — Identity Management

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-IDNT-01 | Test Role Definitions | `identity-model-review` | — |
| WSTG-IDNT-02 | Test User Registration Process | `identity-model-review` | — |
| WSTG-IDNT-03 | Test Account Provisioning Process | `identity-model-review` | — |
| WSTG-IDNT-04 | Testing for Account Enumeration and Guessable User Account | `account-enum-probe` | — |
| WSTG-IDNT-05 | Testing for Weak or Unenforced Username Policy | `identity-model-review` | `account-enum-probe` |

### ATHN — Authentication

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-ATHN-01 | Testing for Credentials Transported over an Encrypted Channel | `authn-flow-review` | — |
| WSTG-ATHN-02 | Testing for Default Credentials | `authn-flow-review` | — |
| WSTG-ATHN-03 | Testing for Weak Lock Out Mechanism | `account-enum-probe` | — |
| WSTG-ATHN-04 | Testing for Bypassing Authentication Schema | `authn-flow-review` | — |
| WSTG-ATHN-05 | Testing for Vulnerable Remember Password | `authn-flow-review` | — |
| WSTG-ATHN-06 | Testing for Browser Cache Weaknesses | `headers-review` | `authn-flow-review` |
| WSTG-ATHN-07 | Testing for Weak Password Policy | `authn-flow-review` | — |
| WSTG-ATHN-08 | Testing for Weak Security Question Answer | `password-reset-review` | — |
| WSTG-ATHN-09 | Testing for Weak Password Change or Reset Functionalities | `password-reset-review` | — |
| WSTG-ATHN-10 | Testing for Weaker Authentication in Alternative Channel | `authn-flow-review` | — |

### ATHZ — Authorization

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-ATHZ-01 | Testing Directory Traversal File Include | `traversal-probe` | — |
| WSTG-ATHZ-02 | Testing for Bypassing Authorization Schema | `authz-matrix` | `api-graphql-test` |
| WSTG-ATHZ-03 | Testing for Privilege Escalation | `authz-matrix` | — |
| WSTG-ATHZ-04 | Testing for Insecure Direct Object References | `authz-matrix` | — |

### SESS — Session Management

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-SESS-01 | Testing for Session Management Schema | `session-capture` | — |
| WSTG-SESS-02 | Testing for Cookies Attributes | `headers-review`, `session-capture` | — |
| WSTG-SESS-03 | Testing for Session Fixation | `session-capture` | — |
| WSTG-SESS-04 | Testing for Exposed Session Variables | `session-abuse-tests` | — |
| WSTG-SESS-05 | Testing for Cross Site Request Forgery | `session-abuse-tests` | — |
| WSTG-SESS-06 | Testing for Logout Functionality | `session-capture` | — |
| WSTG-SESS-07 | Testing Session Timeout | `session-capture` | — |
| WSTG-SESS-08 | Testing for Session Puzzling | `session-abuse-tests` | `authz-matrix` |
| WSTG-SESS-09 | Testing for Session Hijacking | `session-abuse-tests` | `session-capture` |

### INPV — Input Validation

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-INPV-01 | Testing for Reflected Cross Site Scripting | `xss-probe` | — |
| WSTG-INPV-02 | Testing for Stored Cross Site Scripting | `xss-probe` | — |
| WSTG-INPV-04 | Testing for HTTP Parameter Pollution | `http-request-tamper` | — |
| WSTG-INPV-05 | Testing for SQL Injection | `injection-fuzz-server` | — |
| WSTG-INPV-06 | Testing for LDAP Injection | `injection-fuzz-server` | — |
| WSTG-INPV-07 | Testing for XML Injection | `injection-fuzz-server` | — |
| WSTG-INPV-08 | Testing for SSI Injection | `injection-fuzz-server` | — |
| WSTG-INPV-09 | Testing for XPath Injection | `injection-fuzz-server` | — |
| WSTG-INPV-10 | Testing for IMAP SMTP Injection | `injection-fuzz-server` | — |
| WSTG-INPV-11 | Testing for Code Injection | `injection-fuzz-server` | — |
| WSTG-INPV-12 | Testing for Command Injection | `injection-fuzz-server` | — |
| WSTG-INPV-13 | Testing for Format String Injection | `injection-fuzz-server` | — |
| WSTG-INPV-14 | Testing for Incubated Vulnerability | `business-logic-walkthrough` | — |
| WSTG-INPV-15 | Testing for HTTP Splitting Smuggling | `http-request-tamper` | — |
| WSTG-INPV-16 | Testing for HTTP Incoming Requests | `http-request-tamper` | — |
| WSTG-INPV-17 | Testing for Host Header Injection | `http-request-tamper` | — |
| WSTG-INPV-18 | Testing for Server-side Template Injection | `injection-fuzz-server` | — |
| WSTG-INPV-19 | Testing for Server-Side Request Forgery | `ssrf-probe` | — |

### ERRH — Error Handling

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-ERRH-01 | Testing for Improper Error Handling | `error-handling-review` | `injection-fuzz-server` |

### CRYP — Weak Cryptography

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-CRYP-01 | Testing for Weak Transport Layer Security | `tls-scan` | — |
| WSTG-CRYP-02 | Testing for Padding Oracle | `crypto-review` | — |
| WSTG-CRYP-03 | Testing for Sensitive Information Sent via Unencrypted Channels | `authn-flow-review`, `crypto-review` | `headers-review` |
| WSTG-CRYP-04 | Testing for Weak Encryption | `crypto-review` | — |

### BUSL — Business Logic

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-BUSL-01 | Test Business Logic Data Validation | `business-logic-walkthrough` | — |
| WSTG-BUSL-02 | Test Ability to Forge Requests | `business-logic-walkthrough` | — |
| WSTG-BUSL-03 | Test Integrity Checks | `business-logic-walkthrough` | — |
| WSTG-BUSL-04 | Test for Process Timing | `business-logic-walkthrough` | — |
| WSTG-BUSL-05 | Test Number of Times a Function Can Be Used Limits | `business-logic-walkthrough` | — |
| WSTG-BUSL-06 | Testing for the Circumvention of Work Flows | `business-logic-walkthrough` | — |
| WSTG-BUSL-07 | Test Defenses Against Application Misuse | `business-logic-walkthrough` | — |
| WSTG-BUSL-08 | Test Upload of Unexpected File Types | `file-upload-tests` | — |
| WSTG-BUSL-09 | Test Upload of Malicious Files | `file-upload-tests` | — |

### CLNT — Client-side

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-CLNT-01 | Testing for DOM-Based Cross Site Scripting | `xss-probe` | — |
| WSTG-CLNT-02 | Testing for JavaScript Execution | `clientside-js-review` | — |
| WSTG-CLNT-03 | Testing for HTML Injection | `xss-probe` | — |
| WSTG-CLNT-04 | Testing for Client-side URL Redirect | `clientside-js-review` | — |
| WSTG-CLNT-05 | Testing for CSS Injection | `clientside-js-review` | — |
| WSTG-CLNT-06 | Testing for Client-side Resource Manipulation | `clientside-js-review` | — |
| WSTG-CLNT-07 | Testing Cross Origin Resource Sharing | `headers-review`, `cors-websocket-check` | — |
| WSTG-CLNT-08 | Testing for Cross Site Flashing | `ria-legacy-check` | — |
| WSTG-CLNT-09 | Testing for Clickjacking | `headers-review` | — |
| WSTG-CLNT-10 | Testing WebSockets | `cors-websocket-check` | — |
| WSTG-CLNT-11 | Testing Web Messaging | `clientside-js-review` | — |
| WSTG-CLNT-12 | Testing Browser Storage | `clientside-js-review` | — |
| WSTG-CLNT-13 | Testing for Cross Site Script Inclusion | `clientside-js-review` | — |

### APIT — API Testing

| WSTG-ID | テスト名 | primary アクティビティ | secondary |
|---|---|---|---|
| WSTG-APIT-01 | Testing GraphQL | `api-graphql-test` | — |

## 3. アクティビティ詳細

### `recon-osint` — 外部 OSINT・公開情報の収集

検索エンジン・証明書透明性ログ・whois から、対象の公開露出面とサブドメインを洗い出す。

- ツール: theHarvester, crt.sh, whois, Google/Bing dorking, subfinder
- 想定成果物: `artifacts/subdomains.txt`, `artifacts/dorking-hits.md`, `cmd/whois.txt`
- カバー:
  - WSTG-INFO-01 (primary) Conduct Search Engine Discovery Reconnaissance for Information Leakage — 検索エンジンに残った情報漏えいの有無
  - WSTG-CONF-10 (secondary) Test for Subdomain Takeover — サブドメイン列挙が乗っ取り判定の入力

### `fingerprint-stack` — サーバ・フレームワークのフィンガープリント

ポート/サービス/ヘッダ/既知の指紋から、OS・Web サーバ・ミドルウェア・アプリ基盤を特定する。

- ツール: nmap -sV, whatweb, Wappalyzer, httpx
- 想定成果物: `cmd/nmap-sv.txt`, `cmd/whatweb.txt`, `artifacts/stack-summary.md`
- カバー:
  - WSTG-INFO-02 (primary) Fingerprint Web Server
  - WSTG-INFO-08 (primary) Fingerprint Web Application Framework
  - WSTG-CONF-01 (secondary) Test Network Infrastructure Configuration — 露出サービス一覧がネットワーク構成レビューの入力
  - WSTG-CONF-02 (secondary) Test Application Platform Configuration — 既知の既定構成・バージョンの手掛かり

### `tls-scan` — TLS 設定スキャン

対象の全 TLS ポートに対して暗号スイート・プロトコル・証明書・HSTS を一括検査する。

- ツール: testssl.sh, sslyze, nmap --script ssl-enum-ciphers
- 想定成果物: `cmd/testssl.txt`, `artifacts/tls-summary.md`
- カバー:
  - WSTG-CRYP-01 (primary) Testing for Weak Transport Layer Security
  - WSTG-CONF-07 (primary) Test HTTP Strict Transport Security — HSTS ヘッダの有無・max-age・includeSubDomains
  - WSTG-CONF-01 (secondary) Test Network Infrastructure Configuration — TLS を終端する構成要素の把握

### `http-methods` — HTTP メソッドの列挙と検証

OPTIONS 応答を鵜呑みにせず、実際に各メソッドを投げて許可状況と挙動差を確認する。

- ツール: curl, nmap http-methods NSE, ncat, Burp Repeater
- 想定成果物: `cmd/curl-options.txt`, `cmd/nmap-http-methods.txt`
- カバー:
  - WSTG-CONF-06 (primary) Test HTTP Methods
  - WSTG-INPV-03 (secondary) Testing for HTTP Verb Tampering — v4.2 では CONF-06 に統合（HTTP verb tampering）

### `headers-review` — レスポンスヘッダ一括精査（匿名 + 認証済み）

代表エンドポイントについて匿名・認証済みの応答を1セット取得し、セキュリティ関連ヘッダを横断レビューする。

- ツール: curl, Burp Suite, securityheaders.io 相当の手動チェック
- 想定成果物: `cmd/curl-headers-anon.txt`, `cmd/curl-headers-authn.txt`, `artifacts/headers-matrix.md`
- カバー:
  - WSTG-SESS-02 (primary) Testing for Cookies Attributes — Set-Cookie の Secure/HttpOnly/SameSite/Domain/Path/prefix
  - WSTG-CONF-07 (primary) Test HTTP Strict Transport Security — Strict-Transport-Security
  - WSTG-CLNT-09 (primary) Testing for Clickjacking — X-Frame-Options / CSP frame-ancestors
  - WSTG-ATHN-06 (primary) Testing for Browser Cache Weaknesses — Cache-Control / Pragma（認証済み画面のブラウザキャッシュ）
  - WSTG-CLNT-07 (primary) Testing Cross Origin Resource Sharing — Access-Control-Allow-Origin 等の CORS ヘッダ（旧指示の CONF-12 に相当）
  - WSTG-CRYP-03 (secondary) Testing for Sensitive Information Sent via Unencrypted Channels — 平文チャネルでの機微情報送出の兆候

### `metafiles-crawl` — メタファイル・公開コンテンツの収集

robots.txt・sitemap・.well-known・security.txt・HTML コメント・JS ソースを機械収集して読み込む。

- ツール: curl, wget, grep/ripgrep, Burp Suite
- 想定成果物: `cmd/curl-robots.txt`, `cmd/curl-wellknown.txt`, `artifacts/comments-grep.txt`
- カバー:
  - WSTG-INFO-03 (primary) Review Webserver Metafiles for Information Leakage
  - WSTG-INFO-05 (primary) Review Webpage Content for Information Leakage — HTML コメント・JS 内の情報漏えい
  - WSTG-CONF-05 (secondary) Enumerate Infrastructure and Application Admin Interfaces — robots.txt の Disallow が管理画面の入力になる

### `enum-apps` — 仮想ホスト・パスの列挙

DNS/vhost と URL パスをファジングし、同一ホスト上の別アプリ・別インスタンスを洗い出す。

- ツール: ffuf, dirsearch, gobuster, nmap -p-
- 想定成果物: `cmd/ffuf-paths.txt`, `cmd/ffuf-vhost.txt`, `artifacts/app-inventory.md`
- カバー:
  - WSTG-INFO-04 (primary) Enumerate Applications on Webserver
  - WSTG-INFO-06 (secondary) Identify Application Entry Points — 発見したパスがエントリポイント洗い出しの入力

### `burp-crawl-authn` — 認証済みクロールとエントリポイント洗い出し

認証済みセッションでアプリ全体をクロールし、エントリポイント・実行パス・アーキテクチャを把握する。

- ツール: Burp Suite, OWASP ZAP
- 想定成果物: `artifacts/entry-points.txt`, `artifacts/sitemap.xml`, `notes.md`
- カバー:
  - WSTG-INFO-06 (primary) Identify Application Entry Points
  - WSTG-INFO-07 (primary) Map Execution Paths Through Application
  - WSTG-INFO-10 (primary) Map Application Architecture — 経路上の WAF・LB・API GW の推定
  - WSTG-CONF-05 (primary) Enumerate Infrastructure and Application Admin Interfaces — 管理インタフェースの実在確認

### `session-capture` — セッション取得とログイン/ログアウト解析

ログイン〜操作〜ログアウトを1本のトレースとして取得し、トークンの生成・維持・破棄を追う。

- ツール: Burp Suite, Burp Sequencer, curl
- 想定成果物: `artifacts/session-trace.burp`, `artifacts/token-samples.txt`, `notes.md`
- カバー:
  - WSTG-SESS-01 (primary) Testing for Session Management Schema
  - WSTG-SESS-02 (primary) Testing for Cookies Attributes
  - WSTG-SESS-03 (primary) Testing for Session Fixation — ログイン前後でトークンが再発行されるか
  - WSTG-SESS-06 (primary) Testing for Logout Functionality
  - WSTG-SESS-07 (primary) Testing Session Timeout
  - WSTG-SESS-09 (secondary) Testing for Session Hijacking — 取得したトークンの再利用可否の入力

### `backup-unref` — 旧・バックアップ・未参照ファイルの探索

拡張子とファイル名のバリエーションを総当たりし、公開されている残骸ファイルを探す。

- ツール: ffuf, dirsearch, nikto
- 想定成果物: `cmd/ffuf-backup.txt`, `artifacts/found-files.md`
- カバー:
  - WSTG-CONF-03 (primary) Test File Extensions Handling for Sensitive Information
  - WSTG-CONF-04 (primary) Review Old Backup and Unreferenced Files for Sensitive Information

### `server-config-review` — サーバ／プラットフォーム構成レビュー

構成ファイル・配置・権限・不要機能を（可能なら読み取り権限を得て）レビューする。ホスト側の情報提供が前提。

- ツール: 手動レビュー, ls -l / icacls, nikto, CIS Benchmark チェックリスト
- 想定成果物: `artifacts/config-review.md`, `notes.md`
- カバー:
  - WSTG-CONF-01 (primary) Test Network Infrastructure Configuration
  - WSTG-CONF-02 (primary) Test Application Platform Configuration
  - WSTG-CONF-09 (primary) Test File Permission — ファイル・ディレクトリのパーミッション

### `cloud-and-takeover` — クラウドストレージ・サブドメイン乗っ取りの確認

公開バケット等のストレージ露出と、宙に浮いた DNS レコードによる乗っ取り可能性を確認する。

- ツール: dig, curl, grep, aws cli
- 想定成果物: `cmd/curl-bucket.txt`, `artifacts/dangling-dns.md`
- カバー:
  - WSTG-CONF-11 (primary) Test Cloud Storage
  - WSTG-CONF-10 (primary) Test for Subdomain Takeover

### `ria-legacy-check` — RIA クロスドメインポリシーとレガシー Flash の確認

crossdomain.xml / clientaccesspolicy.xml と、残存する Flash/Silverlight コンテンツを確認する。

- ツール: curl, 手動レビュー
- 想定成果物: `cmd/curl-crossdomain.txt`, `artifacts/ria-findings.md`
- カバー:
  - WSTG-CONF-08 (primary) Test RIA Cross Domain Policy
  - WSTG-CLNT-08 (primary) Testing for Cross Site Flashing

### `identity-model-review` — ロール定義・登録・払い出しプロセスのレビュー

ドキュメントとヒアリング＋実機で、ロール定義・アカウント登録・払い出し・ユーザ名ポリシーを確認する。

- ツール: 手動レビュー, ヒアリング, Burp Suite
- 想定成果物: `artifacts/role-matrix.md`, `notes.md`
- カバー:
  - WSTG-IDNT-01 (primary) Test Role Definitions
  - WSTG-IDNT-02 (primary) Test User Registration Process
  - WSTG-IDNT-03 (primary) Test Account Provisioning Process
  - WSTG-IDNT-05 (primary) Testing for Weak or Unenforced Username Policy

### `account-enum-probe` — アカウント列挙とロックアウトの検証

ログイン・登録・パスワードリセットの応答差（本文・ステータス・応答時間）を比較し、ロックアウト挙動も測る。

- ツール: Burp Intruder, ffuf, curl
- 想定成果物: `cmd/enum-responses.txt`, `artifacts/response-diff.md`
- カバー:
  - WSTG-IDNT-04 (primary) Testing for Account Enumeration and Guessable User Account
  - WSTG-ATHN-03 (primary) Testing for Weak Lock Out Mechanism — 試行回数と解除条件
  - WSTG-IDNT-05 (secondary) Testing for Weak or Unenforced Username Policy

### `authn-flow-review` — 認証フロー一括レビュー

認証の入口をひと通り触り、経路暗号化・既定資格情報・スキーマ迂回・記憶機能・パスワードポリシー・代替チャネルをまとめて確認する。

- ツール: Burp Suite, curl, ブラウザ開発者ツール
- 想定成果物: `artifacts/authn-notes.md`, `cmd/curl-login.txt`
- カバー:
  - WSTG-ATHN-01 (primary) Testing for Credentials Transported over an Encrypted Channel
  - WSTG-ATHN-02 (primary) Testing for Default Credentials
  - WSTG-ATHN-04 (primary) Testing for Bypassing Authentication Schema
  - WSTG-ATHN-05 (primary) Testing for Vulnerable Remember Password
  - WSTG-ATHN-06 (secondary) Testing for Browser Cache Weaknesses
  - WSTG-ATHN-07 (primary) Testing for Weak Password Policy
  - WSTG-ATHN-10 (primary) Testing for Weaker Authentication in Alternative Channel — モバイル・API・SSO 等の代替入口
  - WSTG-CRYP-03 (primary) Testing for Sensitive Information Sent via Unencrypted Channels — 資格情報・機微情報が平文チャネルに出ていないか

### `password-reset-review` — パスワード変更・リセット機能のレビュー

リセットトークンの強度・有効期限・所有確認、秘密の質問の強度を通しで確認する。

- ツール: Burp Suite, メールクライアント, 手動レビュー
- 想定成果物: `artifacts/reset-flow.md`, `notes.md`
- カバー:
  - WSTG-ATHN-08 (primary) Testing for Weak Security Question Answer
  - WSTG-ATHN-09 (primary) Testing for Weak Password Change or Reset Functionalities

### `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

各ロールで採取した代表リクエストを、他ロール・未認証で再送して差分を見る。IDOR は識別子を差し替えて確認。

- ツール: Burp Suite, Autorize / AuthMatrix, curl
- 想定成果物: `artifacts/authz-matrix.csv`, `notes.md`
- カバー:
  - WSTG-ATHZ-02 (primary) Testing for Bypassing Authorization Schema
  - WSTG-ATHZ-03 (primary) Testing for Privilege Escalation
  - WSTG-ATHZ-04 (primary) Testing for Insecure Direct Object References
  - WSTG-SESS-08 (secondary) Testing for Session Puzzling — 権限が別ロールへ引き継がれる挙動の兆候

### `traversal-probe` — ディレクトリトラバーサル・ファイルインクルードの検証

パス・ファイル名を扱うパラメータを洗い出し、トラバーサルと LFI/RFI を確認する。

- ツール: Burp Suite, ffuf, 手動 payload
- 想定成果物: `cmd/traversal.txt`, `artifacts/traversal-findings.md`
- カバー:
  - WSTG-ATHZ-01 (primary) Testing Directory Traversal File Include
  - WSTG-CONF-03 (secondary) Test File Extensions Handling for Sensitive Information — 拡張子の扱いが入力になる

### `session-abuse-tests` — セッションの悪用系テスト（露出・CSRF・パズリング・ハイジャック）

取得済みセッションを使って、トークンの露出経路・CSRF 防御・状態の取り違え・再利用可否を検証する。

- ツール: Burp Suite, curl, ブラウザ2枚
- 想定成果物: `artifacts/csrf-poc.html`, `artifacts/session-abuse.md`
- カバー:
  - WSTG-SESS-04 (primary) Testing for Exposed Session Variables — URL・ログ・Referer へのトークン露出
  - WSTG-SESS-05 (primary) Testing for Cross Site Request Forgery
  - WSTG-SESS-08 (primary) Testing for Session Puzzling
  - WSTG-SESS-09 (primary) Testing for Session Hijacking

### `xss-probe` — XSS・HTML インジェクションの検証

反射・保存・DOM の各経路について、代表入力点にペイロードを流して出力エンコーディングを確認する。

- ツール: Burp Suite, DOM Invader, 手動 payload
- 想定成果物: `artifacts/xss-findings.md`, `artifacts/payloads.txt`
- カバー:
  - WSTG-INPV-01 (primary) Testing for Reflected Cross Site Scripting
  - WSTG-INPV-02 (primary) Testing for Stored Cross Site Scripting
  - WSTG-CLNT-01 (primary) Testing for DOM-Based Cross Site Scripting
  - WSTG-CLNT-03 (primary) Testing for HTML Injection

### `clientside-js-review` — クライアントサイド JS のシンク・ストレージレビュー

JS のソース/シンクを追い、URL リダイレクト・CSS/リソース操作・postMessage・ブラウザストレージ・XSSI をまとめて確認する。

- ツール: ブラウザ開発者ツール, DOM Invader, Retire.js, Burp Suite
- 想定成果物: `artifacts/js-sinks.md`, `artifacts/storage-dump.md`
- カバー:
  - WSTG-CLNT-02 (primary) Testing for JavaScript Execution
  - WSTG-CLNT-04 (primary) Testing for Client-side URL Redirect
  - WSTG-CLNT-05 (primary) Testing for CSS Injection
  - WSTG-CLNT-06 (primary) Testing for Client-side Resource Manipulation
  - WSTG-CLNT-11 (primary) Testing Web Messaging — postMessage の origin 検証
  - WSTG-CLNT-12 (primary) Testing Browser Storage — localStorage / sessionStorage / IndexedDB
  - WSTG-CLNT-13 (primary) Testing for Cross Site Script Inclusion — XSSI（JSON/JS の外部読み込み）

### `cors-websocket-check` — CORS と WebSocket の検証

Origin を差し替えた応答差と、WebSocket ハンドシェイク・認可・暗号化を確認する。

- ツール: curl, Burp Suite, wscat
- 想定成果物: `cmd/curl-cors.txt`, `artifacts/ws-trace.md`
- カバー:
  - WSTG-CLNT-07 (primary) Testing Cross Origin Resource Sharing
  - WSTG-CLNT-10 (primary) Testing WebSockets

### `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

収集済みエントリポイントに対し、SQL/LDAP/XML/SSI/XPath/IMAP-SMTP/コード/コマンド/書式文字列/SSTI を横断的に試す。

- ツール: Burp Intruder, sqlmap, tplmap, 手動 payload
- 想定成果物: `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- カバー:
  - WSTG-INPV-05 (primary) Testing for SQL Injection
  - WSTG-INPV-06 (primary) Testing for LDAP Injection
  - WSTG-INPV-07 (primary) Testing for XML Injection
  - WSTG-INPV-08 (primary) Testing for SSI Injection
  - WSTG-INPV-09 (primary) Testing for XPath Injection
  - WSTG-INPV-10 (primary) Testing for IMAP SMTP Injection
  - WSTG-INPV-11 (primary) Testing for Code Injection
  - WSTG-INPV-12 (primary) Testing for Command Injection
  - WSTG-INPV-13 (primary) Testing for Format String Injection
  - WSTG-INPV-18 (primary) Testing for Server-side Template Injection
  - WSTG-ERRH-01 (secondary) Testing for Improper Error Handling — エラー応答の差分が副産物として得られる

### `http-request-tamper` — HTTP リクエスト改変系の検証

パラメータ汚染・ヘッダ分割/スマグリング・Host ヘッダ・受信リクエストの扱いをまとめて検証する。

- ツール: Burp Suite, Burp HTTP Request Smuggler, curl
- 想定成果物: `artifacts/request-tamper.md`, `cmd/curl-hosthdr.txt`
- カバー:
  - WSTG-INPV-04 (primary) Testing for HTTP Parameter Pollution
  - WSTG-INPV-15 (primary) Testing for HTTP Splitting Smuggling
  - WSTG-INPV-16 (primary) Testing for HTTP Incoming Requests
  - WSTG-INPV-17 (primary) Testing for Host Header Injection

### `ssrf-probe` — SSRF の検証

URL・ホスト名・ファイル参照を受けるパラメータを列挙し、外向き/内向きの到達性を確認する。

- ツール: Burp Collaborator, interactsh, curl
- 想定成果物: `artifacts/ssrf-findings.md`, `cmd/ssrf-probe.txt`
- カバー:
  - WSTG-INPV-19 (primary) Testing for Server-Side Request Forgery

### `error-handling-review` — エラーハンドリングのレビュー

異常系を意図的に起こし、返る情報量（スタックトレース・SQL エラー・内部パス）を確認する。

- ツール: Burp Suite, curl, 手動
- 想定成果物: `artifacts/error-samples.md`, `cmd/curl-errors.txt`
- カバー:
  - WSTG-ERRH-01 (primary) Testing for Improper Error Handling
  - WSTG-ERRH-02 (secondary) Testing for Stack Traces — v4.2 では ERRH-01 に統合（スタックトレース）
  - WSTG-INFO-05 (secondary) Review Webpage Content for Information Leakage

### `crypto-review` — 暗号利用のレビュー（パディングオラクル・弱い暗号・平文送出）

暗号化された値の改変応答差、暗号アルゴリズム・鍵管理、平文チャネルでの機微情報送出を確認する。

- ツール: padbuster, testssl.sh, Burp Suite, 手動レビュー
- 想定成果物: `artifacts/crypto-review.md`, `cmd/padbuster.txt`
- カバー:
  - WSTG-CRYP-02 (primary) Testing for Padding Oracle
  - WSTG-CRYP-03 (primary) Testing for Sensitive Information Sent via Unencrypted Channels
  - WSTG-CRYP-04 (primary) Testing for Weak Encryption

### `business-logic-walkthrough` — 業務ロジックの通し検証

業務フローを正常系→逸脱系で通し、データ妥当性・リクエスト偽造・整合性・時間・回数制限・順序・誤用防御を確認する。

- ツール: Burp Suite, 手動操作, 業務仕様書
- 想定成果物: `artifacts/logic-scenarios.md`, `notes.md`
- カバー:
  - WSTG-BUSL-01 (primary) Test Business Logic Data Validation
  - WSTG-BUSL-02 (primary) Test Ability to Forge Requests
  - WSTG-BUSL-03 (primary) Test Integrity Checks
  - WSTG-BUSL-04 (primary) Test for Process Timing
  - WSTG-BUSL-05 (primary) Test Number of Times a Function Can Be Used Limits
  - WSTG-BUSL-06 (primary) Testing for the Circumvention of Work Flows
  - WSTG-BUSL-07 (primary) Test Defenses Against Application Misuse
  - WSTG-INPV-14 (primary) Testing for Incubated Vulnerability — 潜伏型（保存された値が後で発火する）シナリオ

### `file-upload-tests` — ファイルアップロードの検証

想定外の拡張子・MIME・内容のファイルを投入し、保存先・実行可否・スキャンの有無を確認する。

- ツール: Burp Suite, EICAR テストファイル, 手動
- 想定成果物: `artifacts/upload-matrix.md`, `notes.md`
- カバー:
  - WSTG-BUSL-08 (primary) Test Upload of Unexpected File Types
  - WSTG-BUSL-09 (primary) Test Upload of Malicious Files
  - WSTG-CONF-03 (secondary) Test File Extensions Handling for Sensitive Information — 保存されたファイルの拡張子の扱い

### `api-graphql-test` — API / GraphQL の検証

スキーマ内省・バッチクエリ・深い入れ子・認可のかかり方を確認する。REST API も同じ枠で扱う。

- ツール: Burp Suite, GraphQL Voyager, InQL, curl
- 想定成果物: `artifacts/graphql-schema.json`, `artifacts/api-findings.md`
- カバー:
  - WSTG-APIT-01 (primary) Testing GraphQL
  - WSTG-ATHZ-02 (secondary) Testing for Bypassing Authorization Schema — API 側の認可漏れ

## 4. 未割当リスト

どのアクティビティにも割り当てられていない項目（アクティビティの追加が必要）:

- WSTG-INFO-09 — Fingerprint Web Application（統合済み）

secondary のみでカバーされている項目（単独判定には別アクティビティが要る）:

- WSTG-INPV-03 — Testing for HTTP Verb Tampering: http-methods
- WSTG-ERRH-02 — Testing for Stack Traces: error-handling-review

v4.2 で他項目に統合され、単独では実施しない項目:

- WSTG-INFO-09 — Fingerprint Web Application → Fingerprint Web Application Framework
- WSTG-INPV-03 — Testing for HTTP Verb Tampering → Test HTTP Methods
- WSTG-ERRH-02 — Testing for Stack Traces → Testing for Improper Error Handling
