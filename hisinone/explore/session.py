"""Login und Seitenabruf mit Pacer-Pausen."""

import requests

from hisinone.noten import HISinOneClient

from .pacer import pacer


def login(client: HISinOneClient) -> tuple[requests.Session, requests.Response]:
    """Neue Session, eingeloggt; liefert auch die Antwort (= Startseite)."""
    session = client.new_session()
    response = client.login(session, pause=pacer.step)
    return session, response


def get_page(
    session: requests.Session, url: str, referer: str | None, timeout: int
) -> requests.Response:
    """Eine Seite wie per Klick laden (Pause davor, Referer, Encoding gesetzt)."""
    pacer.step()
    headers = {"Referer": referer} if referer else {}
    response = session.get(url, timeout=timeout, headers=headers)
    response.encoding = response.encoding or "utf-8"
    return response


def is_html(response: requests.Response) -> bool:
    return "text/html" in response.headers.get("Content-Type", "text/html")
