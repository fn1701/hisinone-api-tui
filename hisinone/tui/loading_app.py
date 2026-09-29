"""Mittlere Schicht der App: Login und Seiten laden (im Hintergrund-Thread,
damit die Oberflaeche nicht haengt), Seiten mit Baum-Tabelle als Tabellen."""

from dataclasses import dataclass
from urllib.parse import urlsplit

import requests
from textual import work

from hisinone.explore.custom_columns import is_data_table
from hisinone.explore.expand import can_expand_all, expand_tree_tables
from hisinone.explore.html_text import link_name, page_title
from hisinone.explore.links import clean_url
from hisinone.explore.session import get_page, is_html, login
from hisinone.explore.storage import save_html
from hisinone.explore.table_model import TreeTable
from hisinone.explore.tree_tables import TREE_TABLE, parse_tree_tables
from hisinone.noten import HISinOneClient, HISinOneError

from .current_page import CurrentPage
from .link_app import LinkTreeApp
from .page_config import PageConfig
from .tables_screen import TreeTablesScreen


@dataclass
class LoadedTables:
    page: CurrentPage  # Seite, zu der die Tabellen gehoeren
    tables: list[TreeTable]
    expanded_html: str | None  # Ajax-Antwort von "Alle aufklappen", sonst None
    open_col: str  # diese Tabelle (Spalte oder Name) gleich im Vollbild


class LoadingApp(LinkTreeApp):
    def __init__(self, settings):
        super().__init__(settings)
        self.session: requests.Session | None = None
        self.client: HISinOneClient | None = None
        self.home_url = ""
        self.history: list[tuple[str, str]] = []  # (stabile URL, Name)

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

    def open(self, url: str, name: str, push: bool = True, open_col: str = "") -> None:
        self.link_tree.loading = True
        self.fetch(url, name, push, open_col)

    @work(thread=True, exclusive=True)
    def fetch(self, url: str, name: str, push: bool = True, open_col: str = "") -> None:
        """open_col: danach die erste Tabelle mit dieser Spalte im Vollbild (Taste l)."""
        response = self._get(url)
        if response is None:
            return
        name = link_name(name) or page_title(response.text)
        page = CurrentPage(clean_url(url), name, response.url, response.text)
        self.call_from_thread(self.enter_page, page, push)
        config = self._page_config(page) if TREE_TABLE.search(page.html) else None
        if config:
            open_col = open_col or config.open_table
        if config and config.view == "table":
            self._load_tables(page, open_col, config.expand)
        elif open_col:
            self.call_from_thread(self.notify, "Keine Tabelle auf der Seite (abgemeldet?).",
                                  severity="warning")  # fmt: skip

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

    def _page_config(self, page: CurrentPage) -> PageConfig:
        """Ansicht je Seite aus der Config; neu erkannt: reine Navigations-
        Baeume (nur Ebene/Titel/Aktionen) -> "tree" = nur als Links."""
        has_data = any(is_data_table(table) for table in parse_tree_tables(page.html))
        view = "table" if has_data else "tree"
        expand = can_expand_all(page.html)
        return self.call_from_thread(self.learn_page, page, view, expand)

    def learn_page(self, page: CurrentPage, view: str, expand: bool) -> PageConfig:
        config = self.settings.pages.setdefault(page.stable_url, PageConfig())
        config.learn(page.name, view, expand)
        return config

    def _load_tables(self, page: CurrentPage, open_col: str, expand: bool) -> None:
        """Wenn moeglich einmal "Alle aufklappen" (wie ein Klick im Browser)."""
        try:
            tables, html = expand_tree_tables(self.session, page.server_url, page.html,
                                              self.client.timeout, expand)  # fmt: skip
        except (HISinOneError, requests.RequestException) as error:
            self.call_from_thread(self.notify, f"Aufklappen fehlgeschlagen: {error}",
                                  severity="warning")  # fmt: skip
            tables, html = parse_tree_tables(page.html), page.html
        if tables:
            expanded = html if html is not page.html else None
            self.call_from_thread(self.show_tree_tables, LoadedTables(page, tables, expanded,
                                                                      open_col))  # fmt: skip

    def show_tree_tables(self, loaded: LoadedTables) -> None:
        page = loaded.page
        if loaded.expanded_html and self.save_dir:
            save_html(self.save_dir, page.server_url, loaded.expanded_html,
                      f"{page.name}_aufgeklappt")  # fmt: skip
        prefs = self.settings.page_tables(page.stable_url, loaded.tables)
        screen = TreeTablesScreen(page.name, loaded.tables, prefs)
        self.push_screen(screen)
        # Taste l: gleich die Leistungsdaten im Vollbild (Esc -> alle Tabellen)
        screen.open_matching(loaded.open_col)

    def fetch_failed(self, message: str) -> None:
        self.link_tree.loading = False
        self.notify(message, severity="error")
