"""Tasten, die eine feste Seite oeffnen (Config "shortcuts")."""

from dataclasses import asdict, dataclass

from hisinone.explore.leistungen import LEISTUNGEN_PATH


@dataclass
class Shortcut:
    key: str
    description: str
    path: str  # relativ zur HISinOne-Adresse oder volle URL
    # nach dem Laden die erste Tabelle mit dieser Spalte im Vollbild ("" = alle)
    open_table_with_column: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Shortcut":
        key = str(data.get("key", ""))
        return cls(key, str(data.get("description", key)), str(data.get("path", "")),
                   str(data.get("open_table_with_column", "")))  # fmt: skip

    def to_dict(self) -> dict:
        return asdict(self)

    def url(self, qis_base: str) -> str:
        if self.path.startswith(("http://", "https://")):
            return self.path
        return qis_base + self.path


def default_shortcuts() -> list[Shortcut]:
    return [Shortcut("l", "Leistungen", LEISTUNGEN_PATH, "Versuch")]
