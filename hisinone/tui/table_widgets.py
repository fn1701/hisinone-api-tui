"""Bausteine der Tabellen-Bildschirme: Titelleiste, Befüllen, Höhen."""

from rich.cells import cell_len
from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.coordinate import Coordinate
from textual.widgets import DataTable, Static

from hisinone.explore.table_model import Row, TreeTable

from .row_tree import LINK_MARK

CUSTOM_STYLE = "italic magenta"  # eigene (berechnete) Spalten
MIN_ROWS = 10  # größere Tabellen bekommen mindestens so viele Zeilen

TABLES_CSS = """
TableBar { height: 1; background: $boost; color: $text-muted; padding: 0 1; }
TableBar .name { width: auto; text-style: bold; }
TableBar .side { width: 1fr; }
TableBar .action { text-align: right; }
TableBar.clickable:hover { background: $accent; color: $text; }
"""


class TableBar(Horizontal):
    """Titelleiste über einer Tabelle: Name mittig, Aktion rechts;
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
    """DataTable, bei dem schon der erste Klick eine Zeile auswählt
    (RowSelected); DataTable selbst setzt dabei nur den Cursor."""

    async def _on_click(self, event: events.Click) -> None:
        # Textual ruft danach auch DataTable._on_click auf (kein super() hier,
        # sonst doppelt); steht der Cursor schon auf der Zeile, wählt es sie aus
        meta = event.style.meta
        if meta.get("row", -1) >= 0 and "column" in meta:
            self.cursor_coordinate = Coordinate(meta["row"], max(meta["column"], 0))


def fill_table(widget: DataTable, table: TreeTable, rows: list[Row], cols: list[str],
               marks: list[str] | None = None,
               widths: dict[str, int] | None = None) -> None:  # fmt: skip
    """marks: Auf-/Zu-Zeichen je Zeile vor dem Titel (None = keine).
    widths: bisher größte Breite je Spalte, wird hier erweitert; die Spalten
    wachsen nur (None = DataTable misst selbst)."""
    widget.clear(columns=True)
    custom = set(table.custom)
    cells = [_row_cells(row, cols, (table.title_col, marks[index] if marks else None), custom)
             for index, row in enumerate(rows)]  # fmt: skip
    if widths is not None:
        _grow_widths(widths, cols, cells)
    for col in cols:
        label = Text(col, style=CUSTOM_STYLE) if col in custom else col
        widget.add_column(label, width=widths[col] if widths is not None else None)
    for row_cells in cells:
        widget.add_row(*row_cells)
    widget.set_class(len(rows) > MIN_ROWS, "big")


def _row_cells(row: Row, cols: list[str], title: tuple[str, str | None],
               custom: set[str]) -> list:  # fmt: skip
    return [_cell(row, col, title, custom) for col in cols]


def _grow_widths(widths: dict[str, int], cols: list[str], cells: list[list]) -> None:
    for position, col in enumerate(cols):
        widest = max((cell_len(str(row[position])) for row in cells), default=0)
        widths[col] = max(widths.get(col, 0), cell_len(col), widest)


def _cell(row: Row, col: str, title: tuple[str, str | None], custom: set[str]) -> Text | str:
    """title = (Titelspalte, Auf-/Zu-Zeichen); Zeichen "" = flache Liste
    (ohne Einrückung), None = Baum ohne Auf-/Zu."""
    value = str(row.get(col, ""))
    title_col, mark = title
    if col == title_col:  # Titel eingerückt wie der Baum, Wurzeln fett, Link mit Raute
        indent = "" if mark == "" else "  " * row["tiefe"] + (mark or "")
        text = Text(indent + value, style="bold" if row["tiefe"] == 0 and mark != "" else "")
        return text.append(LINK_MARK, style="cyan") if row.get("url") else text
    if col in custom:
        return Text(value, style=CUSTOM_STYLE)
    return value
