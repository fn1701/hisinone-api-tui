"""Einfache .env laden (ohne Zusatzabhängigkeit)."""

import os
from pathlib import Path

# .env liegt im Projekt-Hauptordner (neben hisinone_noten.py)
DEFAULT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


def load_env(path: str | os.PathLike | None = None) -> None:
    """Liest eine einfache ``KEY=VALUE``-.env in ``os.environ`` (setdefault).
    Kommentare (#) und Leerzeilen werden ignoriert, Anführungszeichen
    entfernt. Fehlt die Datei, passiert nichts."""
    env_file = Path(path) if path else DEFAULT_ENV_PATH
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        _apply_line(raw.strip())


def _apply_line(line: str) -> None:
    if not line or line.startswith("#") or "=" not in line:
        return
    key, value = line.split("=", 1)
    key = key.strip()
    if key:
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))
