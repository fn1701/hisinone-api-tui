"""Zwischenspeicher für langsame Seiten: weniger Requests, schneller.

Pro stabiler URL eine JSON-Datei mit dem Seiten-HTML, den schon geladenen
Tabellen (nach allen Klicks wie "Alle aufklappen") und dem Abrufzeitpunkt.
Enthält Noten -> Ordner 0700, Dateien 0600.
"""

import hashlib
import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .storage import prepare_save_dir
from .table_model import TreeTable

DEFAULT_CACHE_PATH = "/tmp/hisinone-cache"


@dataclass
class CacheOptions:
    """Einstellungen des Caches (Config-Datei bzw. Kommandozeile)."""

    no_cache: bool = False  # True = nie lesen, nie schreiben
    ttl_seconds: int = 0  # 0 = unbegrenzt, d.h. bis /tmp beim Neustart geleert wird
    min_load_ms: int = 250  # langsamer geladene Seiten werden gespeichert
    path: str = DEFAULT_CACHE_PATH


@dataclass
class CachedPage:
    stable_url: str
    server_url: str
    name: str
    html: str
    pulled_at: float  # time.time() des Abrufs
    tables: list[TreeTable] = field(default_factory=list)


class PageCache:
    """Liest und schreibt CachedPage-Dateien in einem privaten Ordner."""

    def __init__(self, path: str = DEFAULT_CACHE_PATH, ttl_seconds: int = 0):
        self.directory = prepare_save_dir(path)
        self.ttl_seconds = ttl_seconds

    def get(self, stable_url: str) -> CachedPage | None:
        """None, wenn nicht gespeichert, abgelaufen oder unlesbar (dann
        einfach neu laden)."""
        try:
            data = json.loads(self._path(stable_url).read_text(encoding="utf-8"))
            data["tables"] = [TreeTable(**table) for table in data.get("tables", [])]
            page = CachedPage(**data)
        except (OSError, ValueError, TypeError):
            return None
        if self._expired(page):
            self.drop(stable_url)
            return None
        return page

    def _expired(self, page: CachedPage) -> bool:
        return self.ttl_seconds > 0 and time.time() - page.pulled_at > self.ttl_seconds

    def put(self, page: CachedPage) -> None:
        path = self._path(page.stable_url)
        # Erst anlegen mit 0600, dann schreiben: nie kurz für andere lesbar
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            json.dump(asdict(page), file, ensure_ascii=False)

    def drop(self, stable_url: str) -> None:
        self._path(stable_url).unlink(missing_ok=True)

    def _path(self, stable_url: str) -> Path:
        digest = hashlib.sha256(stable_url.encode("utf-8")).hexdigest()[:32]
        return self.directory / f"{digest}.json"


def pulled_text(pulled_at: float) -> str:
    """Abrufzeitpunkt für die Anzeige, z.B. "29.09.2026 19:41"."""
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(pulled_at))
