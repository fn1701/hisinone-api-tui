"""Auf-/Zuklappen in einer Baum-Tabelle (ohne Oberflaeche).

Ein Knoten wird ueber seinen Titelpfad "Eltern › Kind" erkannt, damit der
Zustand ein Neuladen der Seite und das Speichern in der Config uebersteht.
"""

from dataclasses import dataclass, field

from .table_model import Row

SEPARATOR = " › "
MARK_CLOSED, MARK_OPEN, MARK_LEAF = "▶ ", "▼ ", "  "


@dataclass
class ShownRow:
    """Sichtbare Zeile mit Pfad und Markierung fuer die Titelspalte."""

    row: Row
    key: str
    mark: str


@dataclass
class TreeFold:
    """Menge der zugeklappten Knoten einer Tabelle."""

    folded: set[str] = field(default_factory=set)

    def visible(self, rows: list[Row], title_col: str) -> list[ShownRow]:
        """Zeilen ohne die Nachfahren zugeklappter Knoten."""
        shown: list[ShownRow] = []
        hidden_below = -1  # Tiefe des zugeklappten Vorfahren, -1 = keiner
        for index, (row, key) in enumerate(zip(rows, node_keys(rows, title_col), strict=True)):
            depth = row["tiefe"]
            if 0 <= hidden_below < depth:
                continue
            hidden_below = depth if key in self.folded else -1
            shown.append(ShownRow(row, key, self._mark(rows, index, key)))
        return shown

    def _mark(self, rows: list[Row], index: int, key: str) -> str:
        if not has_children(rows, index):
            return MARK_LEAF
        return MARK_CLOSED if key in self.folded else MARK_OPEN

    def toggle(self, key: str) -> None:
        self.folded ^= {key}

    def fold_all(self, rows: list[Row], title_col: str) -> None:
        keys = node_keys(rows, title_col)
        self.folded = {keys[index] for index in range(len(rows)) if has_children(rows, index)}

    def unfold_all(self) -> None:
        self.folded = set()


def has_children(rows: list[Row], index: int) -> bool:
    return index + 1 < len(rows) and rows[index + 1]["tiefe"] > rows[index]["tiefe"]


def node_keys(rows: list[Row], title_col: str) -> list[str]:
    """Titelpfad je Zeile; Geschwister mit gleichem Titel bekommen "#2", "#3"."""
    keys: list[str] = []
    path: list[str] = []
    seen: dict[str, int] = {}
    for row in rows:
        del path[row["tiefe"] :]
        path.append(str(row.get(title_col, "")))
        key = SEPARATOR.join(path)
        seen[key] = seen.get(key, 0) + 1
        keys.append(key if seen[key] == 1 else f"{key}#{seen[key]}")
    return keys
