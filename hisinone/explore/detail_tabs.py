"""Registerkarten einer Detailseite: Formular-Knöpfe ohne eigene URL
(myfaces.oam.submitForm). Klicken = das ganze Formular absenden wie der
Browser; die Antwort ist die Seite mit der gewählten Registerkarte."""

import re
from dataclasses import dataclass
from urllib.parse import urljoin

import requests

from .html_text import attribute
from .jsf import find_form, hidden_fields
from .pacer import pacer

FORM_ID = "detailViewData"
TAB = re.compile(r'<button\b[^>]*role="tab"[^>]*>')
TAB_KEY = "#tab:"  # Cache-Schlüssel: stabile URL + TAB_KEY + Knopf-Id


@dataclass
class DetailTab:
    """Registerkarte: Id des Knopfs, Beschriftung, gerade angezeigt?"""

    button_id: str
    name: str
    active: bool


def detail_tabs(html: str) -> list[DetailTab]:
    """Registerkarten in Seitenreihenfolge."""
    return [DetailTab(attribute(tag, "id"), attribute(tag, "value"),
                      "active" in attribute(tag, "class").split())
            for tag in TAB.findall(html)]  # fmt: skip


def tab_key(stable_url: str, tab: DetailTab) -> str:
    return f"{base_url(stable_url)}{TAB_KEY}{tab.button_id}"


def base_url(key: str) -> str:
    """Stabile URL der Seite ohne Registerkarten-Anteil."""
    return key.split(TAB_KEY)[0]


def click_tab(
    session: requests.Session, page_url: str, html: str, tab: DetailTab, timeout: int
) -> requests.Response:
    """Sendet das Formular wie submitForm (Knopf als _idcl und Parameter
    DISABLE_VALIDATION); html muss frisch sein (gültiger ViewState)."""
    action, form_html = find_form(html, FORM_ID)
    data = hidden_fields(form_html) | {
        f"{FORM_ID}:_idcl": tab.button_id,
        tab.button_id: tab.name,
        "DISABLE_VALIDATION": "true",
    }
    pacer.step()
    response = session.post(urljoin(page_url, action), data=data, timeout=timeout,
                            headers={"Referer": page_url})  # fmt: skip
    response.encoding = "utf-8"
    return response
