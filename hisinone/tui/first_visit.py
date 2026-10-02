"""Erster Besuch einer Seite mit Baum-Tabellen: Ansicht erkennen und in der
Config merken. Benutzer-Einstellungen gehen vor (PageConfig.learn)."""

from hisinone.explore.page_tables import can_expand, has_data_tables
from hisinone.explore.table_model import TreeTable

from .current_page import CurrentPage
from .page_config import PageConfig


class FirstVisit:
    """Mixin der App; braucht _expanded und _show_tables (LoadingApp)."""

    def _first_visit(self, page: CurrentPage, open_col: str) -> list[TreeTable]:
        """Erst aufklappen, dann entscheiden: manche Bäume zeigen ihre Daten
        (gefüllte Spalten) erst aufgeklappt. Ergebnis merkt sich die Config."""
        expand = can_expand(page.html)
        tables, html = self._expanded(page, expand)
        view = "table" if has_data_tables(page.html, tables) else "tree"
        config = self.call_from_thread(self.learn_page, page, view, expand)
        if config.view != "table":
            return []
        return self._show_tables(page, tables, html, open_col or config.open_table)

    def learn_page(self, page: CurrentPage, view: str, expand: bool) -> PageConfig:
        config = self.settings.pages.setdefault(page.stable_url, PageConfig())
        config.learn(page.name, view, expand)
        return config
