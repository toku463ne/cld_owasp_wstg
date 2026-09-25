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
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from new_activity import (  # noqa: E402
    iter_steps, resolve_activity, refresh_record, write_manual_stubs,
    print_missing_run_yaml, primary_owners, split_delegated,
    COVERAGE_YAML, load_yaml,
)
from run_cmd import append_command  # noqa: E402

# 「入力待ち」を表す終了コード（sysexits の EX_TEMPFAIL）。人が artifacts/ に置く入力
# （ログイン応答のヘッダ・保存した JS など）が無いとき、手順のコマンドが
# `test -s OUTDIR/<入力> || exit 75` で返す。失敗ではないので一括処理は止めず、
# 成功でもないので次回の --skip-done でも再実行される（置いた後に回せば続きが走る）。
PENDING_EXIT = 75


def select_steps(steps: list, only: str | None) -> list:
    """--only で手順を絞る（未指定なら「コマンド手順」を全部）。"""
    cmds = [s for s in steps if s["kind"] == "cmd"]
    if not only:
        return cmds
    wid, _, idx = only.partition(":")
    wid = wid.strip().upper()
    picked = [s for s in cmds if s["wid"] == wid and (not idx or str(s["idx"]) == idx)]
    return picked


def cmd_exit_code(activity_dir: Path, output_rel: str) -> int | None:
    """既存のコマンド出力ファイル末尾から exit_code を読む（無ければ None）。

    `--skip-done` の判定に使う。エビデンス（cmd/*.txt）そのものを真実とするので、
    run.yaml とは独立に「前回このコマンドが 0 で終わったか」を見られる。
    """
    path = activity_dir / output_rel
    if not path.exists():
        return None
    try:
        tail = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for line in reversed(tail):
        m = re.search(r"exit_code:\s*(-?\d+)", line)
        if m:
            return int(m.group(1))
    return None


def cmd_recorded(activity_dir: Path, output_rel: str) -> str | None:
    """既存のコマンド出力ファイルのヘッダから、前回実行したコマンド文字列を読む（無ければ None）。

    run_command が書く `$ <cmd>` 行から区切り線（`# ----`）までを取り出す。
    criteria.yaml の手順を直すと同じ出力パス（s<n>-c<k>）に別コマンドが割り当たるので、
    `--skip-done` は「exit_code 0」だけでなく「コマンドが今と同じ」ことも確かめる。
    """
    path = activity_dir / output_rel
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None
    for i, line in enumerate(lines):
        if line.startswith("$ "):
            body = [line[2:]]
            for rest in lines[i + 1:]:
                if rest.startswith("# " + "-" * 68):
                    break
                body.append(rest)
            return "\n".join(body)
    return None


def own_artifacts(activity_dir: Path, cmd: str) -> set:
    """コマンドが参照する、この活動フォルダの artifacts/ 直下のパス（ファイル/ディレクトリ）。

    他の活動フォルダ（`OUTDIR/../../<活動>-*/artifacts/...`）は含めない。
    """
    pat = re.escape(activity_dir.name) + r"/artifacts/([A-Za-z0-9_-][A-Za-z0-9._-]*)"
    return {activity_dir / "artifacts" / name for name in re.findall(pat, cmd)}


def is_done(activity_dir: Path, run: dict) -> bool:
    """前回このコマンドが（今と同じコマンドのまま）exit_code 0 で終わっていて、まだ新しいか。

    参照する artifacts/ のファイルが前回の出力より新しい（人が入力を置いた・前の手順を
    再実行した）ときは古い結果なので done とみなさない（make と同じ考え方）。
    """
    out = activity_dir / run["output"]
    if not (cmd_exit_code(activity_dir, run["output"]) == 0
            and cmd_recorded(activity_dir, run["output"]) == run["cmd"]):
        return False
    done_at = out.stat().st_mtime
    return all(not p.exists() or p.stat().st_mtime <= done_at
               for p in own_artifacts(activity_dir, run["cmd"]))


