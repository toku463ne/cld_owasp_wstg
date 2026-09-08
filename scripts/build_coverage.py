#!/usr/bin/env python3
"""matrix/coverage.yaml の `activities:` から、双方向インデックスと coverage.md を生成する。

    python scripts/build_coverage.py           # 生成
    python scripts/build_coverage.py --check   # 差分・不整合の確認のみ

手で編集するのは coverage.yaml の `activities:` ブロックだけ。
自動生成マーカー以降（by_activity / by_wstg / unassigned）は毎回書き換わる。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
COVERAGE_YAML = REPO_ROOT / "matrix" / "coverage.yaml"
COVERAGE_MD = REPO_ROOT / "matrix" / "coverage.md"
WSTG_TESTS = REPO_ROOT / "matrix" / "wstg_tests.yaml"

MARKER = "# === ここから下は scripts/build_coverage.py が自動生成（手で編集しない） ==="


def load_wstg_tests() -> dict:
    if not WSTG_TESTS.exists():
        raise SystemExit(
            f"{WSTG_TESTS} がありません。先に python scripts/build_wstg_index.py を実行してください。"
        )
    data = yaml.safe_load(WSTG_TESTS.read_text(encoding="utf-8"))
    return {t["id"]: t for t in data["tests"]}


def load_activities() -> list:
    data = yaml.safe_load(COVERAGE_YAML.read_text(encoding="utf-8"))
    acts = data.get("activities") or []
    if not acts:
        raise SystemExit("coverage.yaml に activities: がありません。")
    return acts


def build_indexes(activities: list, tests: dict):
    by_activity: dict[str, dict[str, list[str]]] = {}
    by_wstg: dict[str, dict[str, list[str]]] = {t: {"primary": [], "secondary": []} for t in tests}
    problems: list[str] = []

    seen_ids = set()
    for act in activities:
        aid = act["id"]
        if aid in seen_ids:
            problems.append(f"activity id が重複: {aid}")
        seen_ids.add(aid)
        entry = {"primary": [], "secondary": []}
        for cov in act.get("covers", []):
            wid, role = cov["id"], cov.get("role", "primary")
            if wid not in tests:
                problems.append(f"{aid}: 未知の WSTG-ID {wid}")
                continue
            if role not in ("primary", "secondary"):
                problems.append(f"{aid}/{wid}: 不正な role {role}")
                role = "secondary"
            entry[role].append(wid)
            by_wstg[wid][role].append(aid)
        by_activity[aid] = entry

    return by_activity, by_wstg, problems


def render_yaml_tail(by_activity, by_wstg, tests) -> str:
    def flow(items):
        return "[" + ", ".join(items) + "]" if items else "[]"

    lines = [MARKER, "", "by_activity:"]
    for aid, roles in by_activity.items():
        lines.append(f"  {aid}:")
        lines.append(f"    primary: {flow(roles['primary'])}")
        lines.append(f"    secondary: {flow(roles['secondary'])}")

    lines.append("")
    lines.append("by_wstg:")
    for wid, roles in by_wstg.items():
        if tests[wid].get("deprecated") and not (roles["primary"] or roles["secondary"]):
            continue
        lines.append(f"  {wid}:")
        lines.append(f"    primary: {flow(roles['primary'])}")
        lines.append(f"    secondary: {flow(roles['secondary'])}")

    unassigned = [w for w, r in by_wstg.items() if not r["primary"] and not r["secondary"]]
    no_primary = [w for w, r in by_wstg.items() if not r["primary"] and r["secondary"]]
    deprecated = [w for w, t in tests.items() if t.get("deprecated")]

    lines.append("")
    lines.append("# どのアクティビティにも割り当てられていない WSTG-ID")
    lines.append(f"unassigned: {flow(unassigned)}")
    lines.append("# secondary でしか触れられていない＝単独では判定を確定できない WSTG-ID")
    lines.append(f"no_primary: {flow(no_primary)}")
    lines.append("# v4.2 で他項目に統合された WSTG-ID（単独では実施しない）")
    lines.append(f"deprecated: {flow(deprecated)}")
    return "\n".join(lines) + "\n"


def render_md(activities, by_activity, by_wstg, tests) -> str:
    act_by_id = {a["id"]: a for a in activities}
    out: list[str] = []
    w = out.append

    w("# カバレッジマトリクス（アクティビティ × WSTG）")
    w("")
    w("> 自動生成: `python scripts/build_coverage.py`（元データは `matrix/coverage.yaml` の `activities:`）")
    w("")
    active_tests = [t for t in tests.values() if not t.get("deprecated")]
    covered = [w_ for w_, r in by_wstg.items() if r["primary"] and not tests[w_].get("deprecated")]
    w(f"- アクティビティ数: **{len(activities)}**")
    w(f"- WSTG 実施対象: **{len(active_tests)}** 件（v4.2 全 {len(tests)} 件 − 統合済み {len(tests) - len(active_tests)} 件）")
    w(f"- primary でカバー済み: **{len(covered)}** 件")
    w("")
    w("`primary` はそのアクティビティ単独で判定まで到達できるもの、`secondary` は入力・補強にとどまるもの。")
    w("")

    w("## 1. アクティビティ → WSTG-ID")
    w("")
    w("| activity_id | 概要 | 主なツール | primary | secondary |")
    w("|---|---|---|---|---|")
    for a in activities:
        roles = by_activity[a["id"]]
        tools = ", ".join(a.get("tools", []))
        w(
            f"| `{a['id']}` | {a.get('title','')} | {tools} | "
            f"{', '.join(roles['primary']) or '—'} | {', '.join(roles['secondary']) or '—'} |"
        )
    w("")

    w("## 2. WSTG-ID → アクティビティ")
    w("")
    current_cat = None
    for wid, t in tests.items():
        if t.get("deprecated"):
            continue
        if t["category"] != current_cat:
            current_cat = t["category"]
            w("")
            w(f"### {current_cat} — {t['category_name']}")
            w("")
            w("| WSTG-ID | テスト名 | primary アクティビティ | secondary |")
            w("|---|---|---|---|")
        roles = by_wstg[wid]
        w(
            f"| {wid} | {t['title']} | "
            f"{', '.join(f'`{a}`' for a in roles['primary']) or '**未割当**'} | "
            f"{', '.join(f'`{a}`' for a in roles['secondary']) or '—'} |"
        )
    w("")

    w("## 3. アクティビティ詳細")
    w("")
    for a in activities:
        w(f"### `{a['id']}` — {a.get('title','')}")
        w("")
        w(a.get("summary", ""))
        w("")
        if a.get("tools"):
            w(f"- ツール: {', '.join(a['tools'])}")
        if a.get("outputs"):
            w(f"- 想定成果物: {', '.join(f'`{o}`' for o in a['outputs'])}")
        w("- カバー:")
        for cov in a.get("covers", []):
            t = tests.get(cov["id"], {})
            note = f" — {cov['note']}" if cov.get("note") else ""
            w(f"  - {cov['id']} ({cov.get('role','primary')}) {t.get('title','')}{note}")
        w("")

    w("## 4. 未割当リスト")
    w("")
    unassigned = [x for x, r in by_wstg.items() if not r["primary"] and not r["secondary"]]
    no_primary = [x for x, r in by_wstg.items() if not r["primary"] and r["secondary"]]
    deprecated = [x for x, t in tests.items() if t.get("deprecated")]

    if unassigned:
        w("どのアクティビティにも割り当てられていない項目（アクティビティの追加が必要）:")
        w("")
        for x in unassigned:
            flag = "（統合済み）" if tests[x].get("deprecated") else ""
            w(f"- {x} — {tests[x]['title']}{flag}")
    else:
        w("どのアクティビティにも割り当てられていない実施対象の項目は **なし**。")
    w("")

    if no_primary:
        w("secondary のみでカバーされている項目（単独判定には別アクティビティが要る）:")
        w("")
        for x in no_primary:
            w(f"- {x} — {tests[x]['title']}: {', '.join(by_wstg[x]['secondary'])}")
        w("")

    w("v4.2 で他項目に統合され、単独では実施しない項目:")
    w("")
    for x in deprecated:
        w(f"- {x} — {tests[x]['title']} → {tests[x].get('merged_into','')}")
    w("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="書き込まず、不整合と差分のみ報告する")
    args = ap.parse_args()

    tests = load_wstg_tests()
    activities = load_activities()
    by_activity, by_wstg, problems = build_indexes(activities, tests)

    for p in problems:
        print(f"[NG] {p}", file=sys.stderr)

    head = COVERAGE_YAML.read_text(encoding="utf-8").split(MARKER)[0].rstrip() + "\n\n"
    new_yaml = head + render_yaml_tail(by_activity, by_wstg, tests)
    new_md = render_md(activities, by_activity, by_wstg, tests)

    if args.check:
        drift = (
            COVERAGE_YAML.read_text(encoding="utf-8") != new_yaml
            or not COVERAGE_MD.exists()
            or COVERAGE_MD.read_text(encoding="utf-8") != new_md
        )
        print("差分あり: python scripts/build_coverage.py を実行してください" if drift else "最新です")
        return 1 if (drift or problems) else 0

    COVERAGE_YAML.write_text(new_yaml, encoding="utf-8")
    COVERAGE_MD.write_text(new_md, encoding="utf-8")
    unassigned = [x for x, r in by_wstg.items() if not r["primary"] and not r["secondary"]]
    print(
        f"coverage.yaml / coverage.md を生成: アクティビティ {len(activities)} 件 / "
        f"未割当 {len(unassigned)} 件"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
