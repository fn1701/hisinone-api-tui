"""Detailansicht einer Seite (z.B. Modulbeschreibung) lesbar als Markdown mit
Inhaltsverzeichnis; Export als .md (e)."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header, MarkdownViewer

from hisinone.explore.detail_view import detail_markdown, detail_tabs, detail_title, parse_detail
from hisinone.explore.storage import prepare_save_dir, safe_file_name, timestamp

from .current_page import CurrentPage
from .dialogs import ExportDialog


class DetailScreen(Screen):
    """Abschnitte der aktiven Registerkarte; Esc zurueck zur Link-Ansicht."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Zurueck"),
        Binding("i", "toggle_toc", "Inhalt"),
        Binding("e", "export", "Export"),
    ]

    def __init__(self, page: CurrentPage):
        super().__init__()
        self.page = page
        sections = parse_detail(page.html)
        self.title_text = detail_title(sections, page.name)
        self.markdown = detail_markdown(self.title_text, detail_tabs(page.html), sections)

    def compose(self) -> ComposeResult:
        yield Header()
        yield MarkdownViewer(self.markdown, show_table_of_contents=False)
        yield Footer()

    def on_mount(self) -> None:
        self.sub_title = f"{self.title_text} · {self.page.title_with_time()}"
        self.query_one(MarkdownViewer).focus()

    def action_toggle_toc(self) -> None:
        viewer = self.query_one(MarkdownViewer)
        viewer.show_table_of_contents = not viewer.show_table_of_contents

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
