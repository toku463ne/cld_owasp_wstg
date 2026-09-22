#!/usr/bin/env python3
"""CVSS v3.1 基本評価基準（Base）の計算と、新人向けの設問定義。

    uv run scripts/cvss31.py "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
    # -> 9.8 Critical（起こりやすさ 3.9 / 影響 5.9）

深刻度（Critical/High/Medium/Low/情報）は人が選ばず、ベクトルから機械的に出す。
スコアの内訳は「起こりやすさ」＝Exploitability（攻撃元・複雑さ・権限・ユーザ関与）と
「影響」＝Impact（機密性・完全性・可用性・スコープ）の2つで、どちらも根拠が
ベクトルの各指標として残る。計算式は FIRST の仕様書（CVSS v3.1 Specification 7.1〜7.4）どおり。
Web の所見ページはこのモジュールを /api/cvss 経由で呼ぶ（計算式を JS に二重実装しない）。
"""

from __future__ import annotations

import math
import sys

PREFIX = "CVSS:3.1"

# 指標の定義（順序＝ベクトルの並び）。q は新人向けの設問、options は (値, ラベル, 説明)。
METRICS = [
    {"key": "AV", "name": "攻撃元区分", "group": "起こりやすさ",
     "q": "攻撃者はどこから攻撃できるか？",
     "options": [
         ("N", "ネットワーク", "インターネット越しに攻撃できる。Web アプリの脆弱性はほぼこれ"),
         ("A", "隣接", "同じ LAN・Wi-Fi・VPN など、隣接したネットワークからのみ"),
         ("L", "ローカル", "対象機にログイン済み、または利用者にファイルを開かせる必要がある"),
         ("P", "物理", "機器に物理的に触れる必要がある"),
     ]},
    {"key": "AC", "name": "攻撃条件の複雑さ", "group": "起こりやすさ",
     "q": "攻撃者が準備すれば、毎回ほぼ確実に成功するか？",
     "options": [
         ("L", "低", "特別な条件は不要。同じリクエストを送れば再現する"),
         ("H", "高", "競合状態・中間者の位置取り・対象ごとの事前調査など、攻撃者の制御外の条件が要る"),
     ]},
    {"key": "PR", "name": "必要な特権レベル", "group": "起こりやすさ",
     "q": "攻撃の前に、対象システムへのログインが必要か？",
     "options": [
         ("N", "不要", "未ログイン（匿名）のまま攻撃できる"),
         ("L", "低", "一般ユーザのアカウントが必要"),
         ("H", "高", "管理者など強い権限のアカウントが必要"),
     ]},
    {"key": "UI", "name": "ユーザ関与", "group": "起こりやすさ",
     "q": "攻撃者以外の人（被害者）の操作が必要か？",
     "options": [
         ("N", "不要", "攻撃者だけで完結する"),
         ("R", "要", "被害者がリンクを開く・ページを見る・ボタンを押す等が必要（XSS・CSRF など）"),
     ]},
    {"key": "S", "name": "スコープ", "group": "影響",
     "q": "影響が、脆弱なコンポーネントの権限の外に及ぶか？",
     "options": [
         ("U", "変更なし", "影響はそのアプリ（同じ権限境界）の中に留まる。大半はこれ"),
         ("C", "変更あり", "別の権限境界に及ぶ（XSS で利用者のブラウザ上で実行、SSRF で内部の別システム、"
                         "コンテナ脱出など）"),
     ]},
    {"key": "C", "name": "機密性への影響", "group": "影響",
     "q": "攻撃者に読まれてしまう情報はどの程度か？",
     "options": [
         ("H", "高", "全データ、または認証情報・個人情報など重大な情報が読める"),
         ("L", "低", "一部の情報が読めるが、どれを読むかを攻撃者が選べない／重大ではない"),
         ("N", "なし", "読まれる情報はない"),
     ]},
    {"key": "I", "name": "完全性への影響", "group": "影響",
     "q": "攻撃者が改ざんできるものはどの程度か？",
     "options": [
         ("H", "高", "任意のデータを改ざんできる、または改ざんが重大な結果を招く"),
         ("L", "低", "一部を改ざんできるが、範囲が限られ重大ではない"),
         ("N", "なし", "改ざんはできない"),
     ]},
    {"key": "A", "name": "可用性への影響", "group": "影響",
     "q": "攻撃者がサービスを止められるか？",
     "options": [
         ("H", "高", "サービスを完全に止められる（継続的・または攻撃中ずっと）"),
         ("L", "低", "性能低下や一部機能の停止に留まる"),
         ("N", "なし", "止められない"),
     ]},
]
KEYS = [m["key"] for m in METRICS]
VALUES = {m["key"]: [o[0] for o in m["options"]] for m in METRICS}

