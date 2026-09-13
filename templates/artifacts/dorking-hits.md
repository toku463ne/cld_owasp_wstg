# {{basename}} — {{activity_id}}（{{wstg_ids}}）
<!-- 検索エンジン dork のヒット記録。1ヒット=1行・列は固定で書く。
       - 後で grep や表計算で絞り込めるよう、tags は [角括弧] で付ける
         例: grep -rn "\[creds\]" evidence/ で資格情報系のヒットだけ横断検索
       - 機微=yes の行は run.yaml の covers: に要約を転記（生値はここに置かず evidence 参照）
       - dork 列には実際に使ったクエリをそのまま貼ると、再現・再検索に強い -->
<!-- tags候補: [creds] [pii] [internal] [config] [source] [error] [doc] [subdomain] [other] -->

| # | dork | url | 機微 | tags | メモ |
|---|------|-----|------|------|------|
| 1 | `site:target.co.jp ext:conf OR ext:bak OR ext:sql` | https://target.co.jp/... | no | [info] |  |
