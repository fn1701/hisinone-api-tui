"""Geladene Tabellen anzeigen (gemeinsam für normale Seiten und den
Studienplaner)."""

from hisinone.explore.storage import save_html

from .current_page import LoadedTables
from .tables_screen import TreeTablesScreen, tables_screen


class TableDisplay:
    """Mixin für LoadingApp (nutzt settings, save_dir, push_screen)."""

    def save_expanded(self, loaded: LoadedTables) -> None:
        """Aufgeklapptes HTML speichern, wenn Speichern eingeschaltet ist."""
        page = loaded.page
        if loaded.expanded_html and self.save_dir:
            save_html(self.save_dir, page.server_url, loaded.expanded_html,
                      f"{page.name}_aufgeklappt")  # fmt: skip

    def show_tree_tables(self, loaded: LoadedTables) -> None:
        page = loaded.page
        self.save_expanded(loaded)
        prefs = self.settings.page_tables(page.stable_url, loaded.tables)
        self.push_screen(tables_screen(page.title_with_time(), loaded.tables, prefs))
        if isinstance(self.screen, TreeTablesScreen):
            # Taste l: gleich die Leistungsdaten im Vollbild (Esc -> alle Tabellen)
            self.screen.open_matching(loaded.open_col)
