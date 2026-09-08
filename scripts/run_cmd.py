#!/usr/bin/env python3
"""CLI をログ付きで実行し、run.yaml の commands: に追記する。

    python scripts/run_cmd.py <activity_dir> -- <command...>

例:
    python scripts/run_cmd.py evidence/tls-scan-20260908 -- testssl.sh --quiet example.test
    python scripts/run_cmd.py evidence/http-methods-20260908 --slug options -- curl -sSI -X OPTIONS https://example.test/

やること:
  1. コマンドを実行し、stdout/stderr を <activity_dir>/cmd/<slug>.txt に保存（画面にもそのまま流す）
  2. <activity_dir>/run.yaml の commands: に、実行したコマンド行・出力パス・開始時刻・
     終了コード・所要秒を追記する

GUI ツール（Burp 等）はこのスクリプトの対象外。run.yaml の steps: に手記録すること。
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

MAX_SLUG = 48


def split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    """`--` の前後で自分の引数と実行コマンドを分ける。"""
    if "--" not in argv:
        return argv, []
    i = argv.index("--")
    return argv[:i], argv[i + 1 :]


def make_slug(command: list[str], explicit: str | None) -> str:
    if explicit:
        return re.sub(r"[^A-Za-z0-9._-]+", "-", explicit).strip("-")[:MAX_SLUG]
    parts = [Path(command[0]).name]
    for arg in command[1:]:
        if arg.startswith("-"):
            parts.append(arg.lstrip("-"))
        elif "://" not in arg and "/" not in arg and "." not in arg:
            parts.append(arg)
        if len("-".join(parts)) > MAX_SLUG:
            break
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", "-".join(p for p in parts if p)).strip("-")
    return (slug or "cmd")[:MAX_SLUG]


def unique_path(cmd_dir: Path, slug: str) -> Path:
    path = cmd_dir / f"{slug}.txt"
    n = 2
    while path.exists():
        path = cmd_dir / f"{slug}-{n}.txt"
        n += 1
    return path


def yaml_dq(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def append_command(run_yaml: Path, entry: dict) -> None:
    """run.yaml の commands: ブロック末尾に1件追記する（コメント・体裁は壊さない）。"""
    item = [
        f"  - cmd: {yaml_dq(entry['cmd'])}",
        f"    output: {entry['output']}",
        f"    started_at: {yaml_dq(entry['started_at'])}",
        f"    duration_sec: {entry['duration_sec']}",
        f"    exit_code: {entry['exit_code']}",
    ]

    lines = run_yaml.read_text(encoding="utf-8").splitlines()
    key_idx = next((i for i, l in enumerate(lines) if re.match(r"^commands\s*:", l)), None)

    if key_idx is None:  # commands: が無ければ末尾に作る
        lines += ["", "commands:"] + item
        run_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    if re.match(r"^commands\s*:\s*\[\s*\]\s*$", lines[key_idx]):  # `commands: []` を展開
        lines[key_idx] = "commands:"
        insert_at = key_idx + 1
    else:
        insert_at = key_idx + 1
        last_content = key_idx
        while insert_at < len(lines):
            line = lines[insert_at]
            if line.strip() == "":
                insert_at += 1
                continue
            if line.startswith((" ", "\t")):
                last_content = insert_at
                insert_at += 1
                continue
            break
        insert_at = last_content + 1

    lines[insert_at:insert_at] = item
    run_yaml.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    my_argv, command = split_argv(sys.argv[1:])
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, usage="%(prog)s <activity_dir> [options] -- <command...>"
    )
    ap.add_argument("activity_dir", help="evidence/<activity_id>-<yyyymmdd>")
    ap.add_argument("--slug", help="出力ファイル名（既定はコマンドから自動生成）")
    ap.add_argument("--note", help="この実行の目的を1行で run.yaml に残す")
    ap.add_argument("--timeout", type=int, help="秒。超えたら中断して記録する")
    ap.add_argument("--dry-run", action="store_true", help="実行せず、記録先だけ表示する")
    args = ap.parse_args(my_argv)

    if not command:
        ap.error("実行するコマンドを `--` の後ろに書いてください")

    activity_dir = Path(args.activity_dir)
    run_yaml = activity_dir / "run.yaml"
    if not run_yaml.exists():
        print(f"run.yaml が見つかりません: {run_yaml}", file=sys.stderr)
        print("  python scripts/new_activity.py <activity_id> で先に作成してください。", file=sys.stderr)
        return 2

    cmd_dir = activity_dir / "cmd"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    out_path = unique_path(cmd_dir, make_slug(command, args.slug))
    cmd_line = shlex.join(command)

    if args.dry_run:
        print(f"[dry-run] {cmd_line}\n[dry-run] -> {out_path}")
        return 0

    started = _dt.datetime.now().astimezone()
    t0 = time.monotonic()
    header = [
        f"# command : {cmd_line}",
        f"# cwd     : {Path.cwd()}",
        f"# started : {started.isoformat(timespec='seconds')}",
    ]
    if args.note:
        header.append(f"# note    : {args.note}")
    header.append("# " + "-" * 68)

    exit_code = None
    with out_path.open("w", encoding="utf-8", errors="replace") as fh:
        fh.write("\n".join(header) + "\n")
        fh.flush()
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", bufsize=1)
        except FileNotFoundError:
            fh.write(f"[run_cmd] コマンドが見つかりません: {command[0]}\n")
            print(f"コマンドが見つかりません: {command[0]}", file=sys.stderr)
            exit_code = 127
        except OSError as exc:
            fh.write(f"[run_cmd] 実行できません: {exc}\n")
            print(f"実行できません: {exc}", file=sys.stderr)
            exit_code = 126

        if exit_code is None:
            try:
                assert proc.stdout is not None
                for line in proc.stdout:  # 画面とファイルの両方へ
                    sys.stdout.write(line)
                    fh.write(line)
                exit_code = proc.wait(timeout=args.timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                fh.write(f"\n[run_cmd] timeout after {args.timeout}s\n")
                print(f"[run_cmd] タイムアウト（{args.timeout}s）", file=sys.stderr)
                exit_code = 124
            except KeyboardInterrupt:
                proc.terminate()
                proc.wait()
                fh.write("\n[run_cmd] interrupted by user\n")
                exit_code = 130

        duration = round(time.monotonic() - t0, 1)
        fh.write(f"# {'-' * 68}\n# exit_code: {exit_code}  duration_sec: {duration}\n")

    entry = {
        "cmd": cmd_line,
        "output": str(out_path.relative_to(activity_dir)),
        "started_at": started.isoformat(timespec="seconds"),
        "duration_sec": duration,
        "exit_code": exit_code,
    }
    append_command(run_yaml, entry)
    if args.note:
        print(f"[run_cmd] note: {args.note}")
    print(f"[run_cmd] 保存: {out_path}  (exit={exit_code}, {duration}s)")
    print(f"[run_cmd] 追記: {run_yaml}")
    return exit_code or 0


if __name__ == "__main__":
    raise SystemExit(main())
