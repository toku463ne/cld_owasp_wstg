#!/usr/bin/env python3
"""実施タスクリストの生成と、進捗の表示。

    uv run scripts/tasks.py            # 今の進捗と「次にやること」を表示
    uv run scripts/tasks.py --write    # TASKS.md を再生成（順序・フェーズの変更後）
    uv run scripts/tasks.py --check    # TASKS.md が最新か確認（selftest 用）

順序の元データは matrix/coverage.yaml の phases: と各アクティビティの
phase / order / depends_on / impact。進捗は evidence/*/run.yaml の verdict から判定する
（要約フィールドのみを読み、cmd/ や artifacts/ の中身は開かない）。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_YAML = REPO_ROOT / "matrix" / "coverage.yaml"
WSTG_TESTS = REPO_ROOT / "matrix" / "wstg_tests.yaml"
TASKS_MD = REPO_ROOT / "TASKS.md"
DEFAULT_EVIDENCE = REPO_ROOT / "evidence"

IMPACT_LABEL = {"low": "低", "medium": "中", "high": "高（要事前合意）"}
DONE, DOING, TODO = "完了", "実施中", "未着手"


def load(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"{path} がありません。README の「生成物を作り直すとき」を参照。")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sorted_activities(coverage: dict) -> list:
    acts = coverage["activities"]
    missing = [a["id"] for a in acts if "order" not in a or "phase" not in a]
    if missing:
        raise SystemExit(f"phase / order の無いアクティビティ: {', '.join(missing)}")
    return sorted(acts, key=lambda a: a["order"])


def scan_progress(evidence_root: Path, activity_ids: set[str]) -> dict:
    """evidence/*/run.yaml から、アクティビティごとの進捗を集計する。"""
    progress = {aid: {"state": TODO, "dirs": [], "done": 0, "total": 0} for aid in activity_ids}
    if not evidence_root.exists():
        return progress
    for run_yaml in sorted(evidence_root.glob("*/run.yaml")):
        try:
            data = yaml.safe_load(run_yaml.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        aid = data.get("activity_id")
        if aid not in progress:
            continue
        covers = [c for c in (data.get("covers") or []) if isinstance(c, dict)]
        done = sum(1 for c in covers if str(c.get("verdict", "todo")).lower() != "todo")
        p = progress[aid]
        p["dirs"].append(run_yaml.parent.name)
        p["done"] += done
        p["total"] += len(covers)
        p["state"] = DONE if (covers and done == len(covers)) else DOING
    return progress


def render_tasks_md(coverage: dict, tests: dict) -> str:
    phases = coverage.get("phases", {})
    acts = sorted_activities(coverage)
    out: list[str] = []
    w = out.append

    w("# 実施タスクリスト（上から順に消化する）")
    w("")
    w("> 自動生成: `uv run scripts/tasks.py --write`")
    w("> 順序・依存の元データは `matrix/coverage.yaml`。ここを直接編集しない。")
    w("")
    w(f"アクティビティ {len(acts)} 本で、WSTG v4.2 の実施対象 "
      f"{sum(1 for t in tests.values() if not t.get('deprecated'))} 項目をカバーする。")
    w("進捗は `uv run scripts/tasks.py` で確認できる。")
    w("")

    w("## フェーズ0 — 準備（1回だけ）")
    w("")
    w("- [ ] 対象・時間帯・禁止事項・連絡先を合意する（`impact: high` の項目は特に）")
    w("- [ ] ロールごとのテストアカウントを入手する")
    w("- [ ] `uv sync` — Python 環境を用意（uv が無い会社PCでは `pip install pyyaml`）")
    w("- [ ] `./scripts/selftest.sh` — ツールが動くことを確認")
    w("- [ ] （原文を読みたいとき）`./scripts/fetch_wstg.sh`")
    w("")

    current = None
    for a in acts:
        if a["phase"] != current:
            current = a["phase"]
            ph = phases.get(current, {})
            w(f"## フェーズ{current} — {ph.get('name', '')}")
            w("")
            if ph.get("goal"):
                w(ph["goal"])
                w("")
        deps = a.get("depends_on") or []
        covers = [c["id"] for c in a.get("covers", [])]
        w(f"### {a['order']}. `{a['id']}` — {a.get('title','')}")
        w("")
        w(a.get("summary", ""))
        w("")
        w(f"- 影響度: {IMPACT_LABEL.get(a.get('impact','low'), a.get('impact','low'))}"
          + (f" / 前提: {', '.join(f'`{d}`' for d in deps)}" if deps else " / 前提: なし"))
        w(f"- カード: {', '.join(f'[{c}](playbooks/{c}.md)' for c in covers)}")
        w("")
        w(f"- [ ] `uv run scripts/new_activity.py {a['id']}` でフォルダと run.yaml を作る")
        w(f"- [ ] カードを開いて手順と判定基準を確認する（{len(covers)} 項目）")
        tools = ", ".join(a.get("tools", []))
        w(f"- [ ] 収集を実行する（{tools}）")
        w(f"      - CLI: `uv run scripts/run_cmd.py evidence/{a['id']}-<yyyymmdd> -- <コマンド>`")
        w("      - GUI: 操作内容を `run.yaml` の `steps:` に手記録")
        w("- [ ] `run.yaml` の `covers:` に verdict と finding（要約のみ）を記入する")
        w("")

    w("## 仕上げ")
    w("")
    w("- [ ] `uv run scripts/tasks.py` で todo の残りが無いことを確認")
    w("- [ ] `uv run scripts/export_checklist.py --summary` で CSV を出力")
    w("- [ ] CSV を目視レビュー（機密が混じっていないか）")
    w("- [ ] Google Sheets へ取り込み（ファイル → インポート → 現在のシートを置換）")
    w("- [ ] `fail` の項目について報告書とカードの判定基準を見直す")
    w("")
    return "\n".join(out)


def show_progress(coverage: dict, evidence_root: Path) -> int:
    phases = coverage.get("phases", {})
    acts = sorted_activities(coverage)
    progress = scan_progress(evidence_root, {a["id"] for a in acts})

    if not evidence_root.exists():
        print(f"[情報] {evidence_root} がまだありません。すべて未着手として表示します。\n")

    current = None
    for a in acts:
        if a["phase"] != current:
            current = a["phase"]
            print(f"\nフェーズ{current} — {phases.get(current, {}).get('name', '')}")
        p = progress[a["id"]]
        detail = f"{p['done']}/{p['total']} 判定済み" if p["total"] else ""
        blockers = [d for d in (a.get("depends_on") or []) if progress[d]["state"] != DONE]
        if p["state"] == TODO and blockers:
            detail = "前提未完: " + ", ".join(blockers)
        mark = {DONE: "x", DOING: "~", TODO: " "}[p["state"]]
        print(f"  [{mark}] {a['order']:2d}. {a['id']:<26s} {p['state']:<4s} {detail}")

    ready = [
        a for a in acts
        if progress[a["id"]]["state"] != DONE
        and all(progress[d]["state"] == DONE for d in (a.get("depends_on") or []))
    ]
    done = sum(1 for a in acts if progress[a["id"]]["state"] == DONE)
    print(f"\n進捗: {done}/{len(acts)} アクティビティ完了")
    if ready:
        nxt = ready[0]
        print(f"次にやること: {nxt['order']}. {nxt['id']} — {nxt.get('title','')}")
        state = progress[nxt["id"]]["state"]
        if state == TODO:
            print(f"  uv run scripts/new_activity.py {nxt['id']}")
        else:
            print(f"  run.yaml の covers を埋める: evidence/{progress[nxt['id']]['dirs'][0]}/run.yaml")
        if len(ready) > 1:
            print(f"  （並行して着手可: {', '.join(a['id'] for a in ready[1:4])}）")
    else:
        print("すべて完了。仕上げへ: uv run scripts/export_checklist.py --summary")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="TASKS.md を生成する")
    ap.add_argument("--check", action="store_true", help="TASKS.md が最新か確認する")
    ap.add_argument("--root", default=str(DEFAULT_EVIDENCE), help="エビデンスのルート（既定: evidence/）")
    ap.add_argument("--out", default=str(TASKS_MD), help="TASKS.md の出力先")
    args = ap.parse_args()

    coverage = load(COVERAGE_YAML)
    tests = {t["id"]: t for t in load(WSTG_TESTS)["tests"]}

    if args.write or args.check:
        text = render_tasks_md(coverage, tests)
        out = Path(args.out)
        if args.check:
            same = out.exists() and out.read_text(encoding="utf-8") == text
            print("最新です" if same else "差分あり: uv run scripts/tasks.py --write を実行してください")
            return 0 if same else 1
        out.write_text(text, encoding="utf-8")
        print(f"{out.name} を生成: {len(coverage['activities'])} アクティビティ")
        return 0

    return show_progress(coverage, Path(args.root))


if __name__ == "__main__":
    raise SystemExit(main())
