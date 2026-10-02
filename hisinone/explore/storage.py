"""Besuchte Seiten als HTML speichern (enthalten persönliche Daten!)."""

import re
import time
from pathlib import Path

from .html_text import link_name, page_title


def timestamp() -> str:
    return time.strftime("%Y-%m-%d_%H-%M-%S")


def prepare_save_dir(path: str) -> Path:
    """Legt den Speicherordner an. Seiten enthalten persönliche Daten ->
    Ordner nur für den eigenen User lesbar."""
    directory = Path(path)
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory.chmod(0o700)
    return directory


def safe_file_name(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name).strip("_")


def save_html(save_dir: Path, url: str, html: str, name: str) -> Path:
    """Speichert als <angeklickter Linkname>_<Datum>.html und liefert den Pfad."""
    base = f"{safe_file_name(link_name(name) or page_title(html) or 'seite')[:80]}_{timestamp()}"
    path = save_dir / f"{base}.html"
    number = 2
    while path.exists():  # mehrere Seiten in derselben Sekunde
        path = save_dir / f"{base}_{number}.html"
        number += 1
    path.write_text(f"<!-- {url} -->\n{html}", encoding="utf-8")
    return path
