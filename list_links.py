#!/usr/bin/env python3
"""
Loggt sich ins HISinOne ein und listet alle Links der Startseite (Menue,
Kacheln, ...) auf - um herauszufinden, welche Bereiche es gibt.

Benutzung (aus dem Projekt-Hauptordner, .env wie bei login_test.py):
    python list_links.py                 # Links nach stdout
    python list_links.py -o start.html   # zusaetzlich rohes HTML speichern

Achtung: start.html enthaelt persoenliche Daten - nicht committen.
"""

import argparse
import sys
from pathlib import Path

import requests

from hisinone.explore.links import extract_links
from hisinone.explore.session import login
from hisinone.noten import HISinOneClient, HISinOneError


def main() -> int:
    parser = argparse.ArgumentParser(description="Links der HISinOne-Startseite auflisten.")
    parser.add_argument("-o", "--output", help="Rohes HTML der Startseite in diese Datei")
    args = parser.parse_args()
    try:
        _, start = login(HISinOneClient.from_env())
    except (HISinOneError, requests.RequestException) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    if args.output:
        Path(args.output).write_text(start.text, encoding="utf-8")
        print(f"HTML -> {args.output}", file=sys.stderr)
    for link in extract_links(start.text, start.url):
        print(f"{link.label[:50]:50}  {link.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
