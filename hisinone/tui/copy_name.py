"""Erste Zeile jeder Seitenleiste: Name des markierten Eintrags; Klick
oder Taste n kopiert ihn in die Zwischenablage."""

from rich.text import Text
from textual.app import App
from textual.widgets import Static

from hisinone.explore.clipboard import copy_external

COPY_MARK = "⧉ "


def copy_text(app: App, text: str) -> None:
    """Externes Tool (wl-copy/xclip) bevorzugt, sonst OSC 52 über das Terminal."""
    tool = copy_external(text)
    if not tool:
        app.copy_to_clipboard(text)
        tool = "OSC 52"
    app.notify(f"Kopiert ({tool}): {text}")


class CopyName(Static):
    """Name als eigene Zeile; leer = nichts markiert."""

    DEFAULT_CSS = "CopyName { margin-bottom: 1; }"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.entry_name = ""
        self.tooltip = "Klick oder n: Name kopieren"

    def set_name(self, name: str) -> None:
        self.entry_name = name.strip()
        line = Text(COPY_MARK, style="dim") + Text(self.entry_name, style="bold")
        self.update(line if self.entry_name else "")

    def copy(self) -> None:
        if self.entry_name:
            copy_text(self.app, self.entry_name)

    def on_click(self) -> None:
        self.copy()