W_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
W_AC = {"L": 0.77, "H": 0.44}
W_PR_U = {"N": 0.85, "L": 0.62, "H": 0.27}
W_PR_C = {"N": 0.85, "L": 0.68, "H": 0.5}
W_UI = {"N": 0.85, "R": 0.62}
W_CIA = {"H": 0.56, "L": 0.22, "N": 0.0}

# 深刻度（仕様書 5 章の Qualitative Severity Rating Scale）。None は「情報」と表示する。
SEVERITIES = [(9.0, "critical", "Critical"), (7.0, "high", "High"),
              (4.0, "medium", "Medium"), (0.1, "low", "Low"), (0.0, "none", "情報")]
EXPL_MAX = 3.9     # 起こりやすさ（Exploitability）の最大値（8.22*0.85*0.77*0.85*0.85 ≒ 3.887）
IMPACT_MAX = 6.1   # 影響（Impact）の最大値（S:C で約 6.05）


class CvssError(ValueError):
    pass


def roundup(x: float) -> float:
    """仕様書 Appendix A の Roundup（浮動小数の誤差を避ける版）。"""
    i = int(round(x * 100000))
    if i % 10000 == 0:
        return i / 100000.0
    return (math.floor(i / 10000) + 1) / 10.0


def parse(vector: str) -> dict:
    """ベクトル文字列を {指標: 値} に分解する。欠けや不正値は CvssError。"""
    v = (vector or "").strip()
    if not v:
        raise CvssError("ベクトルが空です")
    parts = v.split("/")
    if parts[0].startswith("CVSS:"):
        if parts[0] != PREFIX:
            raise CvssError(f"CVSS v3.1 のみ対応です（{parts[0]}）")
        parts = parts[1:]
    out: dict = {}
    for p in parts:
        k, _, val = p.partition(":")
        if k not in VALUES:
            raise CvssError(f"未知の指標: {k}（基本評価基準の {'/'.join(KEYS)} だけ書く）")
        if val not in VALUES[k]:
            raise CvssError(f"{k} の値が不正: {val}（{'/'.join(VALUES[k])} のどれか）")
        if k in out:
            raise CvssError(f"{k} が重複しています")
        out[k] = val
    missing = [k for k in KEYS if k not in out]
    if missing:
        raise CvssError(f"未選択の指標があります: {', '.join(missing)}")
    return out


def to_vector(metrics: dict) -> str:
    return PREFIX + "/" + "/".join(f"{k}:{metrics[k]}" for k in KEYS)


def severity(score: float) -> tuple:
    """(コード, 表示名) を返す。"""
    for lo, code, label in SEVERITIES:
        if score >= lo:
            return code, label
    return "none", "情報"


def score(vector: str) -> dict:
    """基本スコアと内訳を返す。

    返り値: vector（正規化済み）, base, severity, severity_label,
            exploitability（起こりやすさ 0〜3.9）, impact（影響 0〜6.1。負は 0 に丸める）
    """
    m = parse(vector)
    changed = m["S"] == "C"
    iss = 1 - (1 - W_CIA[m["C"]]) * (1 - W_CIA[m["I"]]) * (1 - W_CIA[m["A"]])
    if changed:
        impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15
    else:
        impact = 6.42 * iss
    pr = (W_PR_C if changed else W_PR_U)[m["PR"]]
    expl = 8.22 * W_AV[m["AV"]] * W_AC[m["AC"]] * pr * W_UI[m["UI"]]
    if impact <= 0:
        base = 0.0
    elif changed:
        base = roundup(min(1.08 * (impact + expl), 10))
    else:
        base = roundup(min(impact + expl, 10))
    code, label = severity(base)
    return {"vector": to_vector(m), "metrics": m, "base": base,
            "severity": code, "severity_label": label,
            "exploitability": round(expl, 1), "impact": round(max(impact, 0.0), 1)}


def try_score(vector: str):
    """空・不正なら None（未評価）。表示側の便利関数。"""
    try:
        return score(vector)
    except CvssError:
        return None


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0 if len(sys.argv) == 2 else 2
    try:
        r = score(sys.argv[1])
    except CvssError as exc:
        print(f"ベクトルが不正です: {exc}", file=sys.stderr)
        print("  例: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H", file=sys.stderr)
        return 2
    print(f"{r['base']} {r['severity_label']}（起こりやすさ {r['exploitability']} / 影響 {r['impact']}）")
    print(r["vector"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
