"""Datenmodell einer Baum-Tabelle."""

from dataclasses import dataclass, field

# Eine Zeile: {"tiefe": int, "typ": Symbol-Name, <Spaltenkopf>: Text, ...}
Row = dict


@dataclass
class TreeTable:
    name: str  # Überschrift vor der Tabelle ("" wenn keine)
    cols: list[str]  # Spaltenköpfe der Seite
    rows: list[Row]
    custom: list[str] = field(default_factory=list)  # eigene, berechnete Spalten
    start_folded: bool = False  # große Bäume: anfangs nur die oberste Ebene zeigen

    @property
    def title_col(self) -> str:
        """Spalte mit dem (eingerückten) Titel: die erste außer "Ebene"."""
        return next((col for col in self.cols if col != "Ebene"), "")

    @property
    def display_name(self) -> str:
        """Überschrift, sonst der erste Titel (Wurzel des Baums)."""
        if self.name:
            return self.name
        return next((row[self.title_col] for row in self.rows if row.get(self.title_col)),
                    "Tabelle")  # fmt: skip

    @property
    def prefs_key(self) -> str:
        """Schlüssel der Tabellen-Einstellungen in der Config."""
        return f"{self.display_name} [{','.join(self.cols)}]"
