"""Hinweis waehrend langer Ladevorgaenge: aktueller Schritt und vergangene Zeit."""

import time

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import LoadingIndicator, Static


class LoadingDialog(ModalScreen):
    """Modal, damit waehrenddessen nichts anderes ausgeloest wird; die App
    schliesst ihn, wenn das Laden fertig (oder fehlgeschlagen) ist."""

    CSS = """
    LoadingDialog { align: center middle; }
    LoadingDialog > Vertical { width: 60; height: auto; border: thick $accent;
                               background: $surface; padding: 1 2; }
    LoadingDialog LoadingIndicator { height: 1; }
    """

    def __init__(self, title: str):
        super().__init__()
        self.title_text = title
        self.step_text = "Starte ..."
        self.started = time.monotonic()

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"[b]{self.title_text}[/b] wird geladen")
            yield Static(id="step")
            yield LoadingIndicator()

    def on_mount(self) -> None:
        self._show()
        self.set_interval(0.5, self._show)

    def step(self, text: str) -> None:
        """Neuer Schritt (aus dem Lade-Thread per call_from_thread)."""
        self.step_text = text
        self._show()

    def _show(self) -> None:
        elapsed = time.monotonic() - self.started
        self.query_one("#step", Static).update(f"{self.step_text} · {elapsed:.0f} s")
