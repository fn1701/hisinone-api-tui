#!/usr/bin/env python3
"""
Leistungen (Mein Studium > Leistungen) komplett aufgeklappt abrufen, filtern
und als Tabelle, JSON oder CSV ausgeben. 4 Requests: Login (2), Seite,
"Alle aufklappen" - mit Zufallspausen dazwischen (hisinone/explore/pacer.py).

Benutzung (aus dem Projekt-Hauptordner, .env wie bei login_test.py):
    .venv/bin/python leistungen.py                      # Baum als Tabelle
    .venv/bin/python leistungen.py --pl                 # nur PL/PVL, flach
    .venv/bin/python leistungen.py --pl --latest        # ... nur letzter Versuch
    .venv/bin/python leistungen.py --cols titel,Note,CP,Status
    .venv/bin/python leistungen.py --pl -o leistungen.csv   # oder .json

Filter:
    --pl      nur Prüfungen: Titel endet auf (PL)/(PVL), oder es steht eine
              Note (Zahl) drin und der Typ ist nicht Modul/Konto (-> PL)
    --latest  frühere Versuche ausblenden: Versuche sind Geschwister im Baum
              (gleicher Elternknoten + gleiche Art); es bleibt der höchste

Spalten (--cols, Schlüssel oder Anzeigename, kommagetrennt):
    Ebene, Typ, Art, Titel, Nummer, Versuch, Note, CP, Malus, Status, Freigabe,
    Rücktritt, Freiversuch, Vermerk, Vorbehalt, Zusatzmerkmal

Achtung: Ausgabe enthält Noten (persönliche Daten) - nicht committen.
"""

import argparse
import sys

import requests

from hisinone.explore.columns import DEFAULT_COLS, parse_cols
from hisinone.explore.console import print_leistungen
from hisinone.explore.export import export_rows
from hisinone.explore.leistungen import fetch_leistungen, filter_leistungen
from hisinone.explore.session import login
from hisinone.explore.table_model import Row
from hisinone.noten import HISinOneClient, HISinOneError


def _parse_args() -> tuple[argparse.Namespace, list[str]]:
    """(Argumente, Spalten-Schlüssel); ungültige Angaben beenden das Programm."""
    parser = argparse.ArgumentParser(description="HISinOne-Leistungen abrufen und filtern.")
    parser.add_argument("--pl", action="store_true", help="nur PL/PVL (flache Liste)")
    parser.add_argument("--latest", action="store_true", help="frühere Versuche ausblenden")
    parser.add_argument("--cols", help="Spalten, kommagetrennt (Standard: %(default)s)",
                        default=",".join(DEFAULT_COLS))  # fmt: skip
    parser.add_argument("-o", "--output", metavar="DATEI", help="nach .json oder .csv exportieren")
    args = parser.parse_args()
    try:
        cols = parse_cols(args.cols)
    except ValueError as error:
        parser.error(str(error))
    if args.output and not args.output.lower().endswith((".json", ".csv")):
        parser.error("--output braucht die Endung .json oder .csv")
    return args, cols


def _fetch() -> list[Row] | None:
    try:
        client = HISinOneClient.from_env()
        session, _ = login(client)
        rows, _ = fetch_leistungen(session, client)
    except (HISinOneError, requests.RequestException) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return None
    return rows


def main() -> int:
    args, cols = _parse_args()
    rows = _fetch()
    if rows is None:
        return 1
    shown = filter_leistungen(rows, exams_only=args.pl, latest_only=args.latest)
    if args.output:
        path = export_rows(shown, args.output, cols)
        print(f"{len(shown)} von {len(rows)} Zeilen -> {path}", file=sys.stderr)
    else:
        print_leistungen(shown, cols, tree=not args.pl)
        print(f"\n{len(shown)} von {len(rows)} Zeilen", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
