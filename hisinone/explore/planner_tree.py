"""Baum des Studienplaners (PrimeFaces-TreeTable ``studyPlannerTree``) parsen.

Jede Zeile ist ein Knoten-Block ohne Spalten: Titel, eine Infozeile mit
unbeschrifteten Feldern ("Modul | 1.30.7122 | ... | 5 Credits") und Status-
Plaketten. Damit es auf jedem HISinOne passt, wird nichts nach Inhalt erraten:
die Infofelder werden nach Position zu Spalten "1", "2", ..., die Plaketten zu
"Status 1", "Status 2", ...
"""

import re
from collections.abc import Callable

from .html_text import attribute, text_of
from .table_model import Row, TreeTable

ROW_START = re.compile(r'(?=<tr\b[^>]*\bdata-level=")')
LEVEL = re.compile(r'<tr\b[^>]*\bdata-level="(\d+)"')
TITLE = re.compile(r'class="unit-title-container[^"]*"[^>]*>(.*?)</div>', re.S)
INFO = re.compile(r'class="unit-information[^"]*"[^>]*>(.*?)</div>', re.S)
BADGE = re.compile(r'<[^>]*class="[^"]*\bbadge_character\b[^"]*"[^>]*>')
SEPARATOR = re.compile(r'<img\b[^>]*\balt="\|"[^>]*>')
DETAIL_LINK = re.compile(r'<a\b[^>]*\bid="[^"]*:showFurtherDetailsButton:link"[^>]*>')
NODE_KIND = re.compile(r'class="node-container StudyPlanner(\w+?)NodeData')
TITLE_COL = "Titel"
ColumnName = Callable[[int], str]  # Position (ab 1) -> Spaltenname


def parse_planner_tree(html: str) -> list[TreeTable]:
    """Der Studienplaner-Baum als eine Tabelle ([] wenn keine Zeilen)."""
    rows = [_parse_row(part) for part in ROW_START.split(html) if LEVEL.match(part)]
    if not rows:
        return []
    return [TreeTable("Studienplaner", _columns(rows), rows, start_folded=True)]


def _parse_row(part: str) -> Row:
    """Zeile mit Titel, Infofeldern "1".."n" und Plaketten "Status 1".."m";
    "typ" (Knotenart aus dem Markup, z.B. Modul) und "url" (Detailseite,
    relativ zur Seite) nur intern."""
    row: Row = {"tiefe": int(LEVEL.match(part).group(1)) - 1}
    title = TITLE.search(part)
    row[TITLE_COL] = text_of(title.group(1)) if title else ""
    info = INFO.search(part)
    fields = [text_of(field) for field in SEPARATOR.split(info.group(1))] if info else []
    _numbered(row, [field for field in fields if field], _info_name)
    badges = [attribute(tag, "title") for tag in BADGE.findall(part)]
    _numbered(row, [badge for badge in badges if badge], _badge_name)
    kind = NODE_KIND.search(part)
    row["typ"] = kind.group(1) if kind else ""
    link = DETAIL_LINK.search(part)
    row["url"] = attribute(link.group(0), "href") if link else ""
    return row


def _numbered(row: Row, values: list[str], name: ColumnName) -> None:
    for index, value in enumerate(values, start=1):
        row[name(index)] = value


def _info_name(index: int) -> str:
    """Info-Felder nach Position: 1, 2, 3, ..."""
    return str(index)


def _badge_name(index: int) -> str:
    """Badges nach Position: A, B, ..., Z, AA, AB, ... (wie Tabellenspalten)."""
    name = ""
    while index:
        index, rest = divmod(index - 1, 26)
        name = chr(ord("A") + rest) + name
    return name


def _columns(rows: list[Row]) -> list[str]:
    """Titel, dann so viele Info- und Badge-Spalten, wie es Werte gibt."""
    info = [_info_name(index) for index in range(1, _count(rows, _info_name) + 1)]
    badges = [_badge_name(index) for index in range(1, _count(rows, _badge_name) + 1)]
    return [TITLE_COL] + info + badges


def _count(rows: list[Row], name: ColumnName) -> int:
    """Hoechste Position einer Spalte dieser Art in allen Zeilen."""
    count = 0
    for row in rows:
        while name(count + 1) in row:
            count += 1
    return count
