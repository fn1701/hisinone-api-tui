"""Filterfeld mit Schalter "Regex" (global für alle Seiten, in der Config)."""

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Checkbox, Input

REGEX_HINT = ("Regex (Python, Groß/klein egal), z.B. Bestanden = enthält, "
              "^(?!.*Bestanden) = enthält nicht")  # fmt: skip


class FilterBar(Horizontal):
    """Input mit der gegebenen id plus Checkbox #regex; der Zustand steht in
    app.settings.regex. Bildschirme reagieren auf Checkbox.Changed (#regex)."""

    DEFAULT_CSS = """
    FilterBar { height: auto; }
    FilterBar Input { width: 1fr; }
    FilterBar Checkbox { width: auto; }
    """

    def __init__(self, value: str, input_id: str, hint: str):
        super().__init__()
        self.value, self.input_id, self.hint = value, input_id, hint

    def compose(self) -> ComposeResult:
        regex = self.app.settings.regex
        yield Input(self.value, id=self.input_id, placeholder=self._hint(regex))
        yield Checkbox("Regex", regex, id="regex")

    def _hint(self, regex: bool) -> str:
        return REGEX_HINT if regex else self.hint

    @on(Checkbox.Changed, "#regex")
    def regex_changed(self, event: Checkbox.Changed) -> None:
        self.app.settings.regex = event.value
        self.query_one(Input).placeholder = self._hint(event.value)

    def mark_invalid(self, invalid: bool) -> None:
        """Ungültiger Ausdruck: Feld rot, Ergebnis bleibt das alte."""
        self.query_one(Input).set_class(invalid, "-invalid")
