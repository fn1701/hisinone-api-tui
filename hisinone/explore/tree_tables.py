"""Baum-Tabellen (``treeTableWithIcons``) parsen.

Leistungen, Vorlesungsverzeichnis usw. nutzen dasselbe Markup. Spalten werden
ueber colspan den Kopfzeilen zugeordnet (der Titel-Kopf ueberspannt z.B. auch
die Auf-/Zuklapp-Symbole).
"""

import re

from .custom_columns import add_custom_columns
from .html_text import attribute, text_of
from .table_model import Row, TreeTable

TREE_TABLE = re.compile(r'<table\b[^>]*class="[^"]*\btreeTableWithIcons\b[^"]*"[^>]*>')
ROW = re.compile(r'<tr\b[^>]*class="treeTableCellLevel(\d+)[^"]*"[^>]*>(.*?)</tr>', re.S)
HEADING = re.compile(r"<(h[1-6]|legend|caption)\b[^>]*>(.*?)</\1>", re.S)


def _colspan(tag: str) -> int:
    value = attribute(tag, "colspan") or "1"
    return int(value) if value.isdigit() else 1


def parse_tree_tables(html: str) -> list[TreeTable]:
    """Alle Baum-Tabellen der Seite (bzw. des Ajax-Fragments)."""
    starts = [match.start() for match in TREE_TABLE.finditer(html)]
    if not starts:
        return []
    ends = [*starts[1:], len(html)]
    tables = []
    for index, (start, end) in enumerate(zip(starts, ends, strict=True)):
        # Name = letzte Ueberschrift zwischen voriger Tabelle und dieser
        previous = starts[index - 1] if index else 0
        table = _parse_table(html[start:end], _last_heading(html[previous:start]))
        if table.rows:
            add_custom_columns(table)
            tables.append(table)
    return tables


def _last_heading(html: str) -> str:
    headings = HEADING.findall(html)
    return text_of(headings[-1][1]) if headings else ""


def _parse_table(segment: str, name: str) -> TreeTable:
    heads = _header_spans(segment)
    rows = [_parse_row(int(m.group(1)), m.group(2), heads) for m in ROW.finditer(segment)]
    if rows:  # Tiefe relativ zur flachsten Zeile
        base = min(row["tiefe"] for row in rows)
        for row in rows:
            row["tiefe"] -= base
    return TreeTable(name, [head for _, _, head in heads], rows)


def _header_spans(segment: str) -> list[tuple[int, int, str]]:
    """[(erste Zellposition, Ende, Kopftext)] der ersten Zeile (mit colspan)."""
    first_row = re.search(r"<tr\b[^>]*>(.*?)</tr>", segment, re.S)
    heads, position = [], 0
    for tag, inner in re.findall(r"(<th\b[^>]*>)(.*?)</th>", first_row.group(1) if first_row
                                 else "", re.S):  # fmt: skip
        width = _colspan(tag)
        heads.append((position, position + width, text_of(inner) or f"Spalte {len(heads) + 1}"))
        position += width
    return heads


def _parse_row(depth: int, row_html: str, heads: list[tuple[int, int, str]]) -> Row:
    row: Row = {"tiefe": depth, "typ": ""}
    position = 0
    for tag, inner in re.findall(r"(<td\b[^>]*>)(.*?)</td>", row_html, re.S):
        col = next((head for start, end, head in heads if start <= position < end), None)
        position += _colspan(tag)
        if not row["typ"]:  # Typ = alt-Text des ersten Symbols (Modul, Konto, ...)
            icon = re.search(r'<img\b[^>]*\balt="([^"]+)"', inner)
            row["typ"] = icon.group(1) if icon else ""
        text = text_of(inner)
        if col and text:
            row[col] = f"{row[col]} {text}" if row.get(col) else text
    return row
