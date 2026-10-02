#!/usr/bin/env python3
"""
Debug für die Leistungen-Seite: Login, Leistungen laden, einmal "Alle
aufklappen" (4 Requests, mit Pacer-Pausen). Gibt nur Struktur/Zähler aus,
keine Noten. Rohdaten landen in /tmp/hisinone-explore/ (0700, persönlich!).

    .venv/bin/python debug_leistungen.py
"""

import requests

from hisinone.explore.jsf import jsf_click
from hisinone.explore.leistungen import (
    EXPAND_ALL,
    LEISTUNGEN_FORM,
    LEISTUNGEN_PATH,
    parse_leistungen,
)
from hisinone.explore.session import get_page, login
from hisinone.explore.storage import prepare_save_dir, save_html
from hisinone.noten import HISinOneClient

SAVE_DIR = "/tmp/hisinone-explore"


class RecordingSession:
    """Leitet an die Session weiter und merkt sich die letzte POST-Antwort -
    auch wenn jsf_click sie nicht versteht."""

    def __init__(self, session: requests.Session):
        self.session = session
        self.last_post: requests.Response | None = None

    def post(self, *args, **kwargs) -> requests.Response:
        self.last_post = self.session.post(*args, **kwargs)
        return self.last_post


def report_page(page: requests.Response, save_dir) -> None:
    print(f"GET {page.status_code} {page.url}")
    print("  Formular examsReadonly:", f'id="{LEISTUNGEN_FORM}"' in page.text)
    print("  Button Alle aufklappen:", f'id="{EXPAND_ALL}"' in page.text)
    print("  Zeilen (zugeklappt):", len(parse_leistungen(page.text)))
    print("  ->", save_html(save_dir, page.url, page.text, "debug_get"))


def report_expand(recorder: RecordingSession, page: requests.Response, timeout: int) -> None:
    try:
        fragment = jsf_click(recorder, page.url, page.text, LEISTUNGEN_FORM, EXPAND_ALL, timeout)
        rows = parse_leistungen(fragment)
        print("Zeilen (aufgeklappt):", len(rows))
        print("  Tiefe/Typ:", sorted({(row["tiefe"], row["typ"]) for row in rows}))
    except Exception as error:  # noqa: BLE001 - Debug: jeden Fehler anzeigen
        print("FEHLER:", type(error).__name__, error)


def report_post(post: requests.Response | None, save_dir) -> None:
    if post is None:
        return
    print(f"POST {post.status_code} {post.headers.get('Content-Type')} {len(post.text)} Zeichen")
    print("  Anfang:", post.text[:300].replace("\n", " "))
    print("  ->", save_html(save_dir, post.url, post.text, "debug_post"))


def main() -> int:
    client = HISinOneClient.from_env()
    session, _ = login(client)
    print("Login OK")
    save_dir = prepare_save_dir(SAVE_DIR)
    page = get_page(session, client.qis_base + LEISTUNGEN_PATH, None, client.timeout)
    page.encoding = "utf-8"
    report_page(page, save_dir)
    recorder = RecordingSession(session)
    report_expand(recorder, page, client.timeout)
    report_post(recorder.last_post, save_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
