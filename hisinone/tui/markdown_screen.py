"""Gemeinsame Grundlage der Markdown-Ansichten (Detailseite, allgemeine
Seite): Inhaltsverzeichnis (i), Export als .md (e), im Browser öffnen (o),
Links öffnen in der App."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown, MarkdownViewer

from hisinone.explore.detail_tabs import base_url
from hisinone.explore.storage import prepare_save_dir, safe_file_name, timestamp

from .current_page import CurrentPage
from .dialogs import ExportDialog


class LinkViewer(MarkdownViewer):
    """Links öffnen die Seite in der App statt als Datei."""

    async def _on_markdown_link_clicked(self, message: Markdown.LinkClicked) -> None:
        message.stop()
        message.prevent_default()  # sonst lädt MarkdownViewer den Link als Datei
        self.app.open_from_table(message.href, "")


class MarkdownScreen(Screen):
    """Unterklassen setzen in _read page, title_text und markdown und
    implementieren action_reload."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Zurück"),
        Binding("i", "toggle_toc", "Inhalt"),
        Binding("r", "reload", "Neu laden"),
        Binding("e", "export", "Export"),
        Binding("o", "browser", "Browser"),
    ]

    def __init__(self, page: CurrentPage):
        super().__init__()
        self.page, self.title_text, self.markdown = page, page.name, ""
        self._read(page)

    def _read(self, page: CurrentPage) -> None:
        raise NotImplementedError

    def compose(self) -> ComposeResult:
        yield Header()
        yield from self.compose_top()
        yield LinkViewer(self.markdown, show_table_of_contents=False)
        yield Footer()

    def compose_top(self) -> ComposeResult:
        """Platz über dem Text (z.B. Registerkarten)."""
        yield from ()

    def on_mount(self) -> None:
        self._show_header()
        self.query_one(MarkdownViewer).focus()

    def _show_header(self) -> None:
        self.sub_title = f"{self.title_text} · {self.page.title_with_time()}"

    def action_toggle_toc(self) -> None:
        viewer = self.query_one(MarkdownViewer)
        viewer.show_table_of_contents = not viewer.show_table_of_contents

    def action_browser(self) -> None:
        self.app.open_url(base_url(self.page.stable_url) or self.page.server_url)

    def action_export(self) -> None:
        name = safe_file_name(self.title_text)[:80] or "seite"
        default = prepare_save_dir(self.app.save_path) / f"{name}_{timestamp()}.md"
        self.app.push_screen(ExportDialog(str(default)), self._export)

    def _export(self, path: str | None) -> None:
        if not path:
            return
        try:
            Path(path).expanduser().write_text(self.markdown, encoding="utf-8")
        except OSError as error:
            self.notify(f"Export fehlgeschlagen: {error}", severity="error")
