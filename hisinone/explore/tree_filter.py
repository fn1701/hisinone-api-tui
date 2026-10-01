"""Zeilenfilter fuer Baum-Tabellen: eine Zeile passt, wenn der Filter auf sie
samt ihren Eltern passt (so gilt ein Treffer im Modul fuer alles darunter,
und "enthaelt nicht" blendet ganze Teilbaeume aus). Gezeigt werden die
Treffer und, als Zusammenhang, ihre Eltern.

Zwei Arten: normal ("Text" / "Spalte=Wert", siehe row_filter) oder ein
regulaerer Ausdruck (Python ``re``, Gross-/Kleinschreibung egal) auf der
Zeile als Text "Spalte=Wert | Spalte=Wert | ...", Eltern davor.
"""

import re
from collections.abc import Callable

from .row_filter import parse_checks
from .table_model import Row

PathTest = Callable[[list[Row]], bool]  # Zeile mit Eltern (Wurzel zuerst) -> passt?


def filter_tree(rows: list[Row], cols: list[str], query: str, regex: bool) -> list[Row]:
    """Treffer plus Eltern in Baum-Reihenfolge; regex=True: re.error bei
    ungueltigem Ausdruck (der Aufrufer zeigt dann das alte Ergebnis)."""
    test: PathTest = _RegexTest(cols, query) if regex else _TermsTest(cols, query)
    keep = [False] * len(rows)
    path: list[int] = []  # Indizes der Eltern und der Zeile selbst
    for index, row in enumerate(rows):
        del path[row.get("tiefe", 0) :]
        path.append(index)
        if test([rows[step] for step in path]):
            for step in path:
                keep[step] = True
    return [row for row, kept in zip(rows, keep, strict=True) if kept]


def row_line(row: Row, cols: list[str]) -> str:
    """Zeile als Text fuer den regulaeren Ausdruck (leere Spalten fehlen)."""
    return " | ".join(f"{col}={row[col]}" for col in cols if row.get(col, "") != "")


class _RegexTest:
    """Regulaerer Ausdruck auf Eltern + Zeile als ein Text."""

    def __init__(self, cols: list[str], query: str):
        self.cols = cols
        self.pattern = re.compile(query, re.IGNORECASE)

    def __call__(self, path: list[Row]) -> bool:
        return bool(self.pattern.search(" | ".join(row_line(row, self.cols) for row in path)))


class _TermsTest:
    """Jeder Begriff muss in der Zeile oder einem ihrer Eltern stehen."""

    def __init__(self, cols: list[str], query: str):
        self.checks = parse_checks(cols, query)

    def __call__(self, path: list[Row]) -> bool:
        return all(_found(path, cols, needle) for cols, needle in self.checks)


def _found(path: list[Row], cols: list[str], needle: str) -> bool:
    return any(_row_has(row, cols, needle) for row in path)


def _row_has(row: Row, cols: list[str], needle: str) -> bool:
    return any(needle in str(row.get(col, "")).lower() for col in cols)
