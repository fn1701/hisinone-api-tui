"""Enter auf einem zugeklappten Knoten: seine Kinder laden (Permalink-Seite,
erst aus dem Cache) und in die angezeigte Tabelle einfügen, statt die Seite
zu wechseln - so bleiben andere aufgeklappte Knoten erhalten."""

import time
from urllib.parse import urljoin

from textual import work
from textual.widgets import DataTable

from hisinone.explore.links import clean_url
from hisinone.explore.subtree_merge import merge_subtree, subtree_rows
from hisinone.explore.table_model import Row
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
        url = clean_url(urljoin(self.app.page.server_url, row["subtree_url"]))
        children = self._cached_children(row, url) or self._fetched_children(row, url)
        if children:
            self.app.call_from_thread(self._insert_subtree, row, children)
        else:
            self.app.call_from_thread(
                self.notify, "Server liefert den Unterbaum nicht (Vorlesungsverzeichnis wird "
                "gerade aufgebaut oder abgemeldet?) - Enter versucht es erneut.",
                severity="warning")  # fmt: skip

    def _cached_children(self, row: Row, url: str) -> list[Row]:
        """Kinder aus der gecachten Unterbaum-Seite; leer = nicht (brauchbar) da."""
        cached = self.app.store.get(url, "table")
        return subtree_rows(row, cached[1]) if cached else []

    def _fetched_children(self, row: Row, url: str) -> list[Row]:
        """Unterbaum-Seite vom Server; gecacht nur, wenn sie die Kinder enthält
        (sonst bliebe eine Fehlerseite ohne Ablauf im Cache)."""
        started = time.monotonic()
        response = self.app._get(url)
        if response is None:
            return []
        name = str(row.get(self.table.title_col, ""))
        page = CurrentPage(url, name, response.url, response.text, pulled_at=time.time())
        tables = parse_tree_tables(page.html)
        children = subtree_rows(row, tables)
        if children:
            self.app.store.put(page, tables, time.monotonic() - started)
        return children

    def _insert_subtree(self, row: Row, children: list[Row]) -> None:
        merge_subtree(self.table, row, children)
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
