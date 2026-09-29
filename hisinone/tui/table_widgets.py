"""Bausteine der Tabellen-Bildschirme: Titelleiste, Befuellen, Hoehen."""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import DataTable, Static

from hisinone.explore.table_model import Row, TreeTable

CUSTOM_STYLE = "italic magenta"  # eigene (berechnete) Spalten
MIN_ROWS = 10  # groessere Tabellen bekommen mindestens so viele Zeilen

TABLES_CSS = """
TableBar { height: 1; background: $boost; color: $text-muted; padding: 0 1; }
TableBar .name { width: auto; text-style: bold; }
TableBar .side { width: 1fr; }
TableBar .action { text-align: right; }
TableBar.clickable:hover { background: $accent; color: $text; }
"""


class TableBar(Horizontal):
    """Titelleiste ueber einer Tabelle: Name mittig, Aktion rechts;
    Klick = Tabelle einzeln im Vollbild."""

    def __init__(self, index: int, text: str, clickable: bool):
        super().__init__(classes="clickable" if clickable else "")
        self.index, self.text, self.clickable = index, text, clickable
        self.tooltip = "Klick oder f: Vollbild" if clickable else None
        if index:
            self.styles.margin = (1, 0, 0, 0)  # Leerzeile zwischen Tabellen

    def compose(self) -> ComposeResult:
        yield Static("▸" if self.clickable else "", classes="side")
        yield Static(self.text, classes="name")
        yield Static("erweitern (f)" if self.clickable else "", classes="side action")

    def on_click(self) -> None:
        if self.clickable:
            self.screen.open_single(self.index)


def fill_table(widget: DataTable, table: TreeTable, rows: list[Row], cols: list[str]) -> None:
    widget.clear(columns=True)
    custom = set(table.custom)
    for col in cols:
        widget.add_column(Text(col, style=CUSTOM_STYLE) if col in custom else col)
    for row in rows:
        widget.add_row(*[_cell(row, col, table.title_col, custom) for col in cols])
    widget.set_class(len(rows) > MIN_ROWS, "big")


def _cell(row: Row, col: str, title_col: str, custom: set[str]) -> Text | str:
    value = str(row.get(col, ""))
    if col == title_col:  # Titel eingerueckt wie der Baum, Wurzeln fett
        return Text("  " * row["tiefe"] + value, style="bold" if row["tiefe"] == 0 else "")
    if col in custom:
        return Text(value, style=CUSTOM_STYLE)
    return value
