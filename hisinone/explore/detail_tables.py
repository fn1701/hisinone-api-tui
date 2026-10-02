"""Tabellen einer Detailseite (z.B. "Veranstaltungen und Prüfungen") als
Markdown-Tabellen. In Baum-Tabellen sind Zellen ohne Text nur Symbole und
fallen weg; der Detail-Link einer Zeile wird zum anklickbaren ◆, Kopfzeilen
bleiben reiner Text (ohne Sortier-Knöpfe)."""

import re
from urllib.parse import urljoin

from .html_text import attribute, text_of

# innerste Tabellen (die äußere ist nur ein Rahmen ohne Kopfzeile)
INNER_TABLE = re.compile(r"<table\b(?:(?!<table\b).)*?</table>", re.S)
ROW = re.compile(r"<tr\b.*?</tr>", re.S)
CELL = re.compile(r"<t([hd])\b[^>]*>(.*?)</t\1>", re.S)
LINK = re.compile(r'<a\b[^>]*\bhref="[^"#][^"]*"[^>]*>')  # ohne "#" (nur Skript)
SORT_HINT = re.compile(r"\s*(\[Sortierbare Spalte\]|(Auf|Ab)w\u00e4rts sortieren)")
LIST_END = re.compile(r"</li>")  # Aufzählung in einer Zelle: mit Komma
LINK_MARK = "◆"
MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")


def replace_tables(fragment: str, tables: list[str]) -> str:
    """Ersetzt jede Tabelle mit Kopfzeile durch einen Platzhalter
    (\\x00Nummer\\x00) und hängt ihr Markdown an tables an."""
    while match := _next_table(fragment):
        tables.append(table_markdown(match.group(0)))
        marker = f"\n\n\x00{len(tables) - 1}\x00\n\n"
        fragment = fragment[: match.start()] + marker + fragment[match.end() :]
    return fragment


def _next_table(fragment: str) -> re.Match | None:
    for match in INNER_TABLE.finditer(fragment):
        if "<th" in match.group(0):
            return match
    return None


def table_markdown(table: str) -> str:
    """Kopfzeile aus den <th>, Datenzeilen auf deren Spaltenzahl gebracht."""
    tree = "treeTable" in table[: table.find(">")]
    rows = [cells for cells in (_cells(row, tree) for row in ROW.findall(table)) if any(cells)]
    if not rows:
        return ""
    header, width = rows[0], len(rows[0])
    lines = [_line(header), _line(["---"] * width)]
    for cells in rows[1:]:
        lines.append(_line((cells + [""] * width)[:width]))
    return "\n".join(lines)


def _cells(row: str, tree: bool) -> list[str]:
    """Texte der Zellen; Links werden ◆, im Baum fallen leere Zellen weg."""
    cells = []
    for kind, content in CELL.findall(row):
        text = text_of(LIST_END.sub(", ", content)).rstrip(", ")
        if kind == "h":
            text = SORT_HINT.sub("", text)
        elif link := LINK.search(content):
            href = attribute(link.group(0), "href")
            text = f"{text} [{LINK_MARK}]({href})".strip()
        if text or not tree:
            cells.append(text)
    return cells


def insert_tables(text: str, tables: list[str]) -> str:
    """Platzhalter von replace_tables wieder durch die Tabellen ersetzen."""
    for index, table in enumerate(tables):
        text = text.replace(f"\x00{index}\x00", table)
    return text


def _line(cells: list[str]) -> str:
    return "| " + " | ".join(cell.replace("|", "\\|") for cell in cells) + " |"


def absolute_links(markdown: str, base: str) -> str:
    """Relative Link-Ziele absolut machen: Terminal (Strg+Klick) und Export
    kennen die Seite nicht und würden sonst file:///qisserver/... öffnen."""

    def _absolute(match: re.Match[str]) -> str:
        return f"]({urljoin(base, match.group(1))})"

    return MARKDOWN_LINK.sub(_absolute, markdown)
