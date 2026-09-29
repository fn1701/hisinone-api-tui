#!/usr/bin/env python3
"""
Prueft nur den Login ins moderne HISinOne (Zugangsdaten aus .env).

Benutzung
---------
1. Abhaengigkeit installieren:
       pip install -r requirements.txt
2. .env anlegen (im Projekt-Hauptordner, neben diesem Skript):
       cp .env.example .env
   und HISINONE_USERNAME / HISINONE_PASSWORD eintragen. Fuer eine andere
   Hochschule als die HS Hannover zusaetzlich HISINONE_BASE_URL anpassen.
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

from hisinone_noten import HISinOneClient, HISinOneError


def main() -> int:
    try:
        c = HISinOneClient.from_env()
    except HISinOneError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1

    s = c._new_session()
    start = s.get(f"{c.qis_base}/pages/cs/sys/portal/hisinoneStartPage.faces",
                  timeout=c.timeout)
    print(f"Startseite: HTTP {start.status_code} -> {start.url}")
    token = c._find_ajax_token(start.text)
    print(f"ajax-token gefunden: {'ja' if token else 'nein'}")

    r = s.post(f"{c.qis_base}/rds?state=user&type=1&category=auth.login",
               data={"userInfo": "", "ajax-token": token,
                     "asdf": c.username, "fdsa": c.password, "submit": ""},
               headers={"Origin": c.base_url, "Referer": start.url},
               timeout=c.timeout)
    print(f"Login-POST: HTTP {r.status_code} -> {r.url}")

    if "abmelden" in r.text.lower():
        print("Login OK")
        return 0
    print("Login FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
