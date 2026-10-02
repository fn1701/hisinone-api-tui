"""Allgemeine Seitenansicht: jede Seite ohne eigene Ansicht als Markdown
(Inhaltsbereich ohne Navigation). Esc zeigt den Link-Baum derselben Seite."""

from hisinone.explore.page_markdown import page_markdown

from .current_page import CurrentPage
from .markdown_screen import MarkdownScreen


class PageScreen(MarkdownScreen):
    """Inhalt der Seite als Markdown; r lädt die Seite neu vom Server."""

    def _read(self, page: CurrentPage) -> None:
        self.markdown = page_markdown(page.html, page.name, page.server_url)

    def action_reload(self) -> None:
        # Neu laden zeigt die Seite wieder in dieser Ansicht, daher erst schließen
        self.app.pop_screen()
        self.app.open(self.page.stable_url, self.page.name, push=False, fresh=True)
