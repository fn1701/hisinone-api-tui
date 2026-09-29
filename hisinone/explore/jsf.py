"""JSF-Ajax-Buttons klicken wie jsf.ajax.request im Browser."""

import html as htmlmod
import re
from urllib.parse import urljoin

import requests

from hisinone.noten import HISinOneError

from .html_text import attribute
from .pacer import pacer

AJAX_HEADERS = {"Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest"}


def find_form(html: str, form_id: str) -> tuple[str, str]:
    """(action, inneres HTML) des Formulars mit dieser id."""
    pattern = rf'<form\b[^>]*\bid="{re.escape(form_id)}"[^>]*>(.*?)</form>'
    match = re.search(pattern, html, re.S)
    if not match:
        raise HISinOneError(f"Formular {form_id} nicht gefunden.")
    open_tag = match.group(0)[: match.group(0).find(">") + 1]
    return attribute(open_tag, "action"), match.group(1)


def hidden_fields(form_html: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for tag in re.findall(r'<input\b[^>]*type="hidden"[^>]*>', form_html):
        if name := attribute(tag, "name"):
            fields.setdefault(name, attribute(tag, "value"))
    return fields


def jsf_click(
    session: requests.Session, page_url: str, html: str, form_id: str, button_id: str,
    timeout: int,
) -> str:  # fmt: skip
    """Klickt den Button und liefert das HTML aller aktualisierten Bereiche
    (partial-response)."""
    action, form_html = find_form(html, form_id)
    data = hidden_fields(form_html) | _ajax_fields(form_html, button_id)
    pacer.step()
    response = session.post(urljoin(page_url, action), data=data, timeout=timeout,
                            headers=AJAX_HEADERS | {"Referer": page_url})  # fmt: skip
    response.encoding = "utf-8"
    parts = re.findall(r"<update\b[^>]*><!\[CDATA\[(.*?)\]\]></update>", response.text, re.S)
    if not parts:
        raise HISinOneError(f"Unerwartete Antwort auf {button_id} (HTTP {response.status_code}).")
    return "\n".join(parts)


def _ajax_fields(form_html: str, button_id: str) -> dict[str, str]:
    """Die Felder, die jsf.ajax.request zum Formular hinzufuegt."""
    button = re.search(rf'<button\b[^>]*\bid="{re.escape(button_id)}"[^>]*>', form_html)
    if not button:
        raise HISinOneError(f"Button {button_id} nicht gefunden.")
    # Welche Bereiche neu gerendert werden, steht im onclick des Buttons
    onclick = htmlmod.unescape(attribute(button.group(0), "onclick"))
    render = re.search(r"render:\\?'([^'\\]*)", onclick)
    render_ids = render.group(1) if render else "@form"
    return {
        button_id: attribute(button.group(0), "value"),
        "javax.faces.source": button_id,
        "javax.faces.partial.event": "click",
        "javax.faces.partial.execute": button_id,
        "javax.faces.partial.render": render_ids.replace("@this", button_id).strip(),
        "javax.faces.behavior.event": "action",
        "javax.faces.partial.ajax": "true",
    }
