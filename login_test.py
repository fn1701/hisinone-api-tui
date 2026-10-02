#!/usr/bin/env python3
"""
Prüft nur den Login ins moderne HISinOne (Zugangsdaten aus .env).

Benutzung
---------
1. Abhängigkeit installieren:
       pip install -r requirements.txt
2. .env anlegen (im Projekt-Hauptordner, neben diesem Skript):
       cp .env.example .env
   und HISINONE_USERNAME / HISINONE_PASSWORD eintragen. Für eine andere
   Hochschule als die HS Hannover zusätzlich HISINONE_BASE_URL anpassen.
3. Aus dem Projekt-Hauptordner starten:
       python login_test.py

Ergebnis
--------
"Login OK"      -> Login per Skript funktioniert (Exit-Code 0).
"Login FAILED"  -> Login abgelehnt oder anderes Login-Verfahren, z. B.
                   Shibboleth/SSO (Exit-Code 1). Hinweise dazu geben die
                   ausgegebenen URLs und ob ein ajax-token gefunden wurde.
"""

import sys

import requests

from hisinone.noten import HISinOneAuthError, HISinOneClient, HISinOneError
from hisinone.noten.client import START_PAGE


def print_start_page(client: HISinOneClient) -> None:
    """Diagnose vor dem Login: erreichbar? ajax-token vorhanden?"""
    start = client.new_session().get(client.qis_base + START_PAGE, timeout=client.timeout)
    print(f"Startseite: HTTP {start.status_code} -> {start.url}")
    print(f"ajax-token gefunden: {'ja' if client.find_ajax_token(start.text) else 'nein'}")


def main() -> int:
    try:
        client = HISinOneClient.from_env()
    except HISinOneError as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    print_start_page(client)
    try:
        response = client.login(client.new_session())
    except (HISinOneAuthError, requests.RequestException):
        print("Login FAILED")
        return 1
    print(f"Login-POST: HTTP {response.status_code} -> {response.url}")
    print("Login OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
