"""Filterfeld des Link-Baums: Eingabe, Regex-Schalter, Fokuswechsel.

Handler heißen nach Textuals Namensschema (on_input_changed, ...) statt
@on(...): @on wirkt nur in Klassen mit Textuals Metaklasse, in diesem
einfachen Mixin würde es stillschweigend ignoriert."""

from textual.widgets import Checkbox, Input


class LinkFilter:
    """Mixin für LinkTreeApp (nutzt page, rebuild, link_tree, settings)."""

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "filter":
            self.filter_changed()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "filter":
            self.action_focus_tree()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        if event.checkbox.id == "regex":
            self.regex_changed()

    def filter_changed(self) -> None:
        if self.page.html:
            self.rebuild()

    def regex_changed(self) -> None:
        """Kommt von jedem Bildschirm; die Checkbox der Link-Ansicht (unterster
        Bildschirm) zieht nach, damit alle Seiten denselben Stand zeigen."""
        box = self.screen_stack[0].query_one("#regex", Checkbox)
        if box.value != self.settings.regex:
            with box.prevent(Checkbox.Changed):
                box.value = self.settings.regex
        if self.screen is self.screen_stack[0]:  # Baum nur sichtbar neu aufbauen
            self.filter_changed()

    def action_focus_filter(self) -> None:
        field = self.query_one("#filter", Input)
        if self.focused is field:
            field.insert_text_at_cursor("/")  # im Filterfeld ist "/" normaler Text
        else:
            field.focus()

    def action_focus_tree(self) -> None:
        self.link_tree.focus()
