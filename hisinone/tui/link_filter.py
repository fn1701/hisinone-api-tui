"""Filterfeld des Link-Baums: Eingabe, Regex-Schalter, Fokuswechsel."""

from textual import on
from textual.widgets import Checkbox, Input


class LinkFilter:
    """Mixin für LinkTreeApp (nutzt page, rebuild, link_tree, settings)."""

    @on(Input.Changed, "#filter")
    def filter_changed(self) -> None:
        if self.page.html:
            self.rebuild()

    @on(Checkbox.Changed, "#regex")
    def regex_changed(self) -> None:
        """Kommt von jedem Bildschirm; die Checkbox der Link-Ansicht (unterster
        Bildschirm) zieht nach, damit alle Seiten denselben Stand zeigen."""
        box = self.screen_stack[0].query_one("#regex", Checkbox)
        if box.value != self.settings.regex:
            with box.prevent(Checkbox.Changed):
                box.value = self.settings.regex
        if self.screen is self.screen_stack[0]:  # Baum nur sichtbar neu aufbauen
            self.filter_changed()

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