def write_pending(run: dict, step: dict, activity_dir: Path, waits_on: set) -> None:
    """入力待ちの手順に依存するコマンドを、実行せずに入力待ち（exit 75）として記録する。

    前回の（入力が無いまま走った）出力を残すと、成功扱いや古い結果の表示につながるので上書きする。
    """
    out_path = activity_dir / run["output"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    names = ", ".join(sorted(p.name for p in waits_on))
    out_path.write_text("\n".join([
        f"# {step['wid']} 手順{step['idx']} / {run['role']}",
        f"$ {run['cmd']}",
        "# " + "-" * 68,
        f"[run_activity] 入力待ち: {names} がまだ無いため実行していない（前の手順の入力を置いてから再実行する）",
        "# " + "-" * 68,
        f"# exit_code: {PENDING_EXIT}  duration_sec: 0.0",
    ]) + "\n", encoding="utf-8")


def execute_steps(run_yaml: Path, activity_dir: Path, todo: list, *,
                  timeout: int | None, skip_done: bool,
                  stop_on_error: bool) -> dict:
    """コマンド手順を順に実行する。集計 dict（ran/failed/skipped/pending/aborted/waiting）を返す。

    skip_done   … 前回 exit_code 0 で終わっているコマンドは再実行しない（再開用）。
                  手順を直してコマンドが変わったものは成功済みでも再実行する。
    stop_on_error … 非0終了が出たら、その時点で残りを実行せず打ち切る（aborted=True）。
    PENDING_EXIT（入力待ち）は非0終了に数えず止めない。その手順の残りのコマンドだけ飛ばし、
    どの出力が待っているかを waiting に積む。入力待ちのコマンドが参照するファイルを
    後続のコマンドが参照していれば、それも実行せず入力待ちにする（連鎖する）。
    """
    ran = failed = skipped = pending = 0
    waiting: list = []
    missing: set = set()   # 入力待ちで揃っていない artifacts/ のパス
    aborted = False

    def result() -> dict:
        return {"ran": ran, "failed": failed, "skipped": skipped, "pending": pending,
                "aborted": aborted, "waiting": waiting}

    for s in todo:
        print(f"\n===== {s['wid']} 手順{s['idx']}：{s['desc'][:60]} =====")
        for r in s["runs"]:
            refs = own_artifacts(activity_dir, r["cmd"])
            waits_on = refs & missing
            if waits_on:
                write_pending(r, s, activity_dir, waits_on)
                missing |= refs
                pending += 1
                waiting.append(f"{s['wid']} 手順{s['idx']}（{activity_dir / r['output']}）")
                print(f"[run_activity] 入力待ち: {s['wid']} 手順{s['idx']} は前の入力待ちの手順と同じ"
                      f"ファイル（{', '.join(sorted(p.name for p in waits_on))}）を使うため飛ばします")
                break
            if skip_done and is_done(activity_dir, r):
                skipped += 1
                print(f"[run_activity] スキップ（前回成功）: {r['output']}")
                continue
            if skip_done and cmd_exit_code(activity_dir, r["output"]) == 0:
                why = ("手順のコマンドが前回と変わった"
                       if cmd_recorded(activity_dir, r["output"]) != r["cmd"]
                       else "参照する artifacts/ のファイルが前回より新しい")
                print(f"[run_activity] {why}ため再実行: {r['output']}")
            entry = run_command(r, s, activity_dir, timeout)
            append_command(run_yaml, entry)
            ran += 1
            code = entry["exit_code"]
            if code == PENDING_EXIT:
                missing |= refs
                pending += 1
                waiting.append(f"{s['wid']} 手順{s['idx']}（{activity_dir / entry['output']}）")
                print(f"[run_activity] 入力待ち: {s['wid']} 手順{s['idx']} は人が artifacts/ に置く入力が"
                      f"まだ無いため飛ばします（手順の説明どおりに置いて再実行すると走ります）")
                break
            if code:
                failed += 1
            print(f"[run_activity] 保存: {activity_dir / entry['output']}  (exit={code}, {entry['duration_sec']}s)")
            if code and stop_on_error:
                aborted = True
                print(f"[run_activity] 非0終了（exit={code}）のため打ち切ります: {s['wid']} 手順{s['idx']}",
                      file=sys.stderr)
                return result()
    return result()


def run_command(run: dict, step: dict, activity_dir: Path, timeout: int | None) -> dict:
    """手順内の1コマンドをシェルで実行し、そのコマンド専用のファイルに出力を保存する。

    コマンドごとに別ファイル（cmd/<WSTG-ID>-s<n>-c<k>.txt）に落とすことで、
    record.html が「コマンドの説明→コマンド→その結果」を1対1で並べられる。
    """
    out_rel = run["output"]
    out_path = activity_dir / out_rel
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # 入力置き場として `OUTDIR/<name>/`（末尾スラッシュ＝ディレクトリ）を渡す手順
    # （retire --path OUTDIR/js/ 等）は、置き場が無いと失敗するので先に作っておく。
    for name in re.findall(r"artifacts/([A-Za-z0-9._-]+)/(?=[\s\"']|$)", run["cmd"]):
        (activity_dir / "artifacts" / name).mkdir(parents=True, exist_ok=True)
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
        if exit_code == PENDING_EXIT:
            fh.write("[run_activity] 入力待ち: 手順の説明どおりに artifacts/ へ入力を置いてから再実行する\n")
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
    ap.add_argument("--skip-done", action="store_true",
                    help="前回 exit_code 0 で終わったコマンドは再実行しない（再開。コマンドが変わったものは再実行）")
    ap.add_argument("--stop-on-error", action="store_true",
                    help="非0終了が出たらその時点で打ち切る（戻り値も非0）")
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
    # secondary（入力・補強）のコマンド手順は、その WSTG を primary で扱うアクティビティが
    # 別にある限り、そちらで1回だけ実行する（run_target と同じ委譲）。単体実行でも ffuf 等を
    # 二重に走らせないため、ここでも委譲する。委譲範囲は coverage.yaml 全体（＝どこかに primary が
    # あれば任せる）。--only で明示指定したときは、その手順を狙って実行したい意図を優先し委譲しない。
    if not args.only:
        owners = primary_owners(load_yaml(COVERAGE_YAML)["activities"])
        todo, delegated = split_delegated(todo, owners)
        for wid, acts in delegated.items():
            print(f"  （{wid} は secondary。コマンドは primary の {', '.join(acts)} で"
                  "実行するので、ここでは実行しない）")
    if not todo:
        print("実行するコマンド手順がありません（--only の指定か、手動手順のみ、"
              "または secondary で primary 側に委譲）。")
        print("  手順一覧は --list、手動手順は artifacts/manual-*.txt に観察を書いてください。")
        return 1

    if args.dry_run:
        for s in todo:
            print(f"[dry-run] {s['wid']}:{s['idx']}  {s['desc'][:70]}")
            for r in s["runs"]:
                print(f"    $ {r['cmd']}   -> {r['output']}")
        return 0

    run_yaml = activity_dir / "run.yaml"
    summary = execute_steps(run_yaml, activity_dir, todo, timeout=args.timeout,
                            skip_done=args.skip_done, stop_on_error=args.stop_on_error)

    refresh_record(activity_dir)
    skipped_note = f"、スキップ {summary['skipped']}" if summary["skipped"] else ""
    skipped_note += f"、入力待ち {summary['pending']}" if summary["pending"] else ""
    print(f"\n[run_activity] {summary['ran']} コマンドを実行"
          f"（うち非0終了 {summary['failed']}{skipped_note}）。evidence.js を更新しました。")
    print(f"  表示: {activity_dir / 'record.html'} をブラウザで開く")
    print(f"  判定: {run_yaml} の covers に verdict / finding を記入 → "
          f"uv run scripts/gen_record.py {activity_dir}")
    if summary["failed"]:
        print("  ※ 非0終了の手順は出力が空/失敗の可能性。cmd/*.txt を見て pass の根拠にしない。")
    # 打ち切ったときは戻り値を非0にして、呼び出し側（run_target.py 等）が止まれるようにする
    return 3 if summary["aborted"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
