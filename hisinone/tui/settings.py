"""Alle Einstellungen der TUI (Inhalt der Config-Datei) als ein Objekt."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from hisinone.explore.page_cache import CacheOptions
from hisinone.explore.table_model import TreeTable

from .collapsed import CollapsedNodes
from .config import write_config
from .page_config import PageConfig, TablePrefs
from .shortcuts import Shortcut, default_shortcuts

DEFAULT_SAVE_PATH = "/tmp/hisinone-explore"


@dataclass
class Settings:
    tree: bool = True
    sort: bool = False
    regex: bool = False  # Filter als regulaerer Ausdruck (alle Seiten)
    save_path: str = DEFAULT_SAVE_PATH
    save_on: bool = False
    cache: CacheOptions = field(default_factory=CacheOptions)
    shortcuts: list[Shortcut] = field(default_factory=default_shortcuts)
    shortcuts_from_file: bool = False  # False -> beim Beenden einmal schreiben
    pages: dict[str, PageConfig] = field(default_factory=dict)  # Schluessel = stabile URL
    collapsed: CollapsedNodes = field(default_factory=CollapsedNodes)  # Link-Baum
    # alte Config (Tabellen ohne Seite): beim ersten Treffer in die Seite uebernehmen
    legacy_tables: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: dict) -> "Settings":
        settings = cls(
            tree=config.get("tree", True),
            sort=config.get("sort", False),
            regex=bool(config.get("regex", False)),
            save_path=config.get("save_path", DEFAULT_SAVE_PATH),
            save_on=config.get("save_on", False),
            cache=CacheOptions(
                no_cache=bool(config.get("no_cache", False)),
                ttl_seconds=int(config.get("cache_ttl", 0)),
                min_load_ms=int(config.get("cache_min_load_ms", 250)),
            ),
            collapsed=CollapsedNodes.from_config(config),
            legacy_tables=dict(config.get("tables", {})),
        )
        if "shortcuts" in config:
            settings.shortcuts = [Shortcut.from_dict(s) for s in config["shortcuts"]]
            settings.shortcuts_from_file = True
        for url, page in config.get("pages", {}).items():
            settings.pages[url] = PageConfig.from_dict(page)
        return settings

    def to_config(self, with_collapsed: bool = True) -> dict:
        config = {"tree": self.tree, "sort": self.sort, "regex": self.regex,
                  "save_on": self.save_on,
                  "save_path": self.save_path, "no_cache": self.cache.no_cache,
                  "cache_ttl": self.cache.ttl_seconds,
                  "cache_min_load_ms": self.cache.min_load_ms,
                  "shortcuts": [s.to_dict() for s in self.shortcuts],
                  "pages": {url: page.to_dict() for url, page in self.pages.items()}}  # fmt: skip
        if with_collapsed:
            config["collapsed"] = self.collapsed.paths
        if self.collapsed.overrides:  # nur aus der Datei, unveraendert zurueck
            config["collapsed_overrides"] = self.collapsed.overrides_dict()
        if self.legacy_tables:
            config["tables"] = self.legacy_tables
        return config

    def page_tables(self, url: str, tables: list[TreeTable]) -> dict[str, TablePrefs]:
        """Tabellen-Einstellungen der Seite; alte seitenlose werden uebernommen."""
        prefs = self.pages[url].tables
        for table in tables:
            key = table.prefs_key
            if key in self.legacy_tables and key not in prefs:
                prefs[key] = TablePrefs.from_dict(self.legacy_tables.pop(key))
        return prefs


class ConfigWriter:
    """Schreibt nur, wenn sich seit dem letzten Schreiben etwas geaendert hat.
    Zwischendurch zaehlt der Link-Baum (collapsed) nicht als Aenderung, beim
    Beenden schon - so erzeugt Auf-/Zuklappen keine Schreibvorgaenge."""

    def __init__(self, settings: Settings, path: Path | None):
        self.settings, self.path = settings, path  # path None = --no-config
        # Ohne "shortcuts" in der Datei: einmal schreiben, damit die
        # Standard-Tasten dort sichtbar und editierbar sind
        known = settings.shortcuts_from_file
        self.written = self._snapshot(True) if known else ""
        self.written_main = self._snapshot(False) if known else ""

    def _snapshot(self, with_collapsed: bool) -> str:
        config = self.settings.to_config(with_collapsed)
        return json.dumps(config, sort_keys=True, ensure_ascii=False)

    def save(self, final: bool = False) -> None:
        """Wirft OSError, wenn die Datei nicht schreibbar ist."""
        if self.path is None:
            return
        if final:
            changed = self._snapshot(True) != self.written
        else:
            changed = self._snapshot(False) != self.written_main
        if changed:
            write_config(self.settings.to_config(), self.path)
            self.written, self.written_main = self._snapshot(True), self._snapshot(False)
