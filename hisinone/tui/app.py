"""Oberste Schicht der App: Tasten, Shortcuts, Befehlspalette, Config."""

from textual.app import SystemCommand
from textual.binding import Binding

from .config import AUTOSAVE_SECONDS
from .navigation_app import NavigationApp
from .settings import ConfigWriter, Settings


class ExploreApp(NavigationApp):
    TITLE = "HISinOne Explorer"
    BINDINGS = [
        Binding("b", "back", "Zurueck"),
        Binding("r", "reload", "Neu laden"),
        Binding("h", "home", "Startseite"),
        Binding("slash", "focus_filter", "Filter", priority=True),
        # show=False: nicht in der Fusszeile, nur Taste + Befehlspalette (Strg+P)
        Binding("t", "toggle_tree", "Baum an/aus", show=False),
        Binding("a", "toggle_sort", "Alphabetisch an/aus", show=False),
        Binding("exclamation_mark", "force_open", "Trotzdem oeffnen", show=False),
        Binding("c", "copy_url", "URL kopieren"),
        Binding("v", "toggle_view", "Tabelle/Links", show=False),
        Binding("o", "browser", "Im Browser oeffnen", show=False),
        Binding("s", "toggle_save", "Speichern an/aus", show=False),
        Binding("escape", "focus_tree", "", show=False),
        Binding("q", "quit", "Beenden", show=False),
        Binding("ctrl+r", "toggle_regex", "Regex an/aus", show=False, priority=True),
    ]

    def __init__(self, settings: Settings, writer: ConfigWriter):
        super().__init__(settings)
        self.writer = writer

    def action_toggle_regex(self) -> None:
        """Wie Klick auf die Checkbox (gilt fuer alle Seiten)."""
        boxes = self.screen.query("#regex")
        if boxes:
            boxes.first().toggle()
        else:
            self.settings.regex = not self.settings.regex

    def check_action(self, action: str, parameters) -> bool | None:
        # Tasten der Link-Ansicht nur dort (Tabellen-Bildschirme haben eigene)
        own_actions = {binding.action for binding in self.BINDINGS} | {"shortcut"}
        if len(self.screen_stack) > 1 and action in own_actions:
            return action == "quit"
        return True

    def get_system_commands(self, screen):
        """Alle Tasten-Befehle auch in der Befehlspalette (Strg+P)."""
        yield from super().get_system_commands(screen)
        for binding in self.BINDINGS:
            if binding.description:
                key = self.get_key_display(binding)
                # Titel werden als Markup gelesen -> keine eckigen Klammern ("[/]")
                yield SystemCommand(f"{binding.description} ({key})", f"Taste {key}",
                                    getattr(self, f"action_{binding.action}"))  # fmt: skip
        for index, shortcut in enumerate(self.settings.shortcuts):
            yield SystemCommand(f"{shortcut.description} ({shortcut.key})",
                                f"Taste {shortcut.key}", ShortcutCall(self, index))  # fmt: skip

    def bind_shortcuts(self) -> None:
        taken = {key.strip() for binding in self.BINDINGS for key in binding.key.split(",")}
        for index, shortcut in enumerate(self.settings.shortcuts):
            if not shortcut.key or not shortcut.path or shortcut.key in taken:
                self.notify(f"Shortcut {shortcut.to_dict()!r} ignoriert "
                            "(Taste fehlt/belegt oder kein path)", severity="warning")  # fmt: skip
                continue
            taken.add(shortcut.key)
            self.bind(shortcut.key, f"shortcut({index})", description=shortcut.description)

    def action_shortcut(self, index: int) -> None:
        shortcut = self.settings.shortcuts[index]
        if self.session:
            url = shortcut.url(self.client.qis_base)
            self.open(url, shortcut.description, open_col=shortcut.open_table_with_column)

    def save_config(self, final: bool = False) -> None:
        try:
            self.writer.save(final)
        except OSError as error:
            self.notify(f"Config nicht speicherbar: {error}", severity="error")

    def on_mount(self) -> None:
        self.bind_shortcuts()
        self.set_interval(AUTOSAVE_SECONDS, self.save_config)
        self.link_tree.auto_expand = False  # Klick oeffnet den Link, klappt nicht nur auf
        self.link_tree.show_root = False
        self.link_tree.loading = True
        self.do_login()

    def on_unmount(self) -> None:
        self.save_config(final=True)


class ShortcutCall:
    """Befehl der Befehlspalette fuer einen Shortcut (statt einer Lambda)."""

    def __init__(self, app: ExploreApp, index: int):
        self.app, self.index = app, index

    def __call__(self) -> None:
        self.app.action_shortcut(self.index)
