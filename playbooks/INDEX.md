# プレイブックカード一覧

> 自動生成: `uv run scripts/gen_playbooks.py`

1テスト=1枚。社内 Gemini への貼り付け・新人への説明台本にそのまま使える粒度。


## INFO — Information Gathering

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-INFO-01](WSTG-INFO-01.md) | Conduct Search Engine Discovery Reconnaissance for Information Leakage | `recon-osint` |
| [WSTG-INFO-02](WSTG-INFO-02.md) | Fingerprint Web Server | `fingerprint-stack` |
| [WSTG-INFO-03](WSTG-INFO-03.md) | Review Webserver Metafiles for Information Leakage | `metafiles-crawl` |
| [WSTG-INFO-04](WSTG-INFO-04.md) | Enumerate Applications on Webserver | `enum-apps` |
| [WSTG-INFO-05](WSTG-INFO-05.md) | Review Webpage Content for Information Leakage | `metafiles-crawl`, `error-handling-review` |
| [WSTG-INFO-06](WSTG-INFO-06.md) | Identify Application Entry Points | `burp-crawl-authn`, `enum-apps` |
| [WSTG-INFO-07](WSTG-INFO-07.md) | Map Execution Paths Through Application | `burp-crawl-authn` |
| [WSTG-INFO-08](WSTG-INFO-08.md) | Fingerprint Web Application Framework | `fingerprint-stack` |
| [WSTG-INFO-09](WSTG-INFO-09.md) | Fingerprint Web Application（v4.2 で統合済み） | — |
| [WSTG-INFO-10](WSTG-INFO-10.md) | Map Application Architecture | `burp-crawl-authn` |

## CONF — Configuration and Deployment Management

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-CONF-01](WSTG-CONF-01.md) | Test Network Infrastructure Configuration | `server-config-review`, `fingerprint-stack`, `tls-scan` |
| [WSTG-CONF-02](WSTG-CONF-02.md) | Test Application Platform Configuration | `server-config-review`, `fingerprint-stack` |
| [WSTG-CONF-03](WSTG-CONF-03.md) | Test File Extensions Handling for Sensitive Information | `backup-unref`, `traversal-probe`, `file-upload-tests` |
| [WSTG-CONF-04](WSTG-CONF-04.md) | Review Old Backup and Unreferenced Files for Sensitive Information | `backup-unref` |
| [WSTG-CONF-05](WSTG-CONF-05.md) | Enumerate Infrastructure and Application Admin Interfaces | `burp-crawl-authn`, `metafiles-crawl` |
| [WSTG-CONF-06](WSTG-CONF-06.md) | Test HTTP Methods | `http-methods` |
| [WSTG-CONF-07](WSTG-CONF-07.md) | Test HTTP Strict Transport Security | `tls-scan`, `headers-review` |
| [WSTG-CONF-08](WSTG-CONF-08.md) | Test RIA Cross Domain Policy | `ria-legacy-check` |
| [WSTG-CONF-09](WSTG-CONF-09.md) | Test File Permission | `server-config-review` |
| [WSTG-CONF-10](WSTG-CONF-10.md) | Test for Subdomain Takeover | `cloud-and-takeover`, `recon-osint` |
| [WSTG-CONF-11](WSTG-CONF-11.md) | Test Cloud Storage | `cloud-and-takeover` |

## IDNT — Identity Management

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-IDNT-01](WSTG-IDNT-01.md) | Test Role Definitions | `identity-model-review` |
| [WSTG-IDNT-02](WSTG-IDNT-02.md) | Test User Registration Process | `identity-model-review` |
| [WSTG-IDNT-03](WSTG-IDNT-03.md) | Test Account Provisioning Process | `identity-model-review` |
| [WSTG-IDNT-04](WSTG-IDNT-04.md) | Testing for Account Enumeration and Guessable User Account | `account-enum-probe` |
| [WSTG-IDNT-05](WSTG-IDNT-05.md) | Testing for Weak or Unenforced Username Policy | `identity-model-review`, `account-enum-probe` |

