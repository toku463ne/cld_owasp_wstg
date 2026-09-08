# WSTG-APIT-01 — Testing GraphQL

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

GraphQL（および同種の API）のスキーマ露出・クエリ乱用・認可漏れを確認する。

WSTG の Test Objectives:

- Assess that a secure and production-ready configuration is deployed.
- Validate all input fields against generic attacks.
- Ensure that proper access controls are applied.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. **Introspection Queries** — Introspection queries are the method by which GraphQL lets you ask what queries are supported, which data types are available, and many more …
2. **Using Native GraphQL Introspection** — The most straightforward way is to send an HTTP request (using a personal proxy) with the following payload, taken from an article on Medium …
3. **Using GraphiQL** — GraphiQL is a web-based IDE for GraphQL
4. **Using GraphQL Playground** — GraphQL Playground is a GraphQL client
5. **Introspection Conclusion** — Introspection is a useful tool that allows users to gain more information about the GraphQL deployment
6. **Authorization** — Introspection is the first place to look for authorization problems
7. **Injection** — GraphQL is the implementation of the API layer of an application, and as such, it usually forwards the requests to a back end API or the dat …

## 使用ツール

- GraphQL Playground
- GraphQL Voyager
- sqlmap
- InQL (Burp Extension)
- GraphQL Raider (Burp Extension)
- GraphQL (Add-on for OWASP ZAP)

## 判定基準（pass / fail の見分け）

- **pass**: 本番で introspection が無効、クエリ深さ・複雑度・件数に上限があり、フィールド単位で認可される。
- **fail**: introspection が有効でスキーマ全体を取得できる、深い入れ子やバッチクエリで DoS 相当になる、認可を経ずに他人のデータを取得できる。
- 補足: REST API も同じ枠で扱う。認可漏れは ATHZ 系のカードと合わせて報告する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_cmd.py` 経由で実行したコマンドは自動で残る
- `steps:` — GUI（Burp 等）の操作は手記録
- `artifacts:` — `artifacts/graphql-schema.json`, `artifacts/api-findings.md`
- `covers:` — `{id: WSTG-APIT-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `api-graphql-test` — API / GraphQL の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/12-API_Testing/01-Testing_GraphQL
