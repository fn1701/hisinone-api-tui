"""Die gerade angezeigte Seite und ihr Infotext (rechte Spalte)."""

from dataclasses import dataclass
from pathlib import Path

from rich.text import Text

from hisinone.explore.html_text import page_title
from hisinone.explore.page_cache import pulled_text
from hisinone.explore.table_model import TreeTable


@dataclass
class CurrentPage:
    stable_url: str = ""  # ohne fluechtige Parameter, Schluessel in der Config
    name: str = ""
    server_url: str = ""  # wie vom Server geliefert
    html: str = ""
    saved: Path | None = None  # gespeicherte Kopie, falls Speichern an
    pulled_at: float = 0.0  # Abrufzeitpunkt beim Server (time.time())
    from_cache: bool = False

    def title_with_time(self) -> str:
        """Name plus Abrufzeitpunkt fuer Titelzeilen."""
        if not self.pulled_at:
            return self.name
        source = "Cache" if self.from_cache else "Stand"
        return f"{self.name} · {source} {pulled_text(self.pulled_at)}"


@dataclass
class LoadedTables:
    page: CurrentPage  # Seite, zu der die Tabellen gehoeren
    tables: list[TreeTable]
    expanded_html: str | None  # Ajax-Antwort von "Alle aufklappen", sonst None
    open_col: str  # diese Tabelle (Spalte oder Name) gleich im Vollbild


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
    if page.pulled_at:
        info.append("\nAbgerufen: ", style="dim")
        info.append(pulled_text(page.pulled_at))
        info.append(" (aus dem Cache, r = neu laden)" if page.from_cache else "")
    info.append("\nSpeichern: ", style="dim")
    info.append(f"an ({save_dir})" if save_dir else "aus (Taste s)")
    if page.saved:
        info.append("\nGespeichert: ", style="dim")
        info.append(str(page.saved))
