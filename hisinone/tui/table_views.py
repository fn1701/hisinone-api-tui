"""Ansichten einer Tabelle (t): aufklappbare Tabelle, Baum, flache Liste.
Baum und Liste zeigen die uebrigen Spalten der markierten Zeile unten in
der Seitenleiste; Filter, Auf-/Zu-Zustand und Zeilenaktionen gelten fuer
alle Ansichten gleich."""

from urllib.parse import urljoin

from textual.widgets import DataTable, Static, Tree
from textual.widgets.tree import TreeNode

from hisinone.explore.table_model import Row

from .copy_name import CopyName, copy_text
from .page_config import TABLE_VIEWS
from .row_tree import RowTree, row_details

VIEW_NAMES = {"table": "Tabelle", "tree": "Baum", "flat": "Liste"}
VIEWS_CSS = """
#treeview { height: 1fr; }
#rowtree { width: 2fr; }
#side { width: 1fr; border-left: solid $primary; padding: 0 1; }
#sidehelp { height: 1fr; color: $text-muted; }
#rowinfo { height: auto; }
"""


class TableViews:
    """Mixin fuer SingleTableScreen (nutzt state, shown, table, refresh_table)."""

    @property
    def view(self) -> str:
        """Gewaehlte Ansicht, sonst Standard aus den Einstellungen (--flat)."""
        return self.state.view or ("table" if self.app.settings.tree else "flat")

    def action_toggle_view(self) -> None:
        self.state.view = TABLE_VIEWS[(TABLE_VIEWS.index(self.view) + 1) % len(TABLE_VIEWS)]
        self.refresh_table()
        self.focus_rows()
        self.notify(f"Ansicht: {VIEW_NAMES[self.view]}", timeout=2)

    def show_rows(self) -> None:
        """Sichtbare Zeilen in die Widgets der aktuellen Ansicht."""
        in_table = self.view == "table"
        self.query_one("#tablescroll").display = in_table
        self.query_one("#treeview").display = not in_table
        if not in_table:
            folded = self.state.current_fold.folded if self.view == "tree" else None
            self.query_one(RowTree).fill(self.shown, self.table.title_col, folded)
            self.query_one("#sidehelp", Static).update(
                f"{VIEW_NAMES[self.view]} (t wechselt)\n"
                "g: Seite oeffnen · o: im Browser\nLeertaste/+/-: auf/zu"
            )
            self._show_details(self.current_row())

    def focus_rows(self) -> None:
        widget = DataTable if self.view == "table" else RowTree
        self.query_one(widget).focus()

    def current_index(self) -> int:
        """Index der markierten Zeile in self.shown (-1 = keine)."""
        if self.view == "table":
            return self.query_one(DataTable).cursor_row
        node = self.query_one(RowTree).cursor_node
        return node.data if node is not None and node.data is not None else -1

    def current_row(self) -> Row | None:
        index = self.current_index()
        return self.shown[index].row if 0 <= index < len(self.shown) else None

    def row_url(self, row: Row) -> str:
        return urljoin(self.app.page.server_url, row["url"]) if row.get("url") else ""

    def _show_details(self, row: Row | None) -> None:
        details = row_details(row, self.state.active_cols(), self.table.title_col,
                              self.row_url(row) if row else "")  # fmt: skip
        self.query_one("#rowinfo", Static).update(details)
        title = str(row.get(self.table.title_col, "")) if row else ""
        self.query_one(CopyName).set_name(title)

    def action_copy_name(self) -> None:
        """Name der markierten Zeile (auch in der Tabellen-Ansicht)."""
        row = self.current_row()
        if row:
            copy_text(self.app, str(row.get(self.table.title_col, "")))

    # Namens-Handler statt @on: Dekoratoren in einem Mixin registriert Textual nicht
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self._show_details(self.current_row())

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        self._node_toggled(event.node)

    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
        self._node_toggled(event.node)

    def _node_toggled(self, node: TreeNode) -> None:
        """Auf-/Zuklappen im Baum in den gemeinsamen Zustand uebernehmen."""
        index = node.data
        if self.view != "tree" or index is None or not 0 <= index < len(self.shown):
            return
        key = self.shown[index].key
        if (key in self.state.current_fold.folded) == node.is_expanded:
            self.state.toggle_node(key)
            self.state.remember()

    def action_toggle_node(self, index: int | None = None) -> None:
        """Knoten auf-/zuklappen (Standard: markierte Zeile); Cursor bleibt auf ihm."""
        if self.view != "table":
            node = self.query_one(RowTree).cursor_node
            if node is not None and node.allow_expand:
                node.toggle()
            return
        table = self.query_one(DataTable)
        index = table.cursor_row if index is None else index
        if 0 <= index < len(self.shown) and self.shown[index].mark.strip():
            self.state.toggle_node(self.shown[index].key)
            self.refresh_table()
            table.move_cursor(row=index)

    def action_fold_all(self, folded: bool) -> None:
        self.state.fold_all(folded)
        self.refresh_table()
        if self.view == "table":
            self.query_one(DataTable).move_cursor(row=0)