## ATHN — Authentication

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-ATHN-01](WSTG-ATHN-01.md) | Testing for Credentials Transported over an Encrypted Channel | `authn-flow-review` |
| [WSTG-ATHN-02](WSTG-ATHN-02.md) | Testing for Default Credentials | `authn-flow-review` |
| [WSTG-ATHN-03](WSTG-ATHN-03.md) | Testing for Weak Lock Out Mechanism | `account-enum-probe` |
| [WSTG-ATHN-04](WSTG-ATHN-04.md) | Testing for Bypassing Authentication Schema | `authn-flow-review` |
| [WSTG-ATHN-05](WSTG-ATHN-05.md) | Testing for Vulnerable Remember Password | `authn-flow-review` |
| [WSTG-ATHN-06](WSTG-ATHN-06.md) | Testing for Browser Cache Weaknesses | `headers-review`, `authn-flow-review` |
| [WSTG-ATHN-07](WSTG-ATHN-07.md) | Testing for Weak Password Policy | `authn-flow-review` |
| [WSTG-ATHN-08](WSTG-ATHN-08.md) | Testing for Weak Security Question Answer | `password-reset-review` |
| [WSTG-ATHN-09](WSTG-ATHN-09.md) | Testing for Weak Password Change or Reset Functionalities | `password-reset-review` |
| [WSTG-ATHN-10](WSTG-ATHN-10.md) | Testing for Weaker Authentication in Alternative Channel | `authn-flow-review` |

## ATHZ — Authorization

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-ATHZ-01](WSTG-ATHZ-01.md) | Testing Directory Traversal File Include | `traversal-probe` |
| [WSTG-ATHZ-02](WSTG-ATHZ-02.md) | Testing for Bypassing Authorization Schema | `authz-matrix`, `api-graphql-test` |
| [WSTG-ATHZ-03](WSTG-ATHZ-03.md) | Testing for Privilege Escalation | `authz-matrix` |
| [WSTG-ATHZ-04](WSTG-ATHZ-04.md) | Testing for Insecure Direct Object References | `authz-matrix` |

## SESS — Session Management

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-SESS-01](WSTG-SESS-01.md) | Testing for Session Management Schema | `session-capture` |
| [WSTG-SESS-02](WSTG-SESS-02.md) | Testing for Cookies Attributes | `headers-review`, `session-capture` |
| [WSTG-SESS-03](WSTG-SESS-03.md) | Testing for Session Fixation | `session-capture` |
| [WSTG-SESS-04](WSTG-SESS-04.md) | Testing for Exposed Session Variables | `session-abuse-tests` |
| [WSTG-SESS-05](WSTG-SESS-05.md) | Testing for Cross Site Request Forgery | `session-abuse-tests` |
| [WSTG-SESS-06](WSTG-SESS-06.md) | Testing for Logout Functionality | `session-capture` |
| [WSTG-SESS-07](WSTG-SESS-07.md) | Testing Session Timeout | `session-capture` |
| [WSTG-SESS-08](WSTG-SESS-08.md) | Testing for Session Puzzling | `session-abuse-tests`, `authz-matrix` |
| [WSTG-SESS-09](WSTG-SESS-09.md) | Testing for Session Hijacking | `session-abuse-tests`, `session-capture` |

## INPV — Input Validation

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-INPV-01](WSTG-INPV-01.md) | Testing for Reflected Cross Site Scripting | `xss-probe` |
| [WSTG-INPV-02](WSTG-INPV-02.md) | Testing for Stored Cross Site Scripting | `xss-probe` |
| [WSTG-INPV-03](WSTG-INPV-03.md) | Testing for HTTP Verb Tampering（v4.2 で統合済み） | `http-methods` |
| [WSTG-INPV-04](WSTG-INPV-04.md) | Testing for HTTP Parameter Pollution | `http-request-tamper` |
| [WSTG-INPV-05](WSTG-INPV-05.md) | Testing for SQL Injection | `injection-fuzz-server` |
| [WSTG-INPV-06](WSTG-INPV-06.md) | Testing for LDAP Injection | `injection-fuzz-server` |
| [WSTG-INPV-07](WSTG-INPV-07.md) | Testing for XML Injection | `injection-fuzz-server` |
| [WSTG-INPV-08](WSTG-INPV-08.md) | Testing for SSI Injection | `injection-fuzz-server` |
| [WSTG-INPV-09](WSTG-INPV-09.md) | Testing for XPath Injection | `injection-fuzz-server` |
| [WSTG-INPV-10](WSTG-INPV-10.md) | Testing for IMAP SMTP Injection | `injection-fuzz-server` |
| [WSTG-INPV-11](WSTG-INPV-11.md) | Testing for Code Injection | `injection-fuzz-server` |
| [WSTG-INPV-12](WSTG-INPV-12.md) | Testing for Command Injection | `injection-fuzz-server` |
| [WSTG-INPV-13](WSTG-INPV-13.md) | Testing for Format String Injection | `injection-fuzz-server` |
| [WSTG-INPV-14](WSTG-INPV-14.md) | Testing for Incubated Vulnerability | `business-logic-walkthrough` |
| [WSTG-INPV-15](WSTG-INPV-15.md) | Testing for HTTP Splitting Smuggling | `http-request-tamper` |
| [WSTG-INPV-16](WSTG-INPV-16.md) | Testing for HTTP Incoming Requests | `http-request-tamper` |
| [WSTG-INPV-17](WSTG-INPV-17.md) | Testing for Host Header Injection | `http-request-tamper` |
| [WSTG-INPV-18](WSTG-INPV-18.md) | Testing for Server-side Template Injection | `injection-fuzz-server` |
| [WSTG-INPV-19](WSTG-INPV-19.md) | Testing for Server-Side Request Forgery | `ssrf-probe` |

