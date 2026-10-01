"""Kommandozeile der TUI: Config lesen, Optionen anwenden, App starten."""

import argparse

from .app import ExploreApp
from .config import CONFIG_PATH, load_config
from .settings import ConfigWriter, Settings


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HISinOne als Terminal-Oberflaeche erkunden.")
    # Optionen ueberschreiben die Config nur, wenn sie angegeben sind (None = nicht angegeben)
    parser.add_argument("--flat", dest="tree", action="store_const", const=False,
                        help="flache Liste statt Baum (Taste t)")  # fmt: skip
    parser.add_argument("--sort", action="store_const", const=True, help="alphabetisch (Taste a)")
    parser.add_argument("--save", nargs="?", const="", metavar="DIR",
                        help="Jede besuchte Seite als HTML speichern (Standard-Ordner: "
                             "aus Config, sonst /tmp/hisinone-explore; Taste s)")  # fmt: skip
    parser.add_argument("--no-cache", action="store_const", const=True,
                        help="Seiten-Cache aus (weder lesen noch schreiben)")  # fmt: skip
    parser.add_argument("--cache-ttl", type=int, metavar="SEKUNDEN",
                        help="Cache-Eintraege nach so vielen Sekunden neu laden "
                             "(0 = unbegrenzt, bis zum Neustart)")  # fmt: skip
    parser.add_argument("--cache-min-load", type=int, metavar="MS",
                        help="nur Seiten cachen, die laenger als MS laden "
                             "(Standard 250)")  # fmt: skip
    parser.add_argument("--no-config", action="store_true",
                        help=f"{CONFIG_PATH} weder lesen noch schreiben")  # fmt: skip
    return parser.parse_args()


def _apply_options(settings: Settings, args: argparse.Namespace) -> None:
    if args.tree is not None:
        settings.tree = args.tree
    if args.sort is not None:
        settings.sort = args.sort
    _apply_cache_options(settings, args)
    if args.save is not None:
        settings.save_on = True
        settings.save_path = args.save or settings.save_path


def _apply_cache_options(settings: Settings, args: argparse.Namespace) -> None:
    if args.no_cache is not None:
        settings.cache.no_cache = args.no_cache
    if args.cache_ttl is not None:
        settings.cache.ttl_seconds = max(0, args.cache_ttl)
    if args.cache_min_load is not None:
        settings.cache.min_load_ms = max(0, args.cache_min_load)


def main() -> int:
    args = _parse_args()
    settings = Settings.from_config({} if args.no_config else load_config())
    _apply_options(settings, args)
    # Writer erst nach den Optionen: sie allein sind keine Aenderung
    writer = ConfigWriter(settings, None if args.no_config else CONFIG_PATH)
    ExploreApp(settings, writer).run()
    return 0
