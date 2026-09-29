#!/usr/bin/env python3
"""
Leistungen (Mein Studium > Leistungen) komplett aufgeklappt abrufen, filtern
und als Tabelle, JSON oder CSV ausgeben. 4 Requests: Login (2), Seite,
"Alle aufklappen" - mit Zufallspausen dazwischen (Pacer in explore.py).

Benutzung (aus dem Projekt-Hauptordner, .env wie bei login_test.py):
    .venv/bin/python leistungen.py                      # Baum als Tabelle
    .venv/bin/python leistungen.py --pl                 # nur PL/PVL, flach
    .venv/bin/python leistungen.py --pl --latest        # ... nur letzter Versuch
    .venv/bin/python leistungen.py --cols titel,Note,CP,Status
    .venv/bin/python leistungen.py --pl -o leistungen.csv   # oder .json

Filter:
    --pl      nur Pruefungen: Titel endet auf (PL)/(PVL), oder es steht eine
              Note (Zahl) drin und der Typ ist nicht Modul/Konto (-> PL)
    --latest  fruehere Versuche ausblenden: Versuche sind Geschwister im Baum
              (gleicher Elternknoten + gleiche Art); es bleibt der hoechste

Spalten (--cols, Schluessel oder Anzeigename, kommagetrennt):
    Ebene, Typ, Art, Titel, Nummer, Versuch, Note, CP, Malus, Status, Freigabe,
    Rücktritt, Freiversuch, Vermerk, Vorbehalt, Zusatzmerkmal

Achtung: Ausgabe enthaelt Noten (persoenliche Daten) - nicht committen.
"""

import argparse
import sys

import requests

from explore import (DEFAULT_COLS, export_leistungen, fetch_leistungen, filter_leistungen,
                     login, parse_cols, print_leistungen)
from hisinone_noten import HISinOneClient, HISinOneError


def main() -> int:
    ap = argparse.ArgumentParser(description="HISinOne-Leistungen abrufen und filtern.")
    ap.add_argument("--pl", action="store_true", help="nur PL/PVL (flache Liste)")
    ap.add_argument("--latest", action="store_true", help="fruehere Versuche ausblenden")
    ap.add_argument("--cols", help="Spalten, kommagetrennt (Standard: %(default)s)",
                    default=",".join(DEFAULT_COLS))
    ap.add_argument("-o", "--output", metavar="DATEI", help="nach .json oder .csv exportieren")
    args = ap.parse_args()

    try:
        cols = parse_cols(args.cols)
        if args.output and not args.output.lower().endswith((".json", ".csv")):
            raise ValueError("--output braucht die Endung .json oder .csv")
    except ValueError as e:
        ap.error(str(e))

    try:
        c = HISinOneClient.from_env()
        s, _ = login(c)
        rows, _ = fetch_leistungen(s, c)
    except (HISinOneError, requests.RequestException) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1

    shown = filter_leistungen(rows, exams_only=args.pl, latest_only=args.latest)
    if args.output:
        path = export_leistungen(shown, args.output, cols)
        print(f"{len(shown)} von {len(rows)} Zeilen -> {path}", file=sys.stderr)
    else:
        print_leistungen(shown, cols, tree=not args.pl)
        print(f"\n{len(shown)} von {len(rows)} Zeilen", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
