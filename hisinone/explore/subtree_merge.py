"""Unterbaum eines Knotens in eine Baum-Tabelle einfügen: Der Server liefert
die Kinder eines zugeklappten Knotens nur als eigene Seite (Permalink des
Knotens); aus deren Tabelle werden die Kinder übernommen, damit bereits
aufgeklappte Geschwister erhalten bleiben."""

from .table_model import Row, TreeTable


def merge_subtree(table: TreeTable, node: Row, fetched: list[TreeTable]) -> int:
    """Kinder von node aus den Tabellen der Unterbaum-Seite unter node
    einfügen; Anzahl der eingefügten Zeilen (0 = Knoten hat keine)."""
    children = subtree_rows(node, fetched)
    index = next(position for position, row in enumerate(table.rows) if row is node)
    table.rows[index + 1 : index + 1] = children
    node["subtree_url"] = ""  # geladen: Enter klappt nun auf/zu bzw. öffnet die Seite
    return len(children)


def subtree_rows(node: Row, fetched: list[TreeTable]) -> list[Row]:
    """Nachfahren des Knotens (gefunden über seinen Permalink), Tiefe an
    die Stelle von node angepasst."""
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
