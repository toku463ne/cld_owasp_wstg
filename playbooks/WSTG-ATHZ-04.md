# WSTG-ATHZ-04 — Testing for Insecure Direct Object References

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

識別子を差し替えて他人のデータにアクセスできないか（IDOR）を確認する。

WSTG の Test Objectives:

- Identify points where object references may occur.
- Assess the access control measures and if they're vulnerable to IDOR.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. オブジェクト参照パラメータ（`?id=1001`,`/orders/1001`,ファイル名）を他人の値に変えて開けるか Burp で試す
2. 連番・UUID・base64/ハッシュ ID を Burp Intruder で推測/列挙し、他人の資源にアクセスできるか確認
   > ⚠️ **負荷注意（手順2）**: Intruder による ID 列挙は大量リクエストに加え、他人の資源への実アクセスを伴う。件数を絞り、取得データは要約のみを finding に。
3. 参照方法を変えても（GET/POST/JSON body/multipart）認可チェックが一貫しているか確認
4. 自分の ID でのみアクセスできるべき資源に他 ID で到達できたら IDOR として finding に

## ⚠️ 負荷・レート制限・想定外への注意

本調査は社内のプライベートネットワークで行う前提だが、想定外（古い機器・共有アカウント・外部 API 依存）は起こりうる。次の手順は**対象や外部サービスに負荷をかける／レート制限・アカウントロック・DoS を誘発しうる**。実施前に時間帯・範囲の合意を確認し、少量から段階的に。

- **手順2**: Intruder による ID 列挙は大量リクエストに加え、他人の資源への実アクセスを伴う。件数を絞り、取得データは要約のみを finding に。

## 使用ツール

- Burp Intruder

## 判定基準（pass / fail の見分け）

- **pass**: 識別子を他ユーザのものに変えると 403/404 になり、所有者チェックが効いている。
- **fail**: 連番 ID や UUID の差し替えで他ユーザのデータを閲覧・更新・削除できる。
- 補足: 参照だけでなく更新・削除系も試す。テストデータ同士で行い、実データは触らない。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/authz-matrix.csv`, `notes.md`
- `covers:` — `{id: WSTG-ATHZ-04, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `authz-matrix` — 権限マトリクス試験（ロール横断リクエスト再送）

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/05-Authorization_Testing/04-Testing_for_Insecure_Direct_Object_References
