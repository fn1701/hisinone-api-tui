"""Detailansicht einer Seite (z.B. Modulbeschreibung) lesbar als Markdown mit
Inhaltsverzeichnis; Registerkarten mit 1-9 (gecacht, r = neu laden), Export
als .md (e), im Browser oeffnen (o)."""

from pathlib import Path

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, MarkdownViewer, Static

from hisinone.explore.detail_tabs import base_url, detail_tabs
from hisinone.explore.detail_view import detail_markdown, detail_title, parse_detail
from hisinone.explore.storage import prepare_save_dir, safe_file_name, timestamp

from .current_page import CurrentPage
from .dialogs import ExportDialog


class DetailViewer(MarkdownViewer):
    """Links (◆ in Tabellen) oeffnen die Seite in der App statt als Datei."""

    async def _on_markdown_link_clicked(self, message: Markdown.LinkClicked) -> None:
        message.stop()
        message.prevent_default()  # sonst laedt MarkdownViewer den Link als Datei
        self.app.open_from_table(message.href, "")


TAB_BINDINGS = [Binding(str(number), f"tab({number})", show=False) for number in range(1, 10)]


class DetailScreen(Screen):
    """Abschnitte der aktiven Registerkarte; Esc zurueck zur Link-Ansicht."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Zurueck"),
        Binding("i", "toggle_toc", "Inhalt"),
        Binding("r", "reload", "Neu laden"),
        Binding("e", "export", "Export"),
        Binding("o", "browser", "Browser"),
        *TAB_BINDINGS,
    ]
    CSS = "#tabs { padding: 0 1; background: $boost; }"

    def __init__(self, page: CurrentPage):
        super().__init__()
        self._read(page)

    def _read(self, page: CurrentPage) -> None:
        self.page, self.tabs = page, detail_tabs(page.html)
        sections = parse_detail(page.html)
        self.title_text = detail_title(sections, page.name)
        self.markdown = detail_markdown(self.title_text, sections)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(id="tabs")
        yield DetailViewer(self.markdown, show_table_of_contents=False)
        yield Footer()

    def on_mount(self) -> None:
        self._show_header()
        self.query_one(MarkdownViewer).focus()

    def _show_header(self) -> None:
        self.sub_title = f"{self.title_text} · {self.page.title_with_time()}"
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

    def action_toggle_toc(self) -> None:
        viewer = self.query_one(MarkdownViewer)
        viewer.show_table_of_contents = not viewer.show_table_of_contents

    def action_browser(self) -> None:
        self.app.open_url(base_url(self.page.stable_url) or self.page.server_url)

    def action_export(self) -> None:
        name = safe_file_name(self.title_text)[:80] or "detail"
        default = prepare_save_dir(self.app.save_path) / f"{name}_{timestamp()}.md"
        self.app.push_screen(ExportDialog(str(default)), self._export)

    def _export(self, path: str | None) -> None:
        if not path:
            return
        try:
            Path(path).expanduser().write_text(self.markdown, encoding="utf-8")
        except OSError as error:
            self.notify(f"Export fehlgeschlagen: {error}", severity="error")
        else:
            self.notify(f"Gespeichert: {path}")
