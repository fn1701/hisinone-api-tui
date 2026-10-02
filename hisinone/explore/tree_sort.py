"""Alphabetische Reihenfolge einer Baum-Tabelle (ohne Oberfläche).

Sortiert werden nur Geschwister; jeder Knoten nimmt seine Nachfahren mit,
so bleiben Module unter ihrem Katalog.
"""

from .table_model import Row


def sort_tree(rows: list[Row], title_col: str) -> list[Row]:
    """Zeilen (flach mit "tiefe") mit Geschwistern A-Z nach Titel."""
    result: list[Row] = []
    for block in sorted(_blocks(rows), key=lambda block: title_key(block[0], title_col)):
        result.append(block[0])
        result.extend(sort_tree(block[1:], title_col))
    return result


def title_key(row: Row, title_col: str) -> str:
    """Ohne Groß-/Kleinschreibung und führende Satzzeichen (".Net" unter N)."""
    title = str(row.get(title_col, "")).casefold()
    return title.lstrip(" .-_#*\"'([")


def _blocks(rows: list[Row]) -> list[list[Row]]:
    """Teilbäume der obersten Ebene in rows: Knoten plus Nachfahren."""
    blocks: list[list[Row]] = []
    top = min((row["tiefe"] for row in rows), default=0)
    for row in rows:
        if row["tiefe"] <= top or not blocks:
            blocks.append([row])
        else:
            blocks[-1].append(row)
    return blocks
