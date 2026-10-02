"""Spaltenauswahl (k), eigene Spalten (x), letzter Versuch (v), für den
Vollbild-Tabellenbildschirm."""

from rich.text import Text

from .dialogs import ColumnsDialog
from .table_widgets import CUSTOM_STYLE


class TableColumns:
    """Mixin; erwartet self.table, self.state und refresh_table()."""

    def action_toggle_custom(self) -> None:
        self.state.custom_on = not self.state.custom_on
        self.refresh_table()

    def action_toggle_latest(self) -> None:
        self.state.latest = not self.state.latest
        self.refresh_table()

    def action_columns(self) -> None:
        self.app.push_screen(ColumnsDialog(self._column_options()), self._columns_chosen)

    def _column_options(self) -> list[tuple]:
        chosen = self.state.col_choice
        options = [(col, col, col in chosen) for col in self.table.cols]
        if self.state.custom_on:
            for col in self.table.custom:
                label = Text(f"{col} (eigene)", style=CUSTOM_STYLE)
                options.append((label, col, col in chosen))
        return options

    def _columns_chosen(self, chosen: list[str] | None) -> None:
        if chosen:
            self.state.choose_cols(chosen)
            self.refresh_table()
