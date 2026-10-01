"""Eine Tabelle im Vollbild: Zeilenfilter (/), Spalten (k), eigene Spalten (x),
letzter Versuch (v), Baum/flach (t), Export (e), Knoten auf/zu (Leertaste, +, -)."""

import re

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Checkbox, DataTable, Footer, Header, Input, OptionList, Static

from hisinone.explore.row_filter import filter_suggestions
from hisinone.explore.table_model import TreeTable

from .filter_bar import FilterBar
from .filter_screen import SUGGEST_CSS, FilterScreen
from .page_config import TablePrefs
from .table_columns import TableColumns
from .table_export import TableExport
from .table_heights import fit_tables
from .table_state import TableViewState
from .table_widgets import TABLES_CSS, ClickTable, TableBar, fill_table

FILTER_HINT = "Zeilen filtern: Text oder Spalte=Wert, mehrere mit Leerzeichen (↓ = Vorschlaege)"


class SingleTableScreen(TableColumns, TableExport, FilterScreen):
    BINDINGS = [
        Binding("escape", "back", "Zurueck"),
        Binding("slash", "focus_filter", "Filter"),
        Binding("k", "columns", "Spalten"),
        Binding("x", "toggle_custom", "Eigene Spalten"),
        Binding("v", "toggle_latest", "Letzter Versuch"),
        Binding("t", "toggle_flat", "Baum/Flach"),
        Binding("e", "export", "Export"),
        Binding("space", "toggle_node", "Auf/Zu"),
        Binding("plus", "fold_all(False)", "Alle auf"),
        Binding("minus", "fold_all(True)", "Alle zu"),
    ]
    CSS = "SingleTableScreen DataTable { height: auto; }" + TABLES_CSS + SUGGEST_CSS

    def __init__(self, page_name: str, table: TreeTable, page_prefs: dict[str, TablePrefs]):
        super().__init__()
        self.page_name, self.table = page_name, table
        self.state = TableViewState(table, page_prefs)
        self.shown, self.shown_rows = self.state.shown(), table.rows

    def suggestions(self) -> list[str]:
        return filter_suggestions(self.table.rows, self.state.filter_cols())

    def column_name(self, index: int) -> str:
        return self.state.active_cols()[index]

    def check_action(self, action: str, parameters) -> bool | None:
        if action == "toggle_custom":
            return bool(self.table.custom)
        if action == "toggle_latest":
            return self.state.can_latest
        return True

    def compose_top(self) -> ComposeResult:
        """Platz fuer Bedienelemente ueber dem Filter (Unterklassen)."""
        yield from ()

    def compose(self) -> ComposeResult:
        yield Header()
        yield from self.compose_top()
        yield FilterBar(self.state.filter, "rowfilter", FILTER_HINT)
        yield OptionList(id="suggest")
        with VerticalScroll():
            yield TableBar(0, "", False)
            yield ClickTable(zebra_stripes=True, cursor_type="row")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_table()
        self.query_one(DataTable).focus()  # sonst landen x/k/v/e im Filterfeld
        self.call_after_refresh(fit_tables, self)

    def on_resize(self) -> None:
        self.call_after_refresh(fit_tables, self)

    def refresh_table(self) -> None:
        """Nach jeder Aenderung: merken, filtern, neu fuellen, Titel setzen."""
        self.state.filter = self.filter_input.value
        self.state.remember()
        try:
            self.shown = self.state.shown(self.app.settings.regex)
        except re.error:  # Ausdruck noch unvollstaendig: altes Ergebnis lassen
            self.query_one(FilterBar).mark_invalid(True)
            return
        self.query_one(FilterBar).mark_invalid(False)
        self.shown_rows = [shown.row for shown in self.shown]
        fill_table(self.query_one(DataTable), self.table, self.shown_rows,
                   self.state.active_cols(), [shown.mark for shown in self.shown],
                   self.state.col_widths)  # fmt: skip
        counts = f"{len(self.shown_rows)} von {len(self.table.rows)} Zeilen"
        flags = self.state.flags()
        suffix = f" ({', '.join(flags)})" if flags else ""
        self.sub_title = f"{self.page_name}: {self.table.display_name} · {counts}{suffix}"
        self.query_one(".name", Static).update(f"{self.table.display_name} · {counts}")
        self.refresh_bindings()
        self.call_after_refresh(fit_tables, self)

    @on(Input.Changed, "#rowfilter")
    def rowfilter_changed(self) -> None:
        self.refresh_table()
        self.update_suggest()

    @on(Checkbox.Changed, "#regex")
    def regex_toggled(self) -> None:
        self.refresh_table()
        self.update_suggest()  # Regex an: Beispiele statt Spalte=Wert

    @on(Input.Submitted, "#rowfilter")
    def rowfilter_submitted(self) -> None:
        self.hide_suggest()
        self.query_one(DataTable).focus()

    def action_back(self) -> None:
        if not self.close_filter():
            self.app.pop_screen()

    def action_focus_filter(self) -> None:
        self.filter_input.focus()

    @on(DataTable.RowSelected)
    def row_clicked(self, event: DataTable.RowSelected) -> None:  # Klick/Enter = Leertaste
        self.action_toggle_node(event.cursor_row)

    def action_toggle_node(self, index: int | None = None) -> None:
        """Knoten auf-/zuklappen (Standard: unter dem Cursor); Cursor bleibt auf ihm."""
        table = self.query_one(DataTable)
        index = table.cursor_row if index is None else index
        if 0 <= index < len(self.shown) and self.shown[index].mark.strip():
            self.state.toggle_node(self.shown[index].key)
            self.refresh_table()
            table.move_cursor(row=index)

    def action_fold_all(self, folded: bool) -> None:
        self.state.fold_all(folded)
        self.refresh_table()
        self.query_one(DataTable).move_cursor(row=0)
