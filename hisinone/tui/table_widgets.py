"""Bausteine der Tabellen-Bildschirme: Titelleiste, Befuellen, Hoehen."""

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.coordinate import Coordinate
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


class ClickTable(DataTable):
    """DataTable, bei dem schon der erste Klick eine Zeile auswaehlt
    (RowSelected); DataTable selbst setzt dabei nur den Cursor."""

    async def _on_click(self, event: events.Click) -> None:
        # Textual ruft danach auch DataTable._on_click auf (kein super() hier,
        # sonst doppelt); steht der Cursor schon auf der Zeile, waehlt es sie aus
        meta = event.style.meta
        if meta.get("row", -1) >= 0 and "column" in meta:
            self.cursor_coordinate = Coordinate(meta["row"], max(meta["column"], 0))


def fill_table(widget: DataTable, table: TreeTable, rows: list[Row], cols: list[str],
               marks: list[str] | None = None) -> None:  # fmt: skip
    """marks: Auf-/Zu-Zeichen je Zeile vor dem Titel (None = keine)."""
    widget.clear(columns=True)
    custom = set(table.custom)
    for col in cols:
        widget.add_column(Text(col, style=CUSTOM_STYLE) if col in custom else col)
    for index, row in enumerate(rows):
        mark = marks[index] if marks else ""
        widget.add_row(*[_cell(row, col, (table.title_col, mark), custom) for col in cols])
    widget.set_class(len(rows) > MIN_ROWS, "big")


def _cell(row: Row, col: str, title: tuple[str, str], custom: set[str]) -> Text | str:
    """title = (Titelspalte, Auf-/Zu-Zeichen)."""
    value = str(row.get(col, ""))
    title_col, mark = title
    if col == title_col:  # Titel eingerueckt wie der Baum, Wurzeln fett
        text = "  " * row["tiefe"] + mark + value
        return Text(text, style="bold" if row["tiefe"] == 0 else "")
    if col in custom:
        return Text(value, style=CUSTOM_STYLE)
    return value
