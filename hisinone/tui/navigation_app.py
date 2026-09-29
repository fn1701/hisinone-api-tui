"""Aktionen der Link-Ansicht: Verlauf, Ansicht umschalten, URL, Speichern."""

from hisinone.explore.clipboard import copy_external
from hisinone.explore.storage import prepare_save_dir, save_html

from .loading_app import LoadingApp


class NavigationApp(LoadingApp):
    def action_back(self) -> None:
        if self.history:
            url, name = self.history.pop()
            self.open(url, name, push=False)
        else:
            self.notify("Kein Verlauf.")

    def action_reload(self) -> None:
        if self.page.stable_url:
            self.open(self.page.stable_url, self.page.name, push=False)

    def action_home(self) -> None:
        if self.home_url:
            self.open(self.home_url, "Startseite")

    def action_force_open(self) -> None:
        node = self.link_tree.cursor_node
        if node and node.data:
            self.open(node.data.url, node.data.label)

    def action_toggle_view(self) -> None:
        """Aktuelle Seite zwischen Tabellen-Ansicht und nur Links umschalten
        (wird in der Config gemerkt) und neu laden."""
        config = self.settings.pages.get(self.page.stable_url)
        if not config:
            self.notify("Keine Baum-Tabelle auf dieser Seite.", severity="warning")
            return
        config.toggle_view()
        self.notify(f"Ansicht: {'Tabelle' if config.view == 'table' else 'nur Links'}")
        self.action_reload()

    def current_url(self) -> str:
        """URL des markierten Links, sonst die stabile URL der Seite."""
        node = self.link_tree.cursor_node
        return node.data.url if node and node.data else self.page.stable_url

    def action_copy_url(self) -> None:
        url = self.current_url()
        if not url:
            return
        # Externes Tool (wl-copy/xclip) bevorzugt, sonst OSC 52 ueber das Terminal
        tool = copy_external(url)
        if not tool:
            self.copy_to_clipboard(url)
            tool = "OSC 52"
        self.notify(f"Kopiert ({tool}): {url}")

    def action_browser(self) -> None:
        if url := self.current_url():
            self.open_url(url)

    def action_toggle_save(self) -> None:
        if self.save_dir:
            self.save_dir, self.page.saved = None, None
            self.notify("Speichern aus")
        elif not self._start_saving():
            return
        self.settings.save_on = bool(self.save_dir)
        self.rebuild()

    def _start_saving(self) -> bool:
        try:
            self.save_dir = prepare_save_dir(self.settings.save_path)
        except OSError as error:
            self.notify(f"Ordner nicht anlegbar: {error}", severity="error")
            return False
        if self.page.html:  # aktuelle Seite gleich mitspeichern
            page = self.page
            page.saved = save_html(self.save_dir, page.server_url, page.html, page.name)
        self.notify(f"Speichern an: {self.save_dir}")
        return True

    def action_toggle_tree(self) -> None:
        self.settings.tree = not self.settings.tree
        self.rebuild()

    def action_toggle_sort(self) -> None:
        self.settings.sort = not self.settings.sort
        self.rebuild()
