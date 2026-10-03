"""Zeile öffnen: Enter klappt auf/zu bzw. lädt den Unterbaum (ohne Unterbaum
die Seite der Zeile), g lädt die Seite der Zeile (z.B. Modulbeschreibung im
Studienplaner) in der App, o öffnet sie im Browser (wie im Link-Baum),
p lädt die Seiten aller sichtbaren Zeilen in den Cache (TablePrefetch)."""

from textual.widgets import Tree

from hisinone.explore.subtree_merge import has_child_rows

from .row_tree import RowTree
from .subtree_loading import SubtreeLoading
from .table_prefetch import TablePrefetch


class TableLinks(SubtreeLoading, TablePrefetch):
    """Mixin; erwartet current_row/row_url (TableViews) und app.open_from_table."""

    def action_enter_row(self) -> None:
        """Sichtbare Kinder: auf-/zuklappen; sonst den zugeklappten Unterbaum
        vom Server laden; ohne Unterbaum die Seite der Zeile (wie g)."""
        if self._has_children():
            self.action_toggle_node()
            return
        row = self.current_row()
        if row and row.get("subtree_url") and not has_child_rows(self.table, row):
            self.load_subtree(row)
        elif row and row.get("url"):
            self.app.open_from_table(row["url"], str(row.get(self.table.title_col, "")))

    def _has_children(self) -> bool:
        if self.view != "table":
            node = self.query_one(RowTree).cursor_node
            return node is not None and node.allow_expand
        index = self.current_index()
        return 0 <= index < len(self.shown) and bool(self.shown[index].mark.strip())

    # Namens-Handler statt @on: Dekoratoren in einem Mixin registriert Textual nicht
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        if isinstance(event.control, RowTree):
            self.action_enter_row()

    def action_open_row(self) -> None:
        row = self._linked_row()
        if row is not None:
            self.app.open_from_table(row["url"], str(row.get(self.table.title_col, "")))

    def action_browse_row(self) -> None:
        row = self._linked_row()
        if row is not None:
            self.app.open_url(self.row_url(row))

    def _linked_row(self) -> dict | None:
        row = self.current_row()
        if row is None or not row.get("url"):
            self.notify("Diese Zeile hat keinen Link (ggf. mit r neu laden).", severity="warning")
            return None
        return row
