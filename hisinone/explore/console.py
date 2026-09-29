"""Ausgabe im Terminal (Kommandozeilen-Werkzeuge)."""

import sys
from urllib.parse import urlsplit, urlunsplit

from .columns import COL_LABEL, DEFAULT_COLS
from .link_tree import TreeEntry
from .links import Link
from .table_model import Row


def hyperlink(text: str, url: str) -> str:
    """OSC-8-Terminal-Link: der Text ist klickbar und traegt die volle URL,
    egal wie das Terminal umbricht (tmux: terminal-features "*:hyperlinks")."""
    if not sys.stdout.isatty():
        return text
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def short_url(url: str, host: str) -> str:
    """Pfad + Query fuer Links auf demselben Server, sonst die volle URL."""
    parts = urlsplit(url)
    return url if parts.netloc != host else urlunsplit(("", "", parts.path, parts.query, ""))


def _marks(link: Link, host: str) -> str:
    marks = ""
    if urlsplit(link.url).netloc != host:
        marks += "[ext] "
    elif link.flow_bound:
        marks += "[flow] "
    if link.is_logout:
        marks += "[LOGOUT] "
    return marks


def show_links(entries: list[TreeEntry], host: str, text_filter: str) -> None:
    """Nummerierte Liste; Nummer = Position in entries (1-basiert).
    Gruppen-Ueberschriften nur ohne Filter."""
    for number, entry in enumerate(entries, 1):
        link = entry.link
        if link is None:
            if not text_filter:
                print(f"\n      {entry.label}")
            continue
        if text_filter not in link.label.casefold() and text_filter not in link.url.casefold():
            continue
        label = "  " * entry.depth + link.label
        url_text = hyperlink(short_url(link.url, host), link.url)
        print(f"{number:4}  {_marks(link, host)}{label[:60]:60}  {url_text}")


def print_leistungen(rows: list[Row], cols: list[str] | None = None, tree: bool = True) -> None:
    """Als Tabelle mit festen Spaltenbreiten (max. 60 Zeichen)."""
    cols = cols or DEFAULT_COLS
    cells = [[_cell(row, col, tree) for col in cols] for row in rows]
    widths = [min(60, max([len(COL_LABEL[col])] + [len(line[i]) for line in cells]))
              for i, col in enumerate(cols)]  # fmt: skip
    print("  ".join(f"{COL_LABEL[c]:{w}}" for c, w in zip(cols, widths, strict=True)))
    for line in cells:
        print("  ".join(f"{v[:w]:{w}}" for v, w in zip(line, widths, strict=True)))


def _cell(row: Row, col: str, tree: bool) -> str:
    indent = "  " * (row["tiefe"] - 1) if tree and col == "titel" else ""
    return indent + str(row.get(col, ""))
