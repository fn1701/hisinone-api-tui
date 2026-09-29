"""Datenmodell einer Baum-Tabelle."""

from dataclasses import dataclass, field

# Eine Zeile: {"tiefe": int, "typ": Symbol-Name, <Spaltenkopf>: Text, ...}
Row = dict


@dataclass
class TreeTable:
    name: str  # Ueberschrift vor der Tabelle ("" wenn keine)
    cols: list[str]  # Spaltenkoepfe der Seite
    rows: list[Row]
    custom: list[str] = field(default_factory=list)  # eigene, berechnete Spalten

    @property
    def title_col(self) -> str:
        """Spalte mit dem (eingerueckten) Titel: die erste ausser "Ebene"."""
        return next((col for col in self.cols if col != "Ebene"), "")

    @property
    def display_name(self) -> str:
        """Ueberschrift, sonst der erste Titel (Wurzel des Baums)."""
        if self.name:
            return self.name
        return next((row[self.title_col] for row in self.rows if row.get(self.title_col)),
                    "Tabelle")  # fmt: skip

    @property
    def prefs_key(self) -> str:
        """Schluessel der Tabellen-Einstellungen in der Config."""
        return f"{self.display_name} [{','.join(self.cols)}]"
