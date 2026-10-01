"""Unterste Schicht der App: Link-Baum, Filterfeld und Infospalte."""

from pathlib import Path

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Input, Static, Tree

from hisinone.explore.link_tree import flat_entries, tree_order
from hisinone.explore.links import Link, extract_links
from hisinone.explore.storage import prepare_save_dir, save_html

from .current_page import CurrentPage, LinkCounts, page_info
from .link_view import LinkTreeFiller, link_details
from .settings import Settings


class LinkTreeApp(App):
    CSS = """
    #filter { dock: top; }
    #links { width: 2fr; }
    #details { width: 1fr; border-left: solid $primary; padding: 0 1; }
    """

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.page = CurrentPage()
        self.host = ""
        self.node_paths: dict = {}  # Knoten-ID -> Pfad fuer "collapsed"
        # Ordner wird erst beim ersten Einschalten angelegt
        self.save_dir: Path | None = None
        if settings.save_on:
            self.save_dir = prepare_save_dir(settings.save_path)

    @property
    def save_path(self) -> str:
        return self.settings.save_path

    def open(self, url: str, name: str, push: bool = True, open_col: str = "") -> None:
        raise NotImplementedError  # in der abgeleiteten Klasse (laedt die Seite)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Filter (Name oder URL) ...", id="filter")
        with Horizontal():
            yield Tree("Anmelden ...", id="links")
            with VerticalScroll(id="details"):
                yield Static(id="page")
                yield Static(id="link")
        yield Footer()

    @property
    def link_tree(self) -> Tree:
        return self.query_one("#links", Tree)

    def show_page(self, page: CurrentPage) -> None:
        if self.save_dir:
            page.saved = save_html(self.save_dir, page.server_url, page.html, page.name)
        self.page = page
        # Neue Seite -> Filter zuruecksetzen (sonst sieht man ggf. nichts)
        with self.prevent(Input.Changed):
            self.query_one("#filter", Input).value = ""
        self.rebuild()
        self.link_tree.loading = False
        # Waehrend des Ladens ist der Baum gesperrt und der Fokus wandert ins
        # Filterfeld - danach zurueck in den Baum, damit Tasten Befehle sind.
        self.link_tree.focus()

    def fetch_failed(self, message: str) -> None:
        self.link_tree.loading = False
        self.notify(message, severity="error")

    def rebuild(self) -> None:
        """Baut Baum/Liste aus der aktuellen Seite neu auf (auch nach Filter/Toggle)."""
        tree_mode, sort = self.settings.tree, self.settings.sort
        text = self.query_one("#filter", Input).value.strip().casefold()
        links = extract_links(self.page.html, self.page.server_url, sort=sort and not tree_mode)
        total = len(links)
        if text:
            links = [link for link in links
                     if text in link.label.casefold() or text in link.url.casefold()]  # fmt: skip
        entries = tree_order(links, sort=sort) if tree_mode else flat_entries(links)
        collapsed = self.settings.collapsed.for_page(self.page.stable_url)
        self.node_paths = LinkTreeFiller(self.link_tree, self.host, collapsed).fill(entries)
        self.sub_title = self.page.title_with_time()
        mode = ("Baum" if tree_mode else "Liste") + (", A-Z" if sort else "")
        counts = LinkCounts(total, len(links), text, mode)
        self.query_one("#page", Static).update(page_info(self.page, counts, self.save_dir))
        self.query_one("#link", Static).update("")

    @on(Tree.NodeCollapsed, "#links")
    @on(Tree.NodeExpanded, "#links")
    def node_toggled(self, event: Tree.NodeCollapsed | Tree.NodeExpanded) -> None:
        """Auf-/Zuklappen fuer alle Seiten merken (nur Zugeklapptes wird gespeichert)."""
        path = self.node_paths.get(event.node.id)
        if not path or not self.settings.tree:
            return
        paths = set(self.settings.collapsed.paths)
        if isinstance(event, Tree.NodeCollapsed):
            paths.add(path)
        else:
            paths.discard(path)
        self.settings.collapsed.set_global(paths)

    @on(Tree.NodeSelected, "#links")
    def node_selected(self, event: Tree.NodeSelected) -> None:
        link: Link | None = event.node.data
        if link is None:
            event.node.toggle()  # Gruppen-Ueberschrift
        elif link.needs_confirm:
            self.notify("Keine stabile URL bzw. Abmelden - mit ! trotzdem oeffnen.",
                        severity="warning")  # fmt: skip
        else:
            self.open(link.url, link.label)

    @on(Tree.NodeHighlighted, "#links")
    def node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self.query_one("#link", Static).update(link_details(event.node.data, self.host))

    @on(Input.Changed, "#filter")
    def filter_changed(self) -> None:
        if self.page.html:
            self.rebuild()

    @on(Input.Submitted, "#filter")
    def filter_submitted(self) -> None:
        self.action_focus_tree()

    def action_focus_filter(self) -> None:
        field = self.query_one("#filter", Input)
        if self.focused is field:
            field.insert_text_at_cursor("/")  # im Filterfeld ist "/" normaler Text
        else:
            field.focus()

    def action_focus_tree(self) -> None:
        self.link_tree.focus()
