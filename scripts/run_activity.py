#!/usr/bin/env python3
"""record.html のコマンド手順を wrapper として実行し、純粋なエビデンスを作る。

    uv run scripts/run_activity.py <activity_dir>              # コマンド手順を全部実行
    uv run scripts/run_activity.py <activity_dir> --only WSTG-INFO-02      # その ID だけ
    uv run scripts/run_activity.py <activity_dir> --only WSTG-INFO-02:4    # その手順だけ
    uv run scripts/run_activity.py <activity_dir> --list       # 手順一覧（実行しない）
    uv run scripts/run_activity.py <activity_dir> --dry-run    # 実行内容の確認だけ

やること:
  1. criteria.yaml の手順のうち「コマンド手順」を bash -c で実行し、
     出力をコマンドごとに <dir>/cmd/<WSTG-ID>-s<n>-c<k>.txt に保存する（＝純粋なエビデンス）。
     手順のコマンドはパイプ・ループ・$() を含むので、シェル経由で実行する。
  2. run.yaml の commands: に実行記録（cmd/出力パス/終了コード/所要秒）を追記する。
  3. record.html が読む evidence.js を作り直す（cmd/・artifacts/ の中身を表示に反映）。

手動手順（Burp・ヒアリング等）はここでは実行しない。artifacts/manual-*.txt に
観察を書き、判定は run.yaml の covers に直接記入する（capture.py は廃止）。
コマンドは <activity_dir> ではなくリポジトリルート（またはカレント）で実行される
（OUTDIR は活動フォルダの artifacts/ に置換済み。相対パスはそこを指す）。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_activity import (  # noqa: E402
    iter_steps, resolve_activity, refresh_record, write_manual_stubs,
    print_missing_run_yaml,
)
from run_cmd import append_command  # noqa: E402


def select_steps(steps: list, only: str | None) -> list:
    """--only で手順を絞る（未指定なら「コマンド手順」を全部）。"""
    cmds = [s for s in steps if s["kind"] == "cmd"]
    if not only:
        return cmds
    wid, _, idx = only.partition(":")
    wid = wid.strip().upper()
    picked = [s for s in cmds if s["wid"] == wid and (not idx or str(s["idx"]) == idx)]
    return picked


def run_command(run: dict, step: dict, activity_dir: Path, timeout: int | None) -> dict:
    """手順内の1コマンドをシェルで実行し、そのコマンド専用のファイルに出力を保存する。

    コマンドごとに別ファイル（cmd/<WSTG-ID>-s<n>-c<k>.txt）に落とすことで、
    record.html が「コマンドの説明→コマンド→その結果」を1対1で並べられる。
    """
    out_rel = run["output"]
    out_path = activity_dir / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    started = _dt.datetime.now().astimezone()
    t0 = time.monotonic()

    header = [
        f"# {step['wid']} 手順{step['idx']} / {run['role']}",
        f"# started : {started.isoformat(timespec='seconds')}",
        f"# cwd     : {Path.cwd()}",
        f"$ {run['cmd']}",
        "# " + "-" * 68,
    ]
    exit_code = None
    with out_path.open("w", encoding="utf-8", errors="replace") as fh:
        fh.write("\n".join(header) + "\n")
        fh.flush()
        try:
            proc = subprocess.Popen(["bash", "-c", run["cmd"]], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1)
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                fh.write(line)
            exit_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill(); proc.wait()
            fh.write(f"\n[run_activity] timeout after {timeout}s\n")
            print(f"[run_activity] タイムアウト（{timeout}s）: {out_rel}", file=sys.stderr)
            exit_code = 124
        except FileNotFoundError:
            fh.write("[run_activity] bash が見つかりません\n")
            print("[run_activity] bash が見つかりません（bash を入れてください）", file=sys.stderr)
            exit_code = 127
        except KeyboardInterrupt:
            proc.terminate(); proc.wait()
            fh.write("\n[run_activity] interrupted by user\n")
            exit_code = 130
    duration = round(time.monotonic() - t0, 1)
    with out_path.open("a", encoding="utf-8") as fh:
        fh.write(f"# {'-' * 68}\n# exit_code: {exit_code}  duration_sec: {duration}\n")

    return {
        "cmd": run["cmd"],
        "output": out_rel,
        "started_at": started.isoformat(timespec="seconds"),
        "duration_sec": duration,
        "exit_code": exit_code,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("activity_dir", help="evidence/<activity_id>[-<target>]-<yyyymmdd>")
    ap.add_argument("--only", help="WSTG-ID または WSTG-ID:手順番号 に絞る")
    ap.add_argument("--list", action="store_true", help="手順一覧を出して終了（実行しない）")
    ap.add_argument("--dry-run", action="store_true", help="実行せず、走らせるコマンドだけ表示")
    ap.add_argument("--timeout", type=int, help="1手順あたりの秒。超えたら中断して記録")
    args = ap.parse_args()

    activity_dir = Path(args.activity_dir)
    if not (activity_dir / "run.yaml").exists():
        print_missing_run_yaml(activity_dir, "run_activity.py")
        return 2

    activity, tests, criteria, target, act_dir = resolve_activity(activity_dir)
    steps = iter_steps(activity, criteria, target, act_dir)
    write_manual_stubs(activity, criteria, target, activity_dir, act_dir, force=False)

    if args.list:
        for s in steps:
            mark = "cmd " if s["kind"] == "cmd" else "手動"
            print(f"  [{mark}] {s['wid']}:{s['idx']}  {s['desc'][:70]}")
        return 0

    todo = select_steps(steps, args.only)
    if not todo:
        print("実行するコマンド手順がありません（--only の指定か、手動手順のみ）。")
        print("  手順一覧は --list、手動手順は artifacts/manual-*.txt に観察を書いてください。")
        return 1

    if args.dry_run:
        for s in todo:
            print(f"[dry-run] {s['wid']}:{s['idx']}  {s['desc'][:70]}")
            for r in s["runs"]:
                print(f"    $ {r['cmd']}   -> {r['output']}")
        return 0

    run_yaml = activity_dir / "run.yaml"
    ran, failed = 0, 0
    for s in todo:
        print(f"\n===== {s['wid']} 手順{s['idx']}：{s['desc'][:60]} =====")
        for r in s["runs"]:
            entry = run_command(r, s, activity_dir, args.timeout)
            append_command(run_yaml, entry)
            ran += 1
            if entry["exit_code"]:
                failed += 1
            print(f"[run_activity] 保存: {activity_dir / entry['output']}  (exit={entry['exit_code']}, {entry['duration_sec']}s)")

    refresh_record(activity_dir)
    print(f"\n[run_activity] {ran} コマンドを実行（うち非0終了 {failed}）。evidence.js を更新しました。")
    print(f"  表示: {activity_dir / 'record.html'} をブラウザで開く")
    print(f"  判定: {run_yaml} の covers に verdict / finding を記入 → "
          f"uv run scripts/gen_record.py {activity_dir}")
    if failed:
        print("  ※ 非0終了の手順は出力が空/失敗の可能性。cmd/*.txt を見て pass の根拠にしない。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
