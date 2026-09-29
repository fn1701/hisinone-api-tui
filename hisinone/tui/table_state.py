"""Anzeige-Zustand einer Tabelle im Vollbild (ohne Oberflaeche)."""

from hisinone.explore.exams import latest_attempts_tree
from hisinone.explore.row_filter import match_rows
from hisinone.explore.table_model import Row, TreeTable

from .page_config import TablePrefs


class TableViewState:
    """Spaltenauswahl, eigene Spalten, letzter Versuch und Filter einer
    Tabelle; wird in den Tabellen-Einstellungen der Seite gemerkt."""

    def __init__(self, table: TreeTable, page_prefs: dict[str, TablePrefs]):
        self.table = table
        self.page_prefs = page_prefs  # Objekt aus Settings, wird direkt geaendert
        prefs = page_prefs.get(table.prefs_key, TablePrefs())
        known = table.cols + table.custom
        chosen = prefs.cols if prefs.cols is not None else known
        self.col_choice = [col for col in chosen if col in known] or known
        self.custom_on = prefs.custom_on and bool(table.custom)
        self.latest = prefs.latest
        self.filter = prefs.filter

    @property
    def can_latest(self) -> bool:
        """Nur-letzter-Versuch gibt es nur bei Leistungen."""
        return "Art" in self.table.custom and {"Ebene", "Versuch"} <= set(self.table.cols)

    def active_cols(self) -> list[str]:
        """Angezeigte Spalten: eigene (wenn an) direkt hinter der Titelspalte."""
        cols = [col for col in self.table.cols if col in self.col_choice]
        if self.custom_on:
            extra = [col for col in self.table.custom if col in self.col_choice]
            title_col = self.table.title_col
            at = cols.index(title_col) + 1 if title_col in cols else len(cols)
            cols[at:at] = extra
        return cols

    def filter_cols(self) -> list[str]:
        return self.table.cols + (self.table.custom if self.custom_on else [])

    def choose_cols(self, chosen: list[str]) -> None:
        # ausgeblendete eigene Spalten bleiben, wie sie waren
        hidden_custom = [col for col in self.table.custom
                         if col in self.col_choice and not self.custom_on]  # fmt: skip
        self.col_choice = chosen + hidden_custom

    def shown_rows(self) -> list[Row]:
        rows = latest_attempts_tree(self.table.rows) if self.latest else self.table.rows
        return match_rows(rows, self.filter_cols(), self.filter)

    def remember(self) -> None:
        """In die Seiten-Einstellungen schreiben; den Standardzustand nicht
        (blosses Oeffnen ist keine Aenderung)."""
        self.latest = self.latest and self.can_latest
        prefs = TablePrefs(self.col_choice, self.custom_on, self.latest, self.filter)
        default = TablePrefs(self.table.cols + self.table.custom)
        if prefs == default:
            self.page_prefs.pop(self.table.prefs_key, None)
        else:
            self.page_prefs[self.table.prefs_key] = prefs

    def flags(self) -> list[str]:
        named = (("eigene Spalten", self.custom_on), ("letzter Versuch", self.latest))
        return [name for name, is_on in named if is_on]
