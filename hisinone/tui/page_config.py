"""Gelernte Seiten mit Baum-Tabelle (Config "pages") als Datenklassen.

Die Entscheidungen werden beim ersten Besuch erkannt und eingetragen, danach
gilt, was in der Config steht (Benutzer kann sie dort oder per Taste ändern):
    view        "table" = Tabellen-Ansicht, "tree" = nur Links (Navigationsbäume)
    expand      einmal "Alle aufklappen" klicken (nur wenn es genau einen gibt)
    open_table  diese Tabelle (Name oder Spalte) gleich im Vollbild, "" = alle zeigen
"""

from dataclasses import asdict, dataclass, field

VIEWS = ("table", "tree")
# Tabellen: aufklappbare Tabelle, Baum bzw. Liste mit Seitenleiste
TABLE_VIEWS = ("table", "tree", "flat")


def _typed(data: dict, key: str, kind: type, default):
    """Wert aus der Config, wenn er den erwarteten Typ hat, sonst default."""
    value = data.get(key)
    return value if isinstance(value, kind) else default


def _table_view(data: dict) -> str:
    """Ansicht einer Tabelle; ältere Config hatte nur "flat": true."""
    view = _typed(data, "view", str, "")
    if view not in TABLE_VIEWS:
        view = "flat" if data.get("flat") is True else ""
    return view


@dataclass
class TablePrefs:
    """Einstellungen einer Tabelle im Vollbild."""

    cols: list[str] | None = None  # angezeigte Spalten, None = alle
    custom_on: bool = False  # eigene Spalten (Typ, Art) an
    latest: bool = False  # nur letzter Versuch
    filter: str = ""  # Zeilenfilter
    folded: list[str] | None = None  # zugeklappte Knoten, None = Startzustand
    sort: bool = False  # Geschwister A-Z (Taste a)
    view: str = ""  # TABLE_VIEWS (Taste t); "" = Standard aus den Einstellungen

    @classmethod
    def from_dict(cls, data: dict) -> "TablePrefs":
        return cls(
            cols=_typed(data, "cols", list, None),
            custom_on=_typed(data, "custom_on", bool, False),
            latest=_typed(data, "latest", bool, False),
            filter=_typed(data, "filter", str, ""),
            folded=_typed(data, "folded", list, None),
            sort=_typed(data, "sort", bool, False),
            view=_table_view(data),
        )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PageConfig:
    """Eine Seite; None = noch nicht festgelegt (wird beim Besuch erkannt)."""

    name: str = ""
    view: str | None = None
    expand: bool | None = None
    open_table: str | None = None
    tables: dict[str, TablePrefs] = field(default_factory=dict)  # TreeTable.prefs_key

    @classmethod
    def from_dict(cls, data: dict) -> "PageConfig":
        view = data.get("view") if data.get("view") in VIEWS else None
        tables = {key: TablePrefs.from_dict(prefs)
                  for key, prefs in _typed(data, "tables", dict, {}).items()}  # fmt: skip
        return cls(_typed(data, "name", str, ""), view, _typed(data, "expand", bool, None),
                   _typed(data, "open_table", str, None), tables)  # fmt: skip

    def to_dict(self) -> dict:
        return {"name": self.name, "view": self.view, "expand": self.expand,
                "open_table": self.open_table,
                "tables": {key: prefs.to_dict() for key, prefs in self.tables.items()}}  # fmt: skip

    def learn(self, name: str, view: str, expand: bool) -> None:
        """Erkannte Werte nur eintragen, wo noch nichts (Gültiges) steht -
        Benutzer-Einstellungen gehen vor."""
        self.name = self.name or name
        self.view = self.view or view
        self.expand = expand if self.expand is None else self.expand
        self.open_table = "" if self.open_table is None else self.open_table

    def toggle_view(self) -> None:
        self.view = "tree" if self.view == "table" else "table"
