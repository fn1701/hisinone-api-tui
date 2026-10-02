"""Detailansicht einer Seite (z.B. Modulbeschreibung) lesbar als Markdown mit
Inhaltsverzeichnis; Registerkarten mit 1-9 (gecacht, r = neu laden), Export
als .md (e), im Browser öffnen (o)."""

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import MarkdownViewer, Static

from hisinone.explore.detail_tables import absolute_links
from hisinone.explore.detail_tabs import detail_tabs
from hisinone.explore.detail_view import detail_markdown, detail_title, parse_detail

from .current_page import CurrentPage
from .markdown_screen import MarkdownScreen

TAB_BINDINGS = [Binding(str(number), f"tab({number})", show=False) for number in range(1, 10)]


class DetailScreen(MarkdownScreen):
    """Abschnitte der aktiven Registerkarte; Esc zurück zur Link-Ansicht."""

    BINDINGS = TAB_BINDINGS
    CSS = "#tabs { padding: 0 1; background: $boost; }"

    def _read(self, page: CurrentPage) -> None:
        self.page, self.tabs = page, detail_tabs(page.html)
        sections = parse_detail(page.html)
        self.title_text = detail_title(sections, page.name)
        markdown = detail_markdown(self.title_text, sections)
        self.markdown = absolute_links(markdown, page.server_url)

    def compose_top(self) -> ComposeResult:
        yield Static(id="tabs")

    def _show_header(self) -> None:
        super()._show_header()
        bar = Text()
        for number, tab in enumerate(self.tabs, 1):
            bar.append(f" {number} {tab.name} ", style="reverse bold" if tab.active else "")
        self.query_one("#tabs", Static).update(bar)
        self.query_one("#tabs").display = bool(self.tabs)

    def show_page(self, page: CurrentPage | None) -> None:
        """Geladene Registerkarte anzeigen (None = Fehler, bleibt wie es ist)."""
        self.query_one(MarkdownViewer).loading = False
        if page is None:
            return
        self._read(page)
        self.query_one(MarkdownViewer).document.update(self.markdown)
        self._show_header()

    def action_tab(self, number: int) -> None:
        if number <= len(self.tabs) and not self.tabs[number - 1].active:
            self._load(number - 1, fresh=False)

    def action_reload(self) -> None:
        active = [index for index, tab in enumerate(self.tabs) if tab.active]
        if active:
            self._load(active[0], fresh=True)

    def _load(self, index: int, fresh: bool) -> None:
        self.query_one(MarkdownViewer).loading = True
        self.app.load_detail_tab(self.page, self.tabs[index], fresh)
