"""Tabellenzeilen als Baum bzw. flache Liste (Tree-Widget) und die
Seitenleiste mit den uebrigen Spalten der markierten Zeile."""

from rich.text import Text
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from hisinone.explore.table_model import Row
from hisinone.explore.tree_fold import ShownRow

LINK_MARK = " ◆"  # wie Permalinks im Link-Baum


def row_title(row: Row, title_col: str) -> Text:
    """Titel, Zeilen mit eigener Seite (url) mit Raute markiert."""
    text = Text(str(row.get(title_col, "")), style="bold" if row["tiefe"] == 0 else "")
    if row.get("url"):
        text.append(LINK_MARK, style="cyan")
    return text


def row_details(row: Row | None, cols: list[str], title_col: str, url: str) -> Text:
    """Uebrige Spalten "Spalte: Wert", darunter der Link (url = absolut)."""
    text = Text()
    if row is None:
        return text
    for col in cols:
        if col != title_col and str(row.get(col, "")):
            text.append(f"{col}: ", style="bold")
            text.append(f"{row[col]}\n")
    if url:
        text.append(LINK_MARK.strip() + " ", style="cyan")
        text.append(url, style="underline")
    return text


class RowTree(Tree):
    """Zeilen als Knoten; data = Index in der Liste der sichtbaren Zeilen."""

    def on_mount(self) -> None:
        self.show_root = False
        self.auto_expand = False  # Enter/Klick markiert nur; auf/zu mit Leertaste

    def fill(self, shown: list[ShownRow], title_col: str, folded: set[str] | None) -> None:
        """folded: zugeklappte Knoten; None = flache Liste (alle auf Wurzelebene)."""
        self.clear()
        parents: list[tuple[int, TreeNode]] = []  # (Tiefe, Knoten) entlang des Pfads
        for index, item in enumerate(shown):
            depth = item.row["tiefe"]
            while parents and parents[-1][0] >= depth:
                parents.pop()
            parent = parents[-1][1] if parents and folded is not None else self.root
            node = parent.add(row_title(item.row, title_col), data=index,
                              expand=folded is not None and item.key not in folded)  # fmt: skip
            parents.append((depth, node))
        for node in self._nodes_without_children():
            node.allow_expand = False

    def _nodes_without_children(self) -> list[TreeNode]:
        pending, leaves = [self.root], []
        while pending:
            node = pending.pop()
            pending.extend(node.children)
            if not node.children and node is not self.root:
                leaves.append(node)
        return leaves
