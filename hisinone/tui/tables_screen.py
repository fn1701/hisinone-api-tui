"""Alle Baum-Tabellen einer Seite auf einem Bildschirm (Esc = zurueck)."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header

from hisinone.explore.table_model import TreeTable

from .page_config import TablePrefs
from .single_table_screen import SingleTableScreen
from .table_heights import fit_tables
from .table_widgets import TABLES_CSS, TableBar, fill_table


class TreeTablesScreen(Screen):
    """Ueber jeder Tabelle eine Titelleiste: Klick oder f = Tabelle im Vollbild."""

    BINDINGS = [Binding("escape", "back", "Zurueck"), Binding("f", "fullscreen", "Vollbild")]
    CSS = "TreeTablesScreen DataTable { height: auto; }" + TABLES_CSS

    def __init__(self, page_name: str, tables: list[TreeTable], prefs: dict[str, TablePrefs]):
        super().__init__()
        self.page_name, self.tables = page_name, tables
        self.prefs = prefs  # Tabellen-Einstellungen der Seite (aus Settings)

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            for index, table in enumerate(self.tables):
                yield TableBar(index, f"{table.display_name} · {len(table.rows)} Zeilen", True)
                widget = DataTable(zebra_stripes=True, cursor_type="row")
                fill_table(widget, table, table.rows, table.cols)
                yield widget
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = f"{self.page_name}: {len(self.tables)} Tabelle(n)"
        self.call_after_refresh(fit_tables, self)

    def on_resize(self) -> None:
        self.call_after_refresh(fit_tables, self)

    def open_single(self, index: int) -> None:
        screen = SingleTableScreen(self.page_name, self.tables[index], self.prefs)
        self.app.push_screen(screen)

    def open_matching(self, wanted: str) -> None:
        """Erste Tabelle mit dieser Spalte oder diesem Namen im Vollbild."""
        for index, table in enumerate(self.tables):
            if wanted and (wanted in table.cols or table.display_name == wanted):
                self.open_single(index)
                return

    def action_fullscreen(self) -> None:
        widgets = list(self.query(DataTable))
        # Fokus in keiner Tabelle -> die erste
        self.open_single(widgets.index(self.focused) if self.focused in widgets else 0)

    def action_back(self) -> None:
        self.app.pop_screen()
