"""Zugeklappte Abschnitte einer Detailseite (z.B. Parallelgruppen) öffnen.

HISinOne merkt sich je Nutzer, welche Abschnitte zu sind, und liefert deren
Inhalt dann gar nicht mit - erst der Knopf im Titel lädt ihn per Ajax nach.
Öffnen ändert nur diesen gemerkten Anzeige-Zustand.
"""

import re
from urllib.parse import urljoin

import requests

from .jsf import find_form, jsf_updates

COLLAPSED_PANEL = re.compile(
    r'<div\b[^>]*\bid="([^"]*):collapsiblePanel"[^>]*>\s*<input\b[^>]*>\s*'
    r'<div class="collapsedTitle\b'
)
DIV_TAG = re.compile(r"<(/?)div\b", re.I)


def collapsed_panels(html: str) -> list[str]:
    """Ids der zugeklappten Abschnitte (= der Bereiche, die der Knopf neu rendert)."""
    return list(dict.fromkeys(COLLAPSED_PANEL.findall(html)))


def open_panels(session: requests.Session, page_url: str, html: str, timeout: int) -> str:
    """HTML mit allen Abschnitten geöffnet; ein Request je Abschnitt.
    html muss frisch sein (gültiger ViewState)."""
    for panel in collapsed_panels(html):
        html = _open_panel(session, page_url, html, panel, timeout)
    return html


def _open_panel(
    session: requests.Session, page_url: str, html: str, panel: str, timeout: int
) -> str:
    form_id = panel.split(":")[0]  # JSF-ids beginnen mit der Formular-id
    action, form_html = find_form(html, form_id)
    updates = jsf_updates(session, urljoin(page_url, action), page_url, form_html,
                          f"{panel}:minmax", timeout)  # fmt: skip
    fragment = updates.get(panel)
    return replace_div(html, panel, fragment) if fragment else html


def replace_div(html: str, element_id: str, new_html: str) -> str:
    """Ersetzt das <div> mit dieser id samt Inhalt (bis zum passenden </div>)."""
    start = re.search(rf'<div\b[^>]*\bid="{re.escape(element_id)}"', html)
    if not start:
        return html
    depth = 0
    for tag in DIV_TAG.finditer(html, start.start()):
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            end = html.find(">", tag.end()) + 1
            return html[: start.start()] + new_html + html[end:]
    return html
