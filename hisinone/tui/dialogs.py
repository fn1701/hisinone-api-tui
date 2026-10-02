"""Kleine Dialoge der Tabellen-Ansicht."""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, Input, SelectionList


class ColumnsDialog(ModalScreen[list[str] | None]):
    """Spalten an-/abwählen (Leertaste), Enter = übernehmen, Esc = abbrechen."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "Abbrechen"),
        Binding("enter", "apply", "Übernehmen", priority=True),
    ]
    CSS = "ColumnsDialog { align: center middle; } SelectionList { width: 50; height: 24; }"

    def __init__(self, options: list[tuple]):
        super().__init__()
        self.options = options  # (Anzeige, Schlüssel, an?)

    def compose(self) -> ComposeResult:
        yield SelectionList[str](*self.options)
        yield Footer()

    def action_apply(self) -> None:
        chosen = self.query_one(SelectionList).selected
        # Reihenfolge wie angeboten
        in_order = [key for _, key, _ in self.options if key in chosen]
        self.dismiss(in_order or None)


class ExportDialog(ModalScreen[str | None]):
    """Dateipfad abfragen (.json oder .csv)."""

    BINDINGS = [Binding("escape", "dismiss(None)", "Abbrechen")]
    CSS = "ExportDialog { align: center middle; } Input { width: 80; }"

    def __init__(self, default: str):
        super().__init__()
        self.default = default

    def compose(self) -> ComposeResult:
        yield Input(value=self.default, placeholder="Pfad mit Endung .json oder .csv")
        yield Footer()

    @on(Input.Submitted)
    def submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)
