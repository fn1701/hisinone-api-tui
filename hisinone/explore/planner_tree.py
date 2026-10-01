"""Baum des Studienplaners (PrimeFaces-TreeTable ``studyPlannerTree``) parsen.

Jede Zeile ist ein Knoten-Block ohne Spalten: Titel, eine Infozeile mit
unbeschrifteten Feldern ("Modul | 1.30.7122 | ... | 5 Credits") und Status-
Plaketten. Damit es auf jedem HISinOne passt, wird nichts nach Inhalt erraten:
die Infofelder werden nach Position zu Spalten "1", "2", ..., die Plaketten zu
"Status 1", "Status 2", ...
"""

import re

from .html_text import attribute, text_of
from .table_model import Row, TreeTable

ROW_START = re.compile(r'(?=<tr\b[^>]*\bdata-level=")')
LEVEL = re.compile(r'<tr\b[^>]*\bdata-level="(\d+)"')
TITLE = re.compile(r'class="unit-title-container[^"]*"[^>]*>(.*?)</div>', re.S)
INFO = re.compile(r'class="unit-information[^"]*"[^>]*>(.*?)</div>', re.S)
BADGE = re.compile(r'<[^>]*class="[^"]*\bbadge_character\b[^"]*"[^>]*>')
SEPARATOR = re.compile(r'<img\b[^>]*\balt="\|"[^>]*>')
NODE_KIND = re.compile(r'class="node-container StudyPlanner(\w+?)NodeData')
TITLE_COL = "Titel"
STATUS_COL = "Status"


def parse_planner_tree(html: str) -> list[TreeTable]:
    """Der Studienplaner-Baum als eine Tabelle ([] wenn keine Zeilen)."""
    rows = [_parse_row(part) for part in ROW_START.split(html) if LEVEL.match(part)]
    if not rows:
        return []
    return [TreeTable("Studienplaner", _columns(rows), rows, start_folded=True)]


def _parse_row(part: str) -> Row:
    """Zeile mit Titel, Infofeldern "1".."n" und Plaketten "Status 1".."m";
    "typ" (Knotenart aus dem Markup, z.B. Modul) nur intern."""
    row: Row = {"tiefe": int(LEVEL.match(part).group(1)) - 1}
    title = TITLE.search(part)
    row[TITLE_COL] = text_of(title.group(1)) if title else ""
    info = INFO.search(part)
    fields = [text_of(field) for field in SEPARATOR.split(info.group(1))] if info else []
    _numbered(row, "", [field for field in fields if field])
    badges = [attribute(tag, "title") for tag in BADGE.findall(part)]
    _numbered(row, f"{STATUS_COL} ", [badge for badge in badges if badge])
    kind = NODE_KIND.search(part)
    row["typ"] = kind.group(1) if kind else ""
    return row


def _numbered(row: Row, prefix: str, values: list[str]) -> None:
    for index, value in enumerate(values, start=1):
        row[f"{prefix}{index}"] = value


def _columns(rows: list[Row]) -> list[str]:
    """Titel, dann so viele Info- und Status-Spalten, wie es Werte gibt."""
    info = _count(rows, "")
    status = _count(rows, f"{STATUS_COL} ")
    cols = [TITLE_COL] + [str(index) for index in range(1, info + 1)]
    return cols + [f"{STATUS_COL} {index}" for index in range(1, status + 1)]


def _count(rows: list[Row], prefix: str) -> int:
    """Hoechste Nummer einer Spalte mit diesem Praefix in allen Zeilen."""
    count = 0
    for row in rows:
        while f"{prefix}{count + 1}" in row:
            count += 1
    return count
