#!/usr/bin/env python3
"""1つの対象サイトに対し、全アクティビティのフォルダ作成とコマンド実行を一括で回す。

    uv run scripts/run_target.py --target wwwtest.example.com
    uv run scripts/run_target.py --target example.com --only recon-osint,metafiles-crawl
    uv run scripts/run_target.py --target example.com --no-run    # フォルダ作成だけ
    uv run scripts/run_target.py --target example.com --list      # 実施予定を出すだけ
    uv run scripts/run_target.py --target example.com --reuse-latest  # 日付違いの既存フォルダを使い回す

やること（coverage.yaml の activities: の順に、対象を1つ固定して）:
  1. 各アクティビティのフォルダ一式を作る（new_activity.create_activity）。
     既にあるものは作り直さない（＝作成済みは次回スキップ）。
     フォルダ名は日付入りなので、別の日に叩くと新しいフォルダになる。過去の日付のフォルダを
     そのまま使うには --reuse-latest（アクティビティごとに最新日付の既存フォルダを使い、
     無いものだけ --date の日付で作る）。
  2. 各フォルダのコマンド手順を実行する（run_activity.execute_steps）。
     既定は再開モード（--skip-done）: 前回 exit_code 0 で終わったコマンドは飛ばす（手順を直してコマンドが変わったものは再実行）。
     既定は停止モード（--stop-on-error）: 非0終了が出たらそこで打ち切る。
        → エラー箇所を直して同じコマンドを再実行すれば、成功済みは飛ばして続きから進む。
     人の作業（ブラウザで保存・ログイン・一覧の作成・社外での実行など）で置く入力を読む手順
     （手動→コマンド。入力ガード `|| exit 75` を持つもの）は一括では走らせず、最後に一覧と
     実行コマンド（run_activity.py <フォルダ> --only <WSTG-ID>:<手順>）を出す。作業のあと人が実行する。
     その結果を読む後続の手順は、結果ができるまで「入力待ち」で飛ばし、再実行すると走る。

対象は1サイト固定（--target）。複数サイトを混ぜたいときはサイトごとに叩く。
coverage.yaml で target_kind: domain のアクティビティ（recon-osint など。target が FQDN ではなく
ドメイン）は一括対象から外す。回すときは --only で個別に指定する:
    uv run scripts/run_target.py --target example.com --only recon-osint
手動手順しか無いアクティビティはフォルダだけ作られる（コマンドは実行しない）。

同じコマンドを何度も走らせない: ある WSTG-ID を secondary で扱うアクティビティでは、その ID を
primary で扱うアクティビティが同じ一括処理に入っていれば、その ID のコマンド手順を実行しない
（primary 側で1回だけ実行する。例: WSTG-CONF-01 の nikto は server-config-review でだけ走る）。
secondary 側の判定は primary 側のエビデンスを参照する。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_activity import (  # noqa: E402
    COVERAGE_YAML, WSTG_TESTS, CRITERIA_YAML, load_yaml,
    create_activity, resolve_activity, iter_steps, refresh_record, find_latest_dir,
    primary_owners, split_delegated,
)
from run_activity import (  # noqa: E402
    select_steps, execute_steps, manual_run_steps, manual_not_done,
)
from new_activity import manual_run_hint  # noqa: E402

# primary_owners / split_delegated は new_activity に移動（run_activity 単体実行でも同じ委譲を
# 使えるようにするため）。ここでは import して従来どおりの名前で使う。


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", required=True, help="対象サイト（1つ固定。フォルダ名・コマンドの target 置換に使う）")
    ap.add_argument("--date", default=None, help="yyyymmdd（既定: 今日）")
    ap.add_argument("--tester", default="TOKU")
    ap.add_argument("--root", default=None, help="出力先ルート（既定: evidence/）")
    ap.add_argument("--only", help="アクティビティ ID をカンマ区切りで指定（既定: 全部）")
    ap.add_argument("--timeout", type=int, help="1コマンドあたりの秒。超えたら中断して記録")
    ap.add_argument("--list", action="store_true", help="実施予定（作成/実行対象）を出して終了")
    ap.add_argument("--no-run", action="store_true", help="フォルダ作成だけ行い、コマンドは実行しない")
    ap.add_argument("--reuse-latest", action="store_true",
                    help="日付違いでも既存フォルダ（<activity>-<target>-<yyyymmdd>）があれば最新のものを使う。"
                         "無いアクティビティだけ --date の日付で作る")
    ap.add_argument("--rerun-all", action="store_true",
                    help="前回成功したコマンドも作り直して再実行する（既定は成功分をスキップ）")
    ap.add_argument("--keep-going", action="store_true",
                    help="非0終了が出ても止めず最後まで回す（既定はそこで打ち切り）")
    args = ap.parse_args()

    import datetime as _dt
    date = args.date or _dt.date.today().strftime("%Y%m%d")
    root = args.root or str((Path(__file__).resolve().parent.parent) / "evidence")
    skip_done = not args.rerun_all
    stop_on_error = not args.keep_going

    coverage = load_yaml(COVERAGE_YAML)
    tests = {t["id"]: t for t in load_yaml(WSTG_TESTS)["tests"]}
    criteria = load_yaml(CRITERIA_YAML) if CRITERIA_YAML.exists() else {}
    activities = coverage["activities"]

    if args.only:
        want = [x.strip() for x in args.only.split(",") if x.strip()]
        by_id = {a["id"]: a for a in activities}
        unknown = [x for x in want if x not in by_id]
        if unknown:
            print(f"未知の activity_id: {', '.join(unknown)}", file=sys.stderr)
            print(f"  指定できるのは: {', '.join(a['id'] for a in activities)}", file=sys.stderr)
            return 2
        activities = [by_id[x] for x in want]   # --only の並び順を尊重
    else:
        # target が FQDN 前提ではないもの（ドメイン単位の OSINT 等）は一括では回さない
        domain_acts = [a["id"] for a in activities if a.get("target_kind") == "domain"]
        activities = [a for a in activities if a.get("target_kind") != "domain"]
        if domain_acts:
            print(f"[run_target] target がドメイン単位のため一括対象から外します: {', '.join(domain_acts)}")
            print(f"  回すときは個別に: uv run scripts/run_target.py --target <ドメイン> "
                  f"--only {','.join(domain_acts)}")

    if args.list:
        print(f"対象: {args.target}  日付: {date}  出力先: {root}")
        print(f"アクティビティ {len(activities)} 本を実施予定"
              f"（{'再開' if skip_done else '全再実行'} / "
              f"{'エラーで停止' if stop_on_error else '最後まで継続'}）:")
        for a in activities:
            covered = ", ".join(c["id"] for c in a.get("covers", []))
            print(f"  {a['id']:26s} {covered}")
            if args.reuse_latest:
                found = find_latest_dir(root, a, args.target)
                print(f"  {'':26s} → {'既存を使う: ' + found.name if found else '新規作成'}")
        return 0

    owners = primary_owners(activities)
    created = existed = 0
    total = {"ran": 0, "failed": 0, "skipped": 0, "pending": 0}
    waiting: list = []
    manual_left: list = []   # (act_dir, step) 一括では走らない手動→コマンドで、まだ実行していないもの
    for a in activities:
        aid = a["id"]
        reused = find_latest_dir(root, a, args.target) if args.reuse_latest else None
        if reused is not None:
            result = {"target_dir": reused, "created": False}
        else:
            result = create_activity(a, tests, criteria, target=args.target,
                                     date=date, tester=args.tester, root=root,
                                     force=False)
        target_dir = result["target_dir"]
        if result["created"]:
            created += 1
            print(f"\n########## {aid}  作成: {target_dir}")
        else:
            existed += 1
            print(f"\n########## {aid}  既存: {target_dir}（作り直さない）")

        if args.no_run:
            continue

        # 実行するコマンド手順を組み立てる（run.yaml から activity を引き直す）
        activity, tests2, criteria2, target, act_dir = resolve_activity(target_dir)
        steps = iter_steps(activity, criteria2, target, act_dir)
        todo, delegated = split_delegated(select_steps(steps, None), owners)
        manual, _ = split_delegated(manual_run_steps(steps), owners)
        manual_left += [(act_dir, s) for s in manual_not_done(target_dir, manual)]
        for wid, acts in delegated.items():
            print(f"  （{wid} は secondary。コマンドは primary の {', '.join(acts)} で実行するので、ここでは実行しない）")
        if not todo:
            print(f"  （一括で走らせるコマンド手順なし: {aid} は手動手順のみ。フォルダだけ用意しました）")
            refresh_record(target_dir)
            continue

        summary = execute_steps(target_dir / "run.yaml", target_dir, todo,
                                timeout=args.timeout, skip_done=skip_done,
                                stop_on_error=stop_on_error, manual=manual)
        refresh_record(target_dir)
        for k in total:
            total[k] += summary[k]
        waiting += summary["waiting"]

        if summary["aborted"]:
            print("\n" + "=" * 70)
            print(f"[run_target] {aid} で非0終了が出たため一括処理を打ち切りました。")
            print(f"  直す場所: {target_dir} の cmd/ 末尾（exit_code）と criteria.yaml の該当手順")
            print("  直したら同じコマンドを再実行してください。成功済みは自動でスキップして続きから進みます:")
            print(f"    uv run scripts/run_target.py --target {args.target} --date {date}"
                  f"{' --reuse-latest' if args.reuse_latest else ''}")
            print(f"  作成 {created} / 既存 {existed}、"
                  f"実行 {total['ran']}・スキップ {total['skipped']}・非0終了 {total['failed']}"
                  f"・入力待ち {total['pending']}")
            return 3

    print("\n" + "=" * 70)
    if args.no_run:
        print(f"[run_target] フォルダ作成のみ完了。作成 {created} / 既存 {existed}。")
        print(f"  実行するには: uv run scripts/run_target.py --target {args.target} --date {date}")
        return 0
    print(f"[run_target] 完了。作成 {created} / 既存 {existed}、"
          f"実行 {total['ran']}・スキップ {total['skipped']}・非0終了 {total['failed']}"
          f"・入力待ち {total['pending']}。")
    if waiting:
        print("  入力待ち（人が artifacts/ に入力を置く手順。各手順の説明どおりに置いてから、同じコマンドを再実行）:")
        for w in waiting:
            print(f"    - {w}")
        print(f"    uv run scripts/run_target.py --target {args.target} --date {date}"
              f"{' --reuse-latest' if args.reuse_latest else ''}")
    if manual_left:
        print("  手動→コマンド（一括では走らない。各手順の説明の作業を済ませてから、次のコマンドで実行）:")
        for act_dir, s in manual_left:
            print(f"    - {s['wid']} 手順{s['idx']}: {s['desc'][:50]}")
            print(f"        {manual_run_hint(act_dir, s['wid'], s['idx'])}")
        print("    実行したあと run_target を再実行すると、その結果を読む後続の手順が走る。")
    if total["failed"]:
        print("  ※ --keep-going 指定で非0終了があります。cmd/*.txt を見て pass の根拠にしないこと。")
    print("  判定: 各 run.yaml の covers に verdict / finding を記入（Web の record.html でも可）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
