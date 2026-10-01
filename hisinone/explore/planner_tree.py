"""Baum des Studienplaners (PrimeFaces-TreeTable ``studyPlannerTree``) parsen.

Anders als ``treeTableWithIcons`` hat jede Zeile keine Spalten, sondern einen
Knoten-Block: Infozeile ("Modul | Nummer | Pflichtfach | empf. ... | x von y
Credits"), Titel und Status-Plaketten. Die Infofelder werden nach Inhalt den
Spalten zugeordnet, weil ihre Anzahl je Knotentyp schwankt.
"""

import re

from .html_text import attribute, text_of
from .table_model import Row, TreeTable

PLANNER_COLS = ["Titel", "Typ", "Nummer", "Pflicht", "empf. FS", "Credits", "Details", "Status"]
ROW_START = re.compile(r'(?=<tr\b[^>]*\bdata-level=")')
LEVEL = re.compile(r'<tr\b[^>]*\bdata-level="(\d+)"')
TITLE = re.compile(r'class="unit-title-container[^"]*"[^>]*>(.*?)</div>', re.S)
INFO = re.compile(r'class="unit-information[^"]*"[^>]*>(.*?)</div>', re.S)
BADGE = re.compile(r'<[^>]*class="[^"]*\bbadge_character\b[^"]*"[^>]*>')
SEPARATOR = re.compile(r'<img\b[^>]*\balt="\|"[^>]*>')
NODE_KIND = re.compile(r'class="node-container StudyPlanner(\w+?)NodeData')
UNIQUE_NAME = re.compile(r"\(Eindeutige Bezeichnung:[^)]*\)")


def parse_planner_tree(html: str) -> list[TreeTable]:
    """Der Studienplaner-Baum als eine Tabelle ([] wenn keine Zeilen)."""
    rows = [_parse_row(part) for part in ROW_START.split(html) if LEVEL.match(part)]
    if not rows:
        return []
    return [TreeTable("Studienplaner", list(PLANNER_COLS), rows, start_folded=True)]


def _parse_row(part: str) -> Row:
    row: Row = {"tiefe": int(LEVEL.match(part).group(1)) - 1}
    title = TITLE.search(part)
    row["Titel"] = text_of(title.group(1)) if title else ""
    info = INFO.search(part)
    row.update(_info_fields(info.group(1) if info else ""))
    if not row.get("Typ"):  # Termin-Knoten haben keine Infozeile mit Typ
        kind = NODE_KIND.search(part)
        row["Typ"] = kind.group(1).replace("VeranstaltungPlanelement", "Termine") if kind else ""
    row["typ"] = row["Typ"]
    badges = [attribute(tag, "title") for tag in BADGE.findall(part)]
    row["Status"] = ", ".join(badge for badge in badges if badge)
    return row


def _info_fields(info_html: str) -> dict[str, str]:
    """Infofelder nach Inhalt: erstes = Typ, zweites = Nummer, Rest erkannt
    (Pflicht, empfohlenes Fachsemester, Credits) oder unter Details."""
    fields = [text_of(field) for field in SEPARATOR.split(UNIQUE_NAME.sub("", info_html))]
    fields = [field for field in fields if field]
    if len(fields) < 2:  # z.B. "Veranstaltungstermine im Winter 2026/27"
        return {"Details": fields[0]} if fields else {}
    result = {"Typ": fields[0], "Nummer": fields[1]}
    details = []
    for field in fields[2:]:
        column = _column_of(field)
        if column:
            result[column] = _short(column, field)
        else:
            details.append(field)
    result["Details"] = ", ".join(details)
    return result


def _column_of(field: str) -> str:
    if field.startswith("empf."):
        return "empf. FS"
    if field.endswith("Credits"):
        return "Credits"
    if field.endswith("fach"):  # Pflichtfach, Wahlpflichtfach, ...
        return "Pflicht"
    return ""


def _short(column: str, field: str) -> str:
    """Kurzform fuer schmale Spalten: "empf. fuer das 2. Fachsemester" -> "2"."""
    if column == "empf. FS":
        number = re.search(r"\d+", field)
        return number.group(0) if number else field
    return field.removesuffix(" Credits") if column == "Credits" else field
