"""Kommandozeile: Notenspiegel als JSON."""

import argparse
import json
import sys
from pathlib import Path

from .client import HISinOneClient
from .errors import HISinOneError


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HISinOne Notenspiegel als JSON abrufen.")
    parser.add_argument("-o", "--output", help="JSON in diese Datei schreiben statt stdout")
    parser.add_argument("--compact", action="store_true", help="Kompaktes (einzeiliges) JSON")
    parser.add_argument("--env", help="Pfad zur .env (Standard: Projekt-Hauptordner)")
    parser.add_argument("--attempts", type=int, default=3, help="Abruf-Versuche (Standard 3)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        data = HISinOneClient.from_env(args.env).get_grades(attempts=args.attempts)
    except HISinOneError as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 1
    text = json.dumps(data, ensure_ascii=False, indent=None if args.compact else 2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
        print(f"{len(data['pruefungen'])} Prüfungen -> {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0
