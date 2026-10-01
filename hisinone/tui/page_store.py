"""Anbindung des Seiten-Caches an die App: CurrentPage und Tabellen rein
und raus, nur langsame Seiten werden gespeichert."""

from hisinone.explore.page_cache import CachedPage, CacheOptions, PageCache
from hisinone.explore.table_model import TreeTable

from .current_page import CurrentPage


class PageStore:
    """Wie PageCache, aber mit den Objekten der Oberflaeche; ohne nutzbaren
    Ordner oder mit no_cache einfach aus (dann wird immer geladen)."""

    def __init__(self, options: CacheOptions):
        self.min_seconds = options.min_load_ms / 1000
        try:
            self.cache = None if options.no_cache else PageCache(options.path, options.ttl_seconds)
        except OSError:
            self.cache = None

    def get(self, stable_url: str, view: str) -> tuple[CurrentPage, list[TreeTable]] | None:
        """None auch, wenn die Tabellen-Ansicht gewuenscht ist, aber keine
        Tabellen gespeichert sind (Klicks brauchen eine frische Seite)."""
        cached = self.cache.get(stable_url) if self.cache else None
        if not cached or (view == "table" and not cached.tables):
            return None
        page = CurrentPage(cached.stable_url, cached.name, cached.server_url, cached.html,
                           pulled_at=cached.pulled_at, from_cache=True)  # fmt: skip
        return page, cached.tables

    def put(self, page: CurrentPage, tables: list[TreeTable], seconds: float) -> None:
        if not self.cache or seconds <= self.min_seconds:
            return
        self.cache.put(CachedPage(page.stable_url, page.server_url, page.name, page.html,
                                  page.pulled_at, tables))  # fmt: skip
