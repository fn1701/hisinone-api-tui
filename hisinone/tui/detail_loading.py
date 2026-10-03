"""Detailseiten in der App: aus einer Tabellenzeile über der Tabelle
öffnen (Esc führt zurück) und ihre Registerkarten laden. Immer erst aus
dem Cache (je Registerkarte ein Eintrag), sonst Seite frisch holen und den
Knopf der Registerkarte absenden."""

import time
from urllib.parse import urljoin

import requests
from textual import work

from hisinone.explore.collapsed_panels import collapsed_panels, open_panels
from hisinone.explore.detail_tabs import DetailTab, base_url, click_tab, tab_key
from hisinone.explore.detail_view import has_detail_view
from hisinone.explore.html_text import link_name, page_title
from hisinone.explore.links import clean_url
from hisinone.noten import HISinOneError

from .current_page import CurrentPage
from .detail_screen import DetailScreen


class DetailLoading:
    """Mixin für LoadingApp (nutzt session, client, store, _get, open_as_page)."""

    def open_from_table(self, href: str, name: str) -> None:
        """Link einer Tabellenzeile (relativ zur aktuellen Seite) öffnen."""
        self._open_linked(urljoin(self.page.server_url, href), name)

    @work(thread=True, exclusive=True)
    def _open_linked(self, url: str, name: str) -> None:
        """Detailseite über der Tabelle zeigen, andere Seiten wie bisher."""
        cached = self.store.get(clean_url(url), "")
        page = cached[0] if cached else self._fetch_linked(url, name)
        if page is None:
            return
        if has_detail_view(page.html):
            self.call_from_thread(self.push_screen, DetailScreen(page))
        else:
            self.call_from_thread(self.open_as_page, url, name)

    def _fetch_linked(self, url: str, name: str) -> CurrentPage | None:
        response = self._get(url)
        if response is None:
            return None
        name = link_name(name) or page_title(response.text)
        page = CurrentPage(clean_url(url), name, response.url, self.page_html(response),
                           pulled_at=time.time())  # fmt: skip
        if has_detail_view(page.html):
            self.store.put(page, [], float("inf"))  # Detailseiten immer cachen
        return page

    @work(thread=True, exclusive=True)
    def load_detail_tab(self, page: CurrentPage, tab: DetailTab, fresh: bool) -> None:
        """Ergebnis per screen.show_page; None = Fehler (schon gemeldet)."""
        screen = self.screen
        key = tab_key(page.stable_url, tab)
        cached = None if fresh else self.store.get(key, "")
        loaded = cached[0] if cached else self._fetch_tab(page, tab, key)
        self.call_from_thread(screen.show_page, loaded)

    def _fetch_tab(self, page: CurrentPage, tab: DetailTab, key: str) -> CurrentPage | None:
        """Frische Seite (gültiger ViewState), dann Registerkarte absenden."""
        fresh = self._get(base_url(page.stable_url))
        if fresh is None:
            return None
        try:
            response = click_tab(self.session, fresh.url, fresh.text, tab, self.client.timeout)
        except (HISinOneError, requests.RequestException) as error:
            self.call_from_thread(self.notify, f"Laden fehlgeschlagen: {error}", severity="error")
            return None
        if not has_detail_view(response.text):
            self.call_from_thread(self.notify, "Registerkarte nicht geladen (unerwartete Seite).",
                                  severity="error")  # fmt: skip
            return None
        loaded = CurrentPage(key, page.name, response.url, self.page_html(response),
                             pulled_at=time.time())  # fmt: skip
        self.store.put(loaded, [], float("inf"))  # Registerkarten immer cachen
        return loaded

    def page_html(self, response: requests.Response) -> str:
        """HTML der Seite; bei Detailseiten mit geöffneten zugeklappten
        Abschnitten (sonst fehlt deren Inhalt, z.B. eine Parallelgruppe)."""
        html = response.text
        if not has_detail_view(html) or not collapsed_panels(html):
            return html
        try:
            return open_panels(self.session, response.url, html, self.client.timeout)
        except (HISinOneError, requests.RequestException) as error:
            self.call_from_thread(self.notify, f"Zugeklappte Abschnitte nicht geladen: {error}",
                                  severity="warning")  # fmt: skip
            return html
