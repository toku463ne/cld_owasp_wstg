# {{basename}} — {{activity_id}}（{{wstg_ids}}）
<!-- このアクティビティの観察ログ。検索しやすさ優先で書く:
       - 1観察=1行・列は固定（表計算やエディタで後から絞り込める）
       - タグは [角括弧]。例: grep -rn "\[fail\]" evidence/ で指摘だけ横断検索
       - wstg 列に対応する WSTG-ID を必ず入れる（grep -rn "WSTG-INFO-01" evidence/）
     判定は pass|fail|info|na|todo。確定した所見は run.yaml の covers: に要約を転記する。
     生トークン・資格情報・生ホスト名はここに書かず、証跡列に evidence 内パスで示す。 -->
<!-- tags候補: [creds] [pii] [internal] [config] [source] [error] [version] [auth-bypass] [idor] [injection] [misconfig] [info] -->

| wstg | 判定 | 対象/URL | 観察事実（要約） | tags | 証跡 |
|------|------|----------|------------------|------|------|
{{rows}}
