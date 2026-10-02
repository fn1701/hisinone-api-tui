#!/usr/bin/env python3
"""
HISinOne Noten API
==================

Ruft den Notenspiegel einer HISinOne/QIS-Installation (getestet mit der
Hochschule Hannover) ab und gibt ihn als strukturiertes JSON zurück --
Stammdaten, Zusammenfassung (Durchschnitt / Credits) und alle Prüfungen mit
sämtlichen Tabellenspalten.

Es wird ausschließlich die offizielle Web-Oberfläche verwendet (keine private
API), mit den eigenen Zugangsdaten. Diese liegen in einer ``.env`` (siehe
``.env.example``) und gehören NICHT ins Repository.

Hintergrund der Login-Kette
---------------------------
Moderne HISinOne-Installationen zeigen die Noten teils gar nicht mehr im neuen
Frontend, sondern nur im Legacy-QIS (hier ``icms``). Der Weg dorthin:

1. Login im modernen HISinOne (``campusmanagement``): Startseite holen
   (liefert ``ajax-token`` + Session-Cookie), dann POST auf
   ``rds?state=user&type=1&category=auth.login`` mit ``asdf``/``fdsa``.
2. SSO-Brücke ``rds?state=redirect&sso=qis&myre=...`` -- der ``Location``-
   Header enthält einen Einmal-Token für das Legacy-QIS.
3. Token *sauber* einlösen: ``icms/rds?state=user&type=1&token=<TOKEN>``.
   Wichtig: nur den Token übernehmen, nicht den ``re=``-Anhang aus dem
   Location-Header (der enthält ein doppeltes ``type=8`` und würde den
   Token-Login aushebeln).
4. Über das POS-Menü die ``asi`` (Anwendungs-Session-Id) einsammeln.
5. Notenspiegel-Baum initialisieren (``tree.vm``) und die Liste (``list.vm``)
   abrufen. Die Seite ist UTF-8 kodiert (wichtig für Umlaute in der Legende).

Benutzung
---------
    python hisinone_noten.py                 # JSON nach stdout
    python hisinone_noten.py -o noten.json   # in Datei
    python hisinone_noten.py --compact       # einzeilig

Als Bibliothek:
    from hisinone_noten import HISinOneClient
    daten = HISinOneClient.from_env().get_grades()

Der Code liegt im Paket ``hisinone/noten/`` (client, qis, parser, cli);
dieses Modul reicht nur die öffentliche API und die Kommandozeile durch.
"""

from hisinone.noten import (
    HISinOneAuthError,
    HISinOneClient,
    HISinOneError,
    load_env,
    parse_notenspiegel,
)
from hisinone.noten.cli import main

__all__ = [
    "HISinOneAuthError",
    "HISinOneClient",
    "HISinOneError",
    "load_env",
    "main",
    "parse_notenspiegel",
]

if __name__ == "__main__":
    raise SystemExit(main())
