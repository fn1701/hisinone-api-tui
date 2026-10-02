"""Mittlere Schicht der App: Login und Seiten laden (im Hintergrund-Thread,
damit die Oberfläche nicht hängt), Seiten mit Baum-Tabelle als Tabellen."""

import time
from urllib.parse import urlsplit

import requests
from textual import work

from hisinone.explore.html_text import link_name, page_title
from hisinone.explore.links import clean_url
from hisinone.explore.page_tables import has_tables, load_tables
from hisinone.explore.session import get_page, is_html, login
from hisinone.explore.table_model import TreeTable
from hisinone.explore.tree_tables import parse_tree_tables
from hisinone.noten import HISinOneClient, HISinOneError

from .current_page import CurrentPage, LoadedTables
from .first_visit import FirstVisit
from .link_app import LinkTreeApp
from .page_store import PageStore
from .special_pages import SpecialPages
from .table_display import TableDisplay


class LoadingApp(FirstVisit, SpecialPages, TableDisplay, LinkTreeApp):
    def __init__(self, settings):
        super().__init__(settings)
        self.session: requests.Session | None = None
        self.client: HISinOneClient | None = None
        self.home_url = ""
        self.history: list[tuple[str, str]] = []  # (stabile URL, Name)
        self.store = PageStore(settings.cache)
        self.planner_choices = {}

    @work(thread=True, exclusive=True)
    def do_login(self) -> None:
        try:
            self.client = HISinOneClient.from_env()
            self.session, response = login(self.client)
        except (HISinOneError, requests.RequestException) as error:
            self.call_from_thread(self.exit, message=f"Fehler: {error}")
            return
        self.home_url = clean_url(response.url)
        self.host = urlsplit(self.home_url).netloc
        start = CurrentPage(self.home_url, "Startseite", response.url, response.text)
        self.call_from_thread(self.show_page, start)

    def open(
        self, url: str, name: str, push: bool = True, open_col: str = "", fresh: bool = False
    ) -> None:
        """fresh: am Cache vorbei neu vom Server laden (Taste r)."""
        self.link_tree.loading = True
        self.fetch(url, name, push, open_col, fresh)

    @work(thread=True, exclusive=True)
    def fetch(
        self, url: str, name: str, push: bool = True, open_col: str = "", fresh: bool = False
    ) -> None:
        """open_col: danach die erste Tabelle mit dieser Spalte im Vollbild (Taste l)."""
        if not fresh and self._show_cached(clean_url(url), push, open_col):
            return
        started = time.monotonic()
        response = self._get(url)
        if response is None:
            return
        name = link_name(name) or page_title(response.text)
        page = CurrentPage(clean_url(url), name, response.url, response.text,
                           pulled_at=time.time())  # fmt: skip
        self.call_from_thread(self.enter_page, page, push)
        tables = self._fetched_tables(page, open_col)
        self.store.put(page, tables, time.monotonic() - started)

    def _fetched_tables(self, page: CurrentPage, open_col: str) -> list[TreeTable]:
        """Tabellen der neu geladenen Seite zeigen (je nach Config)."""
        if self.call_from_thread(self.show_special, page):
            return []
        if not has_tables(page.html):
            if open_col:
                self.call_from_thread(self.notify, "Keine Tabelle auf der Seite (abgemeldet?).",
                                      severity="warning")  # fmt: skip
            return []
        config = self.settings.pages.get(page.stable_url)
        if config is None or config.view is None:
            return self._first_visit(page, open_col)
        if config.view != "table":
            return []
        tables, html = self._expanded(page, config.expand)
        return self._show_tables(page, tables, html, open_col or config.open_table)

    def _show_cached(self, stable_url: str, push: bool, open_col: str) -> bool:
        """Seite (und ggf. Tabellen) aus dem Cache zeigen; False = nicht da."""
        config = self.settings.pages.get(stable_url)
        cached = self.store.get(stable_url, config.view if config else "tree")
        if not cached:
            return False
        page, tables = cached
        if has_tables(page.html) and (config is None or config.view is None):
            return False  # Ansicht noch unbekannt: neu laden, aufklappen, erkennen
        self.call_from_thread(self.enter_page, page, push)
        if self.call_from_thread(self.show_special, page):
            pass  # alte Planer-Einträge haben noch Tabellen
        elif tables:
            loaded = LoadedTables(page, tables, None, open_col or config.open_table)
            self.call_from_thread(self.show_tree_tables, loaded)
        return True

    def enter_page(self, page: CurrentPage, push: bool) -> None:
        if push and self.page.stable_url:
            self.history.append((self.page.stable_url, self.page.name))
        self.show_page(page)

    def _get(self, url: str) -> requests.Response | None:
        """None = Fehler (schon gemeldet)."""
        try:
            response = get_page(self.session, url, self.page.server_url, self.client.timeout)
        except requests.RequestException as error:
            self.call_from_thread(self.fetch_failed, f"Fehler: {error}")
            return None
        if not is_html(response):
            content_type = response.headers.get("Content-Type")
            message = f"Kein HTML ({content_type}), {len(response.content)} Bytes."
            self.call_from_thread(self.fetch_failed, message)
            return None
        if response.status_code != 200:
            self.call_from_thread(self.notify, f"HTTP {response.status_code}", severity="warning")
        return response

    def _expanded(self, page: CurrentPage, expand: bool) -> tuple[list[TreeTable], str]:
        """(Tabellen, HTML) - wenn möglich nach einmal "Alle aufklappen"."""
        try:
            return load_tables(self.session, page.server_url, page.html, self.client.timeout,
                               expand)  # fmt: skip
        except (HISinOneError, requests.RequestException) as error:
            self.call_from_thread(self.notify, f"Aufklappen fehlgeschlagen: {error}",
                                  severity="warning")  # fmt: skip
            return parse_tree_tables(page.html), page.html

    def _show_tables(
        self, page: CurrentPage, tables: list[TreeTable], html: str, open_col: str
    ) -> list[TreeTable]:
        if tables:
            expanded = html if html is not page.html else None
            self.call_from_thread(self.show_tree_tables, LoadedTables(page, tables, expanded,
                                                                      open_col))  # fmt: skip
        return tables
