"""Navigation der Kommandozeile: aktuelle Seite, Verlauf, Speichern."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import requests

from hisinone.noten import HISinOneClient

from .html_text import link_name, page_title
from .links import clean_url
from .session import get_page, is_html
from .storage import save_html


@dataclass
class Page:
    # stable_url ohne _flowExecutionKey: "b" und "r" nutzen nie einen
    # veralteten Flow-Key; server_url = wohin HISinOne umgeleitet hat
    stable_url: str
    name: str  # angeklickter Linkname
    server_url: str
    html: str


class PageBrowser:
    """Eingeloggte Session plus aktuelle Seite und Verlauf (stabile URLs)."""

    def __init__(self, client: HISinOneClient, session: requests.Session,
                 start: requests.Response, save_dir: Path | None):  # fmt: skip
        self.client, self.session, self.save_dir = client, session, save_dir
        self.home_url = clean_url(start.url)
        self.host = urlsplit(self.home_url).netloc
        self.history: list[tuple[str, str]] = []  # [(stabile URL, Name)]
        self.page = Page(self.home_url, "Startseite", start.url, start.text)
        self.save_current()

    def save(self, url: str, html: str, name: str) -> None:
        """Nur wenn Speichern an ist (--save)."""
        if self.save_dir:
            print(f"[gespeichert: {save_html(self.save_dir, url, html, name)}]")

    def save_current(self) -> None:
        self.save(self.page.server_url, self.page.html, self.page.name)

    def open(self, url: str, name: str = "", push: bool = True) -> bool:
        try:
            response = get_page(self.session, url, self.page.server_url, self.client.timeout)
        except requests.RequestException as error:
            print(f"Fehler: {error}")
            return False
        if not is_html(response):
            ctype = response.headers.get("Content-Type")
            print(f"Kein HTML ({ctype}), {len(response.content)} Bytes.")
            return False
        if push:
            self.history.append((self.page.stable_url, self.page.name))
        name = link_name(name) or page_title(response.text)
        self.page = Page(clean_url(url), name, response.url, response.text)
        self.save_current()
        if response.status_code != 200:
            print(f"HTTP {response.status_code}")
        return True

    def back(self) -> None:
        if not self.history:
            print("Kein Verlauf.")
            return
        url, name = self.history.pop()
        self.open(url, name, push=False)

    def reload(self) -> None:
        self.open(self.page.stable_url, self.page.name, push=False)

    def home(self) -> None:
        self.open(self.home_url, "Startseite")
