"""Unterbaum eines Knotens in eine Baum-Tabelle einfügen: Der Server liefert
die Kinder eines zugeklappten Knotens nur als eigene Seite (Permalink des
Knotens); aus deren Tabelle werden die Kinder übernommen, damit bereits
aufgeklappte Geschwister erhalten bleiben."""

from .table_model import Row, TreeTable


def merge_subtree(table: TreeTable, node: Row, children: list[Row]) -> None:
    """Die geladenen Kinder (subtree_rows) unter node einfügen. Ob ein Knoten
    einen Unterbaum hat, sagt nur das Markup des Servers - eine leere Antwort
    ist ein Fehler (z.B. Seite "wird gerade aufgebaut") und ändert nichts."""
    if not children or has_child_rows(table, node):
        return
    index = _index_of(table, node)
    table.rows[index + 1 : index + 1] = children


def has_child_rows(table: TreeTable, node: Row) -> bool:
    """Kinder schon in der Tabelle (geladen)? Unabhängig von Filter und
    Auf-/Zu-Zustand der Anzeige."""
    index = _index_of(table, node)
    following = table.rows[index + 1 : index + 2]
    return bool(following) and following[0]["tiefe"] > node["tiefe"]


def _index_of(table: TreeTable, node: Row) -> int:
    return next(position for position, row in enumerate(table.rows) if row is node)


def subtree_rows(node: Row, fetched: list[TreeTable]) -> list[Row]:
    """Nachfahren des Knotens (gefunden über seinen Permalink), Tiefe an
    die Stelle von node angepasst; leer = Seite enthält den Knoten nicht."""
    if not node.get("permalink"):
        return []
    for other in fetched:
        for index, row in enumerate(other.rows):
            if row.get("permalink") == node["permalink"]:
                return _descendants(other.rows, index, node["tiefe"])
    return []


def _descendants(rows: list[Row], index: int, depth: int) -> list[Row]:
    base = rows[index]["tiefe"]
    result = []
    for row in rows[index + 1 :]:
        if row["tiefe"] <= base:
            break
        result.append({**row, "tiefe": depth + row["tiefe"] - base})
    return result
