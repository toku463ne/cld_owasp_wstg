"""WSTG 原文（Markdown 版 / HTML ミラー版）を解析する共通ライブラリ。

このモジュールは docs/owasp/ 配下の **公開情報のみ** を読む。
evidence 系のパスは名前で除外する（CLAUDE.md の境界を機械的にも守るため）。

標準ライブラリのみに依存する。
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs" / "owasp"

ID_RE = re.compile(r"WSTG-([A-Z]{4})-(\d{2})")

# 実案件データが紛れ込んでいても絶対に開かないためのブロックリスト。
BLOCKED_PARTS = {"evidence", "artifacts", "cmd", "recon"}
BLOCKED_SUFFIXES = {".xlsx", ".xls", ".csv", ".burp", ".har", ".pcap", ".zip"}

CATEGORY_NAMES = {
    "INFO": "Information Gathering",
    "CONF": "Configuration and Deployment Management",
    "IDNT": "Identity Management",
    "ATHN": "Authentication",
    "ATHZ": "Authorization",
    "SESS": "Session Management",
    "INPV": "Input Validation",
    "ERRH": "Error Handling",
    "CRYP": "Weak Cryptography",
    "BUSL": "Business Logic",
    "CLNT": "Client-side",
    "APIT": "API Testing",
}

CATEGORY_ORDER = list(CATEGORY_NAMES)

# v4.2 で他項目に統合された（＝単独では実施しない）テストの判定。
MERGED_RE = re.compile(r"content has been merged into:?\s*(.+?)(?:\.|$)", re.I)

SECTION_KEYS = {
    "summary": "summary",
    "test-objectives": "objectives",
    "test-objective": "objectives",
    "objectives": "objectives",
    "how-to-test": "how_to_test",
    "remediation": "remediation",
    "tools": "tools",
    "references": "references",
}


@dataclass
class WstgTest:
    id: str
    category: str
    number: str
    title: str
    source: str
    sections: dict = field(default_factory=dict)
    deprecated: bool = False
    merged_into: str = ""

    @property
    def category_name(self) -> str:
        return CATEGORY_NAMES.get(self.category, self.category)

    def section(self, key: str) -> str:
        return self.sections.get(key, "").strip()

    def sort_key(self):
        cat = CATEGORY_ORDER.index(self.category) if self.category in CATEGORY_ORDER else 99
        return (cat, self.number)


class _TextExtractor(HTMLParser):
    """WSTG のページ本文を、見出し単位のプレーンテキストに落とす。"""

    SKIP = {"script", "style", "nav", "header", "footer", "form", "svg"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[tuple[str, str]] = []  # (heading_id, text)
        self._heading = "_intro"
        self._buf: list[str] = []
        self._skip_depth = 0
        self._list_stack: list[str] = []
        self._li_index: list[int] = []
        self._in_h = None
        self._h_id = None
        self._h_text: list[str] = []
        self._in_pre = False

    # --- helpers -----------------------------------------------------
    def _flush_line(self, prefix: str = "") -> None:
        text = "".join(self._buf).strip()
        self._buf = []
        if text:
            self.blocks.append((self._heading, prefix + text))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.SKIP:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag in ("h1", "h2", "h3", "h4"):
            self._flush_line()
            self._in_h = tag
            self._h_id = attrs.get("id", "")
            self._h_text = []
        elif tag in ("ul", "ol"):
            self._flush_line()
            self._list_stack.append(tag)
            self._li_index.append(0)
        elif tag == "li":
            self._flush_line()
        elif tag == "p":
            self._flush_line()
        elif tag == "pre":
            self._flush_line()
            self._in_pre = True
        elif tag == "br":
            self._buf.append(" ")

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag in ("h1", "h2", "h3", "h4") and self._in_h == tag:
            title = " ".join("".join(self._h_text).split())
            if tag in ("h1", "h2"):
                # h2 が節の区切り。h3/h4 は直前の h2 節の中に留める。
                self._heading = self._h_id or title.lower().replace(" ", "-")
            elif title:
                self.blocks.append((self._heading, f"### {title}"))
            self._in_h = None
        elif tag in ("ul", "ol"):
            self._flush_line(self._bullet())
            if self._list_stack:
                self._list_stack.pop()
                self._li_index.pop()
        elif tag == "li":
            if self._li_index:
                self._li_index[-1] += 1
            self._flush_line(self._bullet())
        elif tag == "p":
            self._flush_line()
        elif tag == "pre":
            self._flush_line("`")
            self._in_pre = False

    def _bullet(self) -> str:
        if not self._list_stack:
            return ""
        depth = "  " * (len(self._list_stack) - 1)
        if self._list_stack[-1] == "ol":
            return f"{depth}{max(1, self._li_index[-1])}. "
        return f"{depth}- "

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_h:
            self._h_text.append(data)
            return
        if self._in_pre:
            self._buf.append(data.replace("\n", " "))
        else:
            self._buf.append(data)

    def close(self):
        super().close()
        self._flush_line()


def _is_blocked(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    if parts & BLOCKED_PARTS:
        return True
    return path.suffix.lower() in BLOCKED_SUFFIXES


def _parse_html(path: Path) -> WstgTest | None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    m = ID_RE.search(raw)
    if not m:
        return None
    # 本文は最初の `<h1 id=...>` 以降、サイト共通フッタ手前まで。
    start = raw.find("<h1 id=")
    if start < 0:
        return None
    end = raw.find('<h2><a href="../../index.html"', start)
    if end < 0:
        end = raw.find("</section>", start)
    body = raw[start : end if end > 0 else len(raw)]

    parser = _TextExtractor()
    parser.feed(body)
    parser.close()

    title = ""
    tm = re.search(r'<h1 id="[^"]*">(.*?)</h1>', body, re.S)
    if tm:
        title = " ".join(html.unescape(re.sub(r"<[^>]+>", "", tm.group(1))).split())

    sections: dict[str, list[str]] = {}
    for heading, text in parser.blocks:
        key = SECTION_KEYS.get(heading)
        if not key:
            continue
        if ID_RE.fullmatch(text.strip()) or text.strip() == "ID":
            continue
        sections.setdefault(key, []).append(text)

    merged = ""
    for _, text in parser.blocks:
        mm = MERGED_RE.search(text)
        if mm:
            merged = " ".join(mm.group(1).split())
            break

    return WstgTest(
        id=m.group(0),
        category=m.group(1),
        number=m.group(2),
        title=title,
        source=str(path.relative_to(REPO_ROOT)),
        sections={k: "\n".join(v) for k, v in sections.items()},
        deprecated=bool(merged) and not sections,
        merged_into=merged,
    )


def _parse_markdown(path: Path) -> WstgTest | None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    m = ID_RE.search(raw)
    if not m:
        return None

    title = ""
    for line in raw.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break

    sections: dict[str, list[str]] = {}
    current = None
    for line in raw.splitlines():
        if line.startswith("## "):
            slug = re.sub(r"[^a-z0-9]+", "-", line[3:].strip().lower()).strip("-")
            current = SECTION_KEYS.get(slug)
            continue
        if line.startswith("# "):
            current = None
            continue
        if current:
            stripped = line.rstrip()
            if stripped.startswith("|") or set(stripped) <= {"|", "-", " "} and stripped:
                continue
            if stripped:
                sections.setdefault(current, []).append(stripped)

    mm = MERGED_RE.search(raw)
    merged = " ".join(re.sub(r"[\[\]()]|\S+\.md", " ", mm.group(1)).split()) if mm else ""

    return WstgTest(
        id=m.group(0),
        category=m.group(1),
        number=m.group(2),
        title=title,
        source=str(path.relative_to(REPO_ROOT)),
        sections={k: "\n".join(v) for k, v in sections.items()},
        deprecated=bool(merged) and not sections,
        merged_into=merged,
    )


def load_tests(docs_root: Path | None = None) -> list[WstgTest]:
    """docs/owasp 配下から WSTG テスト定義を収集する。

    Markdown 版が見つかればそれを優先し、無ければ HTML ミラーを使う。
    """
    root = Path(docs_root) if docs_root else DOCS_ROOT
    if not root.exists():
        raise FileNotFoundError(
            f"WSTG 原文が見つかりません: {root}\n"
            "  ./scripts/fetch_wstg.sh を実行してください。"
        )

    found: dict[str, WstgTest] = {}
    seen_priority: dict[str, int] = {}
    for suffix, parser, priority in ((".md", _parse_markdown, 0), (".html", _parse_html, 1)):
        for path in sorted(root.rglob(f"*{suffix}")):
            if _is_blocked(path):
                continue
            if "4-Web_Application_Security_Testing" not in str(path):
                continue
            try:
                test = parser(path)
            except Exception:  # 壊れたファイルは無視して続行
                continue
            if not test or not test.title:
                continue
            prev = found.get(test.id)
            if prev is None or priority < seen_priority.get(test.id, 9):
                found[test.id] = test
                seen_priority[test.id] = priority
    return sorted(found.values(), key=lambda t: t.sort_key())


if __name__ == "__main__":  # 簡易確認用
    tests = load_tests()
    print(f"{len(tests)} tests")
    for t in tests[:5]:
        print(f"  {t.id}  {t.title}  <- {t.source}")
