# WSTG-ERRH-01 — Testing for Improper Error Handling

<!-- 自動生成: scripts/gen_playbooks.py — このファイルを直接編集しない。
     判定基準は matrix/criteria.yaml、アクティビティは matrix/coverage.yaml を直す。 -->

## 目的

エラー応答が内部情報を漏らしていないかを確認する（スタックトレースを含む）。

WSTG の Test Objectives:

- Identify existing error output.
- Analyze the different output returned.

## 前提 / スコープ

- 対象: 検査スコープ内のホスト・アプリ
- 権限: 必要な認証済みアカウント（ロールごとに1つ）
- 準備: プロキシ設定・スコープ制限（対象外ホストへ飛ばさない）

## 手順

1. エラーを誘発して内部情報の漏れを確認する: `for u in '/nope-$(date +%s)' '/%c0%ae/' '/?id=%27' '/api/nope'; do echo "===== $u ====="; curl -s -m 10 "https://target$u" | grep -iE 'exception|stack trace|at [a-z0-9_.]+\(|sql|syntax error|ORA-|PDOException|Traceback|line [0-9]+|/var/www|C:\\\\|Warning:|Fatal error' | head -20; done | tee evidence/<活動フォルダ>/artifacts/error-leak.txt`。ヒットしたら詳細エラーが露出＝finding。存在しないパスに加え、各エンドポイントの型不一致・不正入力も手動で試す
2. 4xx/5xx の両方、API（JSON）とフロント（HTML）の両方で応答本文を確認
3. エラー時に内部情報（フレームワーク・DB・内部 IP・バージョン）が漏れないか確認
4. 詳細が出る箇所を列挙。v4.2 では ERRH-02（スタックトレース）もここに統合して判定

## 使用ツール

- curl

## 判定基準（pass / fail の見分け）

- **pass**: 異常系でも汎用エラー画面が返り、内部パス・SQL・スタックトレース・製品バージョンが出ない。
- **fail**: 例外のスタックトレース・SQL エラー・内部パス・デバッグ情報がそのまま表示される。
- 補足: 4xx/5xx の両方、API とフロントの両方で確認する。v4.2 では ERRH-02 がここに統合。

## 記録すべき成果物（run.yaml へ）

- `commands:` — `scripts/run_activity.py`（手順を実行）/ `run_cmd.py`（単発）が自動で残す
- 手動手順（GUI・Burp 等）の観察は `artifacts/manual-*.txt` に書く
- `artifacts:` — `artifacts/error-samples.md`, `cmd/curl-errors.txt`, `cmd/sqlmap.txt`, `artifacts/injection-findings.md`
- `covers:` — `{id: WSTG-ERRH-01, verdict: pass|fail|info|na, finding: 要約, evidence: パス}`

## カバーするアクティビティ

- `error-handling-review` — エラーハンドリングのレビュー
- `injection-fuzz-server` — サーバサイド・インジェクション系の一括ファジング

原文: https://owasp.org/www-project-web-security-testing-guide/stable/4-Web_Application_Security_Testing/08-Testing_for_Error_Handling/01-Testing_For_Improper_Error_Handling
