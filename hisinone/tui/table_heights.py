"""Alle Tabellen auf einen Bildschirm verteilen.

Kleine (<= MIN_ROWS Zeilen) bekommen ihre volle Höhe, größere teilen sich
den Rest, mindestens MIN_ROWS Zeilen + Kopf + ggf. waagrechter Scrollbalken,
mit eigenem Scrollbalken. Die äußere Scrollleiste erscheint nur, wenn das
Terminal dafür zu niedrig ist. (Berechnet statt "1fr" - das löst sich in
einem Scroll-Container nicht zuverlässig auf.)
"""

from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import DataTable

from .table_widgets import MIN_ROWS


def fit_tables(screen: Screen) -> None:
    widgets = list(screen.query(DataTable))
    # abzüglich der Leerzeilen zwischen den Tabellen
    available = screen.query_one(VerticalScroll).scrollable_content_region.height
    available -= len(widgets) - 1
    small = [widget for widget in widgets if not widget.has_class("big")]
    # +1 = Titelleiste
    available -= sum(widget.outer_size.height + 1 for widget in small)
    for widget in small:
        widget.styles.height = "auto"
    big = [widget for widget in widgets if widget.has_class("big")]
    _share_height(big, available)


def _share_height(widgets: list[DataTable], available: int) -> None:
    """Gleichmäßig teilen, aber keine höher als ihr Inhalt (Zeilen + Kopf +
    Scrollbalken); überschüssiger Platz geht an die übrigen."""
    rest = {widget: widget.row_count + 2 for widget in widgets}
    while rest:
        share = available // len(rest) - 1
        fits = {widget: need for widget, need in rest.items() if need <= share}
        if not fits:
            break
        for widget, need in fits.items():
            widget.styles.height = need
            available -= need + 1
            del rest[widget]
    for widget in rest:
        widget.styles.height = max(MIN_ROWS + 2, available // len(rest) - 1)
