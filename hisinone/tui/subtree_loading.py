"""Enter auf einem zugeklappten Knoten: seine Kinder laden (Permalink-Seite,
erst aus dem Cache) und in die angezeigte Tabelle einfügen, statt die Seite
zu wechseln - so bleiben andere aufgeklappte Knoten erhalten."""

import time
from urllib.parse import urljoin

from textual import work
from textual.widgets import DataTable

from hisinone.explore.links import clean_url
from hisinone.explore.subtree_merge import merge_subtree
from hisinone.explore.table_model import Row, TreeTable
from hisinone.explore.tree_fold import MARK_CLOSED
from hisinone.explore.tree_tables import parse_tree_tables

from .current_page import CurrentPage
from .row_tree import RowTree


class SubtreeLoading:
    """Mixin des Tabellen-Screens (nutzt table, state, shown, view,
    refresh_table sowie app.page, app.store und app._get)."""

    def load_subtree(self, row: Row) -> None:
        self.notify(f"Lade Unterpunkte von {row.get(self.table.title_col, '')} ...")
        self._fetch_subtree(row)

    @work(thread=True, exclusive=True, group="subtree")
    def _fetch_subtree(self, row: Row) -> None:
        url = urljoin(self.app.page.server_url, row["subtree_url"])
        tables = self._subtree_tables(url, str(row.get(self.table.title_col, "")))
        if tables is not None:
            self.app.call_from_thread(self._insert_subtree, row, tables)

    def _subtree_tables(self, url: str, name: str) -> list[TreeTable] | None:
        """Tabellen der Unterbaum-Seite; None = Fehler (schon gemeldet)."""
        cached = self.app.store.get(clean_url(url), "table")
        if cached:
            return cached[1]
        started = time.monotonic()
        response = self.app._get(url)
        if response is None:
            return None
        page = CurrentPage(clean_url(url), name, response.url, response.text,
                           pulled_at=time.time())  # fmt: skip
        tables = parse_tree_tables(page.html)
        self.app.store.put(page, tables, time.monotonic() - started)
        return tables

    def _insert_subtree(self, row: Row, tables: list[TreeTable]) -> None:
        if not merge_subtree(self.table, row, tables):
            self.notify("Keine Unterpunkte (Enter öffnet nun die Seite der Zeile).")
        self.app.store.update_table(self.app.page.stable_url, self.table)
        self._show_unfolded(row)

    def _show_unfolded(self, row: Row) -> None:
        """Neu anzeigen, Knoten aufgeklappt und mit dem Cursor darauf."""
        self.refresh_table()
        index = next((pos for pos, shown in enumerate(self.shown) if shown.row is row), -1)
        if index < 0:
            return  # z.B. vom Filter ausgeblendet
        if self.shown[index].mark == MARK_CLOSED:
            self.state.toggle_node(self.shown[index].key)
            self.refresh_table()
        if self.view == "table":
            self.query_one(DataTable).move_cursor(row=index)
        else:
            self.query_one(RowTree).select_index(index)
