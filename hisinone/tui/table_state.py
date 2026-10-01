"""Anzeige-Zustand einer Tabelle im Vollbild (ohne Oberflaeche)."""

from hisinone.explore.exams import latest_attempts_tree
from hisinone.explore.table_model import Row, TreeTable
from hisinone.explore.tree_filter import filter_tree
from hisinone.explore.tree_fold import ShownRow, TreeFold

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
        self.view = prefs.view  # "" = Standard (der Bildschirm setzt ihn ein)
        # Spalten wachsen beim Auf-/Zuklappen nur (kein Springen); neuer Filter
        # oder Alle auf/zu: neu aus dem Gezeigten
        self.col_widths: dict[str, int] = {}
        self._last_query: tuple[str, bool, bool] | None = None
        # Filterergebnis: eigener Auf-/Zu-Zustand, startet offen, neu je Filter
        self.filter_fold = TreeFold(set())
        self.matched: list[Row] | None = None  # None = kein Filter aktiv
        self.fold_changed = prefs.folded is not None  # sonst Startzustand, nicht merken
        self.fold = TreeFold(set(prefs.folded or []))
        if not self.fold_changed and table.start_folded:
            self.fold.fold_all(table.rows, table.title_col)

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

    def shown(self, view: str, regex: bool = False) -> list[ShownRow]:
        """Sichtbare Zeilen der Ansicht (TABLE_VIEWS); mit Filter die Treffer
        samt Eltern (eigener Auf-/Zu-Zustand), in der Liste nur die Treffer.
        "tree": alle Zeilen, das Auf-/Zuklappen macht das Baum-Widget.
        regex: re.error bei ungueltigem Ausdruck."""
        if (self.filter, regex, view) != self._last_query:
            self.col_widths.clear()
            self.filter_fold = TreeFold(set())
            self._last_query = (self.filter, regex, view)
        rows = latest_attempts_tree(self.table.rows) if self.latest else self.table.rows
        self.matched = None
        if view == "flat":
            return self._flat(rows, regex)
        if self.filter.strip():
            rows = self.matched = filter_tree(rows, self.filter_cols(), self.filter, regex)
        fold = TreeFold(set()) if view == "tree" else self.current_fold
        return fold.visible(rows, self.table.title_col)

    @property
    def current_fold(self) -> TreeFold:
        """Zugeklappte Knoten: mit Filter die des Filterergebnisses."""
        return self.filter_fold if self.matched is not None else self.fold

    def _flat(self, rows: list[Row], regex: bool) -> list[ShownRow]:
        """Alle Zeilen bzw. nur die Treffer (ohne Eltern); Markierung "" =
        nicht einruecken."""
        if self.filter.strip():
            rows = filter_tree(rows, self.filter_cols(), self.filter, regex, parents=False)
        return [ShownRow(row, "", "") for row in rows]

    def toggle_node(self, key: str) -> None:
        if self.matched is not None:
            self.filter_fold.toggle(key)
            return
        self.fold.toggle(key)
        self.fold_changed = True

    def fold_all(self, folded: bool) -> None:
        """True = alles bis auf die oberste Ebene zu, False = alles auf."""
        self.col_widths.clear()
        if self.matched is not None:
            self._set_all(self.filter_fold, self.matched, folded)
            return
        self._set_all(self.fold, self.table.rows, folded)
        self.fold_changed = True

    def _set_all(self, fold: TreeFold, rows: list[Row], folded: bool) -> None:
        if folded:
            fold.fold_all(rows, self.table.title_col)
        else:
            fold.unfold_all()

    def remember(self) -> None:
        """In die Seiten-Einstellungen schreiben; den Standardzustand nicht
        (blosses Oeffnen ist keine Aenderung)."""
        self.latest = self.latest and self.can_latest
        folded = sorted(self.fold.folded) if self.fold_changed else None
        prefs = TablePrefs(self.col_choice, self.custom_on, self.latest, self.filter, folded,
                           self.view)  # fmt: skip
        default = TablePrefs(self.table.cols + self.table.custom)
        if prefs == default:
            self.page_prefs.pop(self.table.prefs_key, None)
        else:
            self.page_prefs[self.table.prefs_key] = prefs

    def flags(self) -> list[str]:
        named = (("eigene Spalten", self.custom_on), ("letzter Versuch", self.latest))
        return [name for name, is_on in named if is_on]