## ERRH — Error Handling

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-ERRH-01](WSTG-ERRH-01.md) | Testing for Improper Error Handling | `error-handling-review`, `injection-fuzz-server` |
| [WSTG-ERRH-02](WSTG-ERRH-02.md) | Testing for Stack Traces（v4.2 で統合済み） | `error-handling-review` |

## CRYP — Weak Cryptography

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-CRYP-01](WSTG-CRYP-01.md) | Testing for Weak Transport Layer Security | `tls-scan` |
| [WSTG-CRYP-02](WSTG-CRYP-02.md) | Testing for Padding Oracle | `crypto-review` |
| [WSTG-CRYP-03](WSTG-CRYP-03.md) | Testing for Sensitive Information Sent via Unencrypted Channels | `authn-flow-review`, `crypto-review`, `headers-review` |
| [WSTG-CRYP-04](WSTG-CRYP-04.md) | Testing for Weak Encryption | `crypto-review` |

## BUSL — Business Logic

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-BUSL-01](WSTG-BUSL-01.md) | Test Business Logic Data Validation | `business-logic-walkthrough` |
| [WSTG-BUSL-02](WSTG-BUSL-02.md) | Test Ability to Forge Requests | `business-logic-walkthrough` |
| [WSTG-BUSL-03](WSTG-BUSL-03.md) | Test Integrity Checks | `business-logic-walkthrough` |
| [WSTG-BUSL-04](WSTG-BUSL-04.md) | Test for Process Timing | `business-logic-walkthrough` |
| [WSTG-BUSL-05](WSTG-BUSL-05.md) | Test Number of Times a Function Can Be Used Limits | `business-logic-walkthrough` |
| [WSTG-BUSL-06](WSTG-BUSL-06.md) | Testing for the Circumvention of Work Flows | `business-logic-walkthrough` |
| [WSTG-BUSL-07](WSTG-BUSL-07.md) | Test Defenses Against Application Misuse | `business-logic-walkthrough` |
| [WSTG-BUSL-08](WSTG-BUSL-08.md) | Test Upload of Unexpected File Types | `file-upload-tests` |
| [WSTG-BUSL-09](WSTG-BUSL-09.md) | Test Upload of Malicious Files | `file-upload-tests` |

## CLNT — Client-side

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-CLNT-01](WSTG-CLNT-01.md) | Testing for DOM-Based Cross Site Scripting | `xss-probe` |
| [WSTG-CLNT-02](WSTG-CLNT-02.md) | Testing for JavaScript Execution | `clientside-js-review` |
| [WSTG-CLNT-03](WSTG-CLNT-03.md) | Testing for HTML Injection | `xss-probe` |
| [WSTG-CLNT-04](WSTG-CLNT-04.md) | Testing for Client-side URL Redirect | `clientside-js-review` |
| [WSTG-CLNT-05](WSTG-CLNT-05.md) | Testing for CSS Injection | `clientside-js-review` |
| [WSTG-CLNT-06](WSTG-CLNT-06.md) | Testing for Client-side Resource Manipulation | `clientside-js-review` |
| [WSTG-CLNT-07](WSTG-CLNT-07.md) | Testing Cross Origin Resource Sharing | `headers-review`, `cors-websocket-check` |
| [WSTG-CLNT-08](WSTG-CLNT-08.md) | Testing for Cross Site Flashing | `ria-legacy-check` |
| [WSTG-CLNT-09](WSTG-CLNT-09.md) | Testing for Clickjacking | `headers-review` |
| [WSTG-CLNT-10](WSTG-CLNT-10.md) | Testing WebSockets | `cors-websocket-check` |
| [WSTG-CLNT-11](WSTG-CLNT-11.md) | Testing Web Messaging | `clientside-js-review` |
| [WSTG-CLNT-12](WSTG-CLNT-12.md) | Testing Browser Storage | `clientside-js-review` |
| [WSTG-CLNT-13](WSTG-CLNT-13.md) | Testing for Cross Site Script Inclusion | `clientside-js-review` |

## APIT — API Testing

| カード | テスト名 | アクティビティ |
|---|---|---|
| [WSTG-APIT-01](WSTG-APIT-01.md) | Testing GraphQL | `api-graphql-test` |
