"""Anbindung des Seiten-Caches an die App: CurrentPage und Tabellen rein
und raus, nur langsame Seiten werden gespeichert."""

from hisinone.explore.page_cache import CachedPage, CacheOptions, PageCache
from hisinone.explore.planner import is_study_planner
from hisinone.explore.table_model import TreeTable

from .current_page import CurrentPage


class PageStore:
    """Wie PageCache, aber mit den Objekten der Oberfläche; ohne nutzbaren
    Ordner oder mit no_cache einfach aus (dann wird immer geladen)."""

    def __init__(self, options: CacheOptions):
        self.min_seconds = options.min_load_ms / 1000
        try:
            self.cache = None if options.no_cache else PageCache(options.path, options.ttl_seconds)
        except OSError:
            self.cache = None

    def get(self, stable_url: str, view: str) -> tuple[CurrentPage, list[TreeTable]] | None:
        """None auch, wenn die Tabellen-Ansicht gewünscht ist, aber keine
        Tabellen gespeichert sind (Klicks brauchen eine frische Seite); der
        Studienplaner speichert seine Tabellen je Filter extra."""
        cached = self.cache.get(stable_url) if self.cache else None
        if not cached:
            return None
        if view == "table" and not cached.tables and not is_study_planner(cached.html):
            return None
        page = CurrentPage(cached.stable_url, cached.name, cached.server_url, cached.html,
                           pulled_at=cached.pulled_at, from_cache=True)  # fmt: skip
        return page, cached.tables

    def put(self, page: CurrentPage, tables: list[TreeTable], seconds: float) -> None:
        if not self.cache or seconds <= self.min_seconds:
            return
        self.cache.put(CachedPage(page.stable_url, page.server_url, page.name, page.html,
                                  page.pulled_at, tables))  # fmt: skip

    def update_table(self, stable_url: str, table: TreeTable) -> None:
        """Geänderte Tabelle (z.B. eingefügter Unterbaum) im Cache der Seite
        ersetzen; ist die Seite nicht gecacht, bleibt es dabei."""
        cached = self.cache.get(stable_url) if self.cache else None
        if not cached:
            return
        keys = [old.prefs_key for old in cached.tables]
        if table.prefs_key in keys:
            cached.tables[keys.index(table.prefs_key)] = table
            self.cache.put(cached)

    def get_tables(self, key: str) -> tuple[float, list[TreeTable]] | None:
        """(Abrufzeitpunkt, Tabellen) einer Variante, z.B. Seite + Filter."""
        cached = self.cache.get(key) if self.cache else None
        return (cached.pulled_at, cached.tables) if cached and cached.tables else None

    def put_tables(self, key: str, page: CurrentPage, tables: list[TreeTable], seconds: float):
        """Wie put, aber ohne HTML (die Variante wird nur als Tabelle gezeigt)."""
        if not self.cache or seconds <= self.min_seconds or not tables:
            return
        self.cache.put(CachedPage(key, page.server_url, page.name, "", page.pulled_at, tables))
