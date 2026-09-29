"""Einstieg des Kommandozeilen-Explorers (python explore.py)."""

import argparse
import sys

import requests

from hisinone.noten import HISinOneClient, HISinOneError

from .browser import PageBrowser
from .repl import ExplorerRepl
from .session import login
from .storage import prepare_save_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HISinOne interaktiv erkunden.")
    parser.add_argument(
        "--sort",
        action="store_true",
        help="Links alphabetisch statt in Seitenreihenfolge (Befehl: a)",
    )
    parser.add_argument(
        "--save",
        nargs="?",
        const="/tmp/hisinone-explore",
        metavar="DIR",
        help="Jede besuchte Seite als HTML speichern (Standard-Ordner: /tmp/hisinone-explore)",
    )
    parser.add_argument(
        "--tree",
        action="store_true",
        help="Links als Baum (Navigation / Vorlesungsverzeichnis) (Befehl: t)",
    )
    return parser.parse_args()  # fmt: skip


def main() -> int:
    args = _parse_args()
    save_dir = prepare_save_dir(args.save) if args.save else None
    try:
        client = HISinOneClient.from_env()
        session, start = login(client)
    except (HISinOneError, requests.RequestException) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    browser = PageBrowser(client, session, start, save_dir)
    return ExplorerRepl(browser, sort=args.sort, tree=args.tree).run()
