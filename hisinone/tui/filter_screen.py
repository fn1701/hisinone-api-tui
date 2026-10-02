"""Basisklasse: Bildschirm mit Zeilenfilter und Vorschlagsliste darunter;
mit Regex stehen dort Beispiel-Ausdrücke statt "Spalte=Wert"."""

from textual import on
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import DataTable, Input, OptionList
from textual.widgets.option_list import Option

SUGGEST_CSS = """
#suggest { display: none; overlay: screen; max-height: 12; width: 60;
           border: tall $accent; background: $panel; }
#suggest.shown { display: block; }
"""

# (Beschreibung, Ausdruck); Zeile = "Spalte=Wert | ..." samt Eltern davor
REGEX_EXAMPLES = [
    ("enthält Bestanden", "Bestanden"),
    ("enthält nicht Bestanden", "^(?!.*Bestanden)"),
    ("PL, aber nicht Bestanden", r"^(?=.*\bPL\b)(?!.*Bestanden)"),
    ("Spalte A = Bestanden", r"\bA=Bestanden"),
    ("PV im Titel, A nicht Bestanden", r"Titel=[^|]*PV(?!.*\bA=Bestanden)"),
    ("eins von beiden", "Mathe|Programm"),
]


class FilterScreen(Screen):
    """Erwartet Widgets #rowfilter (Input), #suggest (OptionList) und eine
    DataTable. Unterklassen liefern die Vorschläge und Spaltennamen."""

    BINDINGS = [Binding("down", "open_suggest", "", show=False)]

    def suggestions(self) -> list[str]:
        raise NotImplementedError

    def column_name(self, index: int) -> str:
        raise NotImplementedError

    @property
    def filter_input(self) -> Input:
        return self.query_one("#rowfilter", Input)

    @property
    def suggest_list(self) -> OptionList:
        return self.query_one("#suggest", OptionList)

    def last_term(self) -> str:
        """Der Begriff, der gerade getippt wird (nach dem letzten Leerzeichen)."""
        value = self.filter_input.value
        return "" if value.endswith(" ") else value.rsplit(" ", 1)[-1]

    def replace_last_term(self, text: str) -> None:
        field = self.filter_input
        field.value = field.value[: len(field.value) - len(self.last_term())] + text
        field.cursor_position = len(field.value)
        field.focus()

    def update_suggest(self) -> None:
        if not self.suggest_list.has_class("shown"):
            return
        if self.app.settings.regex:
            self._show_examples()
            return
        typed = self.last_term().lower()
        options = [text for text in self.suggestions() if typed in text.lower()][:100]
        self.suggest_list.clear_options()
        self.suggest_list.add_options(options or [Option("(keine Vorschläge)", disabled=True)])

    def _show_examples(self) -> None:
        """Ausdruck als id: Auswahl ersetzt das Feld (keine Begriffe)."""
        self.suggest_list.clear_options()
        for label, pattern in REGEX_EXAMPLES:
            self.suggest_list.add_option(Option(f"{pattern}   ({label})", id=pattern))

    def show_suggest(self) -> None:
        self.suggest_list.add_class("shown")
        self.update_suggest()

    def hide_suggest(self) -> None:
        self.suggest_list.remove_class("shown")

    def on_descendant_focus(self, event) -> None:
        if event.widget.id == "rowfilter":
            self.show_suggest()
        elif event.widget.id != "suggest":
            self.hide_suggest()

    def on_click(self, event) -> None:
        # Klick ins schon fokussierte Filterfeld öffnet die Liste ebenfalls
        if getattr(event.widget, "id", None) == "rowfilter":
            self.show_suggest()

    @on(OptionList.OptionSelected, "#suggest")
    def suggestion_picked(self, event: OptionList.OptionSelected) -> None:
        if event.option.id:  # Regex-Beispiel: ersetzt das ganze Feld
            pattern = event.option.id
            self.filter_input.value = pattern
            self.filter_input.cursor_position = len(pattern)
            self.filter_input.focus()
            return
        self.replace_last_term(str(event.option.prompt) + " ")

    @on(DataTable.HeaderSelected)
    def header_clicked(self, event: DataTable.HeaderSelected) -> None:
        """Klick auf Spaltenkopf: 'Spalte=' als letzten Filterbegriff setzen,
        Vorschläge für diese Spalte zeigen."""
        col = self.column_name(event.column_index)
        self.replace_last_term((f'"{col}"' if " " in col else col) + "=")
        self.show_suggest()

    def action_open_suggest(self) -> None:
        if self.focused and self.focused.id == "rowfilter":
            self.show_suggest()
            if self.suggest_list.highlighted is None and self.suggest_list.option_count:
                self.suggest_list.highlighted = 0
            self.suggest_list.focus()

    def focus_rows(self) -> None:
        """Zeilen-Widget fokussieren (Unterklassen mit mehreren Ansichten)."""
        self.query_one(DataTable).focus()

    def close_filter(self) -> bool:
        """Esc: erst Vorschlagsliste, dann Filterfeld verlassen.
        False = nichts zu schließen (Bildschirm verlassen)."""
        if self.suggest_list.has_class("shown"):
            self.hide_suggest()
            if self.focused is self.suggest_list:
                self.filter_input.focus()
            return True
        if self.focused is self.filter_input:
            self.focus_rows()
            return True
        return False
