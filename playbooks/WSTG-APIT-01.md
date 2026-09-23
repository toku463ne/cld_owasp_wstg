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

1. GraphQL エンドポイント（`/graphql`）に `curl`/Burp でイントロスペクション（`{__schema{types{name}}}`）が有効か確認
2. スキーマから機微な query/mutation を洗い、認可なしで呼べないか確認
3. 深いネスト/エイリアス量産でクエリコスト制限（DoS 耐性）・レート制限の有無を確認
   > ⚠️ **負荷注意（手順3）**: 深いネスト/エイリアス量産のクエリは、まさに GraphQL の DoS を誘発する検証。コスト制限が無いと1リクエストでサーバを落としうる。ネスト段数を段階的に上げる。
4. バッチクエリで認可迂回・列挙ができないか試し、成立点を finding に

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順3**: 深いネスト/エイリアス量産のクエリは、まさに GraphQL の DoS を誘発する検証。コスト制限が無いと1リクエストでサーバを落としうる。ネスト段数を段階的に上げる。

## 使用ツール

- curl
- Burp Suite

## 判定基準（pass / fail の見分け）

- **pass**: 本番で introspection が無効、クエリ深さ・複雑度・件数に上限があり、フィールド単位で認可される。
- **fail**: introspection が有効でスキーマ全体を取得できる、深い入れ子やバッチクエリで DoS 相当になる、認可を経ずに他人のデータを取得できる。
- 補足: REST API も同じ枠で扱う。認可漏れは ATHZ 系のカードと合わせて報告する。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/graphql-schema.json`, `artifacts/api-findings.md`
- `covers:` — `{id: WSTG-APIT-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `api-graphql-test` — API / GraphQL の検証

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/12-API_Testing/01-Testing_GraphQL
