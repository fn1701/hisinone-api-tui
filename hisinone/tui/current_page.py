"""Die gerade angezeigte Seite und ihr Infotext (rechte Spalte)."""

from dataclasses import dataclass
from pathlib import Path

from rich.text import Text

from hisinone.explore.html_text import page_title


@dataclass
class CurrentPage:
    stable_url: str = ""  # ohne fluechtige Parameter, Schluessel in der Config
    name: str = ""
    server_url: str = ""  # wie vom Server geliefert
    html: str = ""
    saved: Path | None = None  # gespeicherte Kopie, falls Speichern an


@dataclass
class LinkCounts:
    total: int
    shown: int
    filter: str
    mode: str  # z.B. "Baum, A-Z"


def page_info(page: CurrentPage, counts: LinkCounts, save_dir: Path | None) -> Text:
    info = Text()
    info.append(page_title(page.html) + "\n\n", style="bold")
    info.append("Stabil: ", style="green")
    info.append(page.stable_url, style=f"link {page.stable_url}")
    info.append("\n")
    if page.server_url != page.stable_url:
        info.append("Server: ", style="dim")
        info.append(page.server_url, style=f"link {page.server_url}")
        info.append("\n")
    _append_status(info, page, counts, save_dir)
    return info


def _append_status(info: Text, page: CurrentPage, counts: LinkCounts, save_dir: Path | None):
    info.append(f"\n{counts.total} Links ({counts.mode})")
    if counts.filter:
        info.append(f', {counts.shown} passen zu "{counts.filter}"')
    info.append("\nSpeichern: ", style="dim")
    info.append(f"an ({save_dir})" if save_dir else "aus (Taste s)")
    if page.saved:
        info.append("\nGespeichert: ", style="dim")
        info.append(str(page.saved))
