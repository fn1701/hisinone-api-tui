"""Zugeklappte Knoten im Link-Baum: global für alle Seiten (die Navigation
steht überall), dazu Ausnahmen je Seite, die nur in der Config-Datei stehen.

Pfade haben die Form "Eltern › Kind"; alles nicht Zugeklappte ist offen.
"""

from dataclasses import dataclass, field


@dataclass
class CollapsedOverride:
    """Ausnahme für eine Seite: diese Pfade immer offen bzw. immer zu."""

    open: list[str] = field(default_factory=list)
    closed: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "CollapsedOverride":
        return cls(open=list(data.get("open", [])), closed=list(data.get("closed", [])))

    def to_dict(self) -> dict:
        return {"open": self.open, "closed": self.closed}


@dataclass
class CollapsedNodes:
    """Globale Menge plus Ausnahmen; Auf-/Zuklappen in der TUI ändert nur
    die globale Menge, die Ausnahmen gewinnen beim Anzeigen."""

    paths: list[str] = field(default_factory=list)
    overrides: dict[str, CollapsedOverride] = field(default_factory=dict)  # stabile URL

    @classmethod
    def from_config(cls, config: dict) -> "CollapsedNodes":
        overrides = {url: CollapsedOverride.from_dict(data)
                     for url, data in config.get("collapsed_overrides", {}).items()}  # fmt: skip
        return cls(cls._merged(config.get("collapsed", [])), overrides)

    @staticmethod
    def _merged(value: list[str] | dict[str, list[str]]) -> list[str]:
        """Alte Config hatte die Pfade je Seite: dann alle zusammenfassen."""
        if not isinstance(value, dict):
            return sorted(set(value))
        paths: set[str] = set()
        for page_paths in value.values():
            paths.update(page_paths)
        return sorted(paths)

    def for_page(self, url: str) -> set[str]:
        """Auf dieser Seite zugeklappte Pfade (global + Ausnahmen)."""
        override = self.overrides.get(url, CollapsedOverride())
        return (set(self.paths) | set(override.closed)) - set(override.open)

    def set_global(self, paths: set[str]) -> None:
        self.paths = sorted(paths)

    def overrides_dict(self) -> dict:
        return {url: override.to_dict() for url, override in self.overrides.items()}
