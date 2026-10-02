"""Zeilenfilter für Tabellen: "Text" oder "Spalte=Wert", mehrere mit
Leerzeichen (alle müssen passen, Groß-/Kleinschreibung egal). Gefiltert
wird lokal auf den schon geladenen Zeilen."""

import shlex

from .table_model import Row


def _terms(query: str) -> list[str]:
    try:
        return shlex.split(query)
    except ValueError:  # offenes Anführungszeichen beim Tippen
        return query.replace('"', " ").split()


def parse_checks(cols: list[str], query: str) -> list[tuple[list[str], str]]:
    """[(Spalten, in denen gesucht wird, gesuchter Text)] je Begriff."""
    by_name = {col.lower(): col for col in cols}
    checks = []
    for term in _terms(query):
        col, separator, value = term.partition("=")
        if separator and col.lower() in by_name:
            checks.append(([by_name[col.lower()]], value.lower()))
        else:
            checks.append((cols, term.lower()))
    return checks


def _matches(row: Row, checks: list[tuple[list[str], str]]) -> bool:
    return all(
        any(needle in str(row.get(col, "")).lower() for col in cols) for cols, needle in checks
    )


def match_rows(rows: list[Row], cols: list[str], query: str) -> list[Row]:
    """ "Spalte=Wert" sucht nur in dieser Spalte, sonst in allen. Werte mit
    Leerzeichen in Anführungszeichen."""
    checks = parse_checks(cols, query)
    return [row for row in rows if _matches(row, checks)]


def filter_suggestions(rows: list[Row], cols: list[str], max_values: int = 40) -> list[str]:
    """Vorschläge "Spalte=Wert" für Spalten mit wenigen verschiedenen Werten."""
    suggestions = []
    for col in cols:
        values = sorted({str(row.get(col, "")) for row in rows} - {""})
        if 1 < len(values) <= max_values:
            suggestions += [f"{col}={shlex.quote(v) if ' ' in v else v}" for v in values]
    return suggestions
