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
    updates = jsf_updates(session, urljoin(page_url, action), page_url, form_html, button_id,
                          timeout)  # fmt: skip
    return "\n".join(updates.values())


def jsf_updates(
    session: requests.Session, post_url: str, page_url: str, form_html: str, source_id: str,
    timeout: int, values: dict[str, str] | None = None,
) -> dict[str, str]:  # fmt: skip
    """Klickt Button oder Link im Formular; {id des Bereichs: neues HTML}.
    values: Eingaben im Formular (z.B. gewaehlte Filter)."""
    fields = _ajax_fields(form_html, source_id) | (values or {})
    return jsf_partial(session, post_url, page_url, form_html, fields, timeout)


def jsf_partial(
    session: requests.Session, post_url: str, page_url: str, form_html: str,
    fields: dict[str, str], timeout: int,
) -> dict[str, str]:  # fmt: skip
    """Ajax-Request mit den Formularfeldern plus `fields` (z.B. Blaettern
    in einer PrimeFaces-Tabelle); {id des Bereichs: neues HTML}."""
    data = hidden_fields(form_html) | fields
    pacer.step()
    response = session.post(post_url, data=data, timeout=timeout,
                            headers=AJAX_HEADERS | {"Referer": page_url})  # fmt: skip
    response.encoding = "utf-8"
    parts = re.findall(r'<update\b[^>]*\bid="([^"]*)"[^>]*><!\[CDATA\[(.*?)\]\]></update>',
                       response.text, re.S)  # fmt: skip
    if not parts:
        source = fields.get("javax.faces.source", "")
        raise HISinOneError(f"Unerwartete Antwort auf {source} (HTTP {response.status_code}).")
    return dict(parts)


def _ajax_fields(form_html: str, source_id: str) -> dict[str, str]:
    """Die Felder, die jsf.ajax.request zum Formular hinzufuegt."""
    pattern = rf'<(button|a)\b[^>]*\bid="{re.escape(source_id)}"[^>]*>'
    source = re.search(pattern, form_html)
    if not source:
        raise HISinOneError(f"Button/Link {source_id} nicht gefunden.")
    execute_ids, render_ids = _partial_ids(attribute(source.group(0), "onclick"), source_id)
    # Nur ein Button schickt seinen Wert mit, ein Link nicht
    own_value = (
        {source_id: attribute(source.group(0), "value")} if source.group(1) == "button" else {}
    )
    return own_value | {
        "javax.faces.source": source_id,
        "javax.faces.partial.event": "click",
        "javax.faces.partial.execute": execute_ids,
        "javax.faces.partial.render": render_ids,
        "javax.faces.behavior.event": "action",
        "javax.faces.partial.ajax": "true",
    }


def _partial_ids(onclick: str, source_id: str) -> tuple[str, str]:
    """(execute, render) aus dem onclick von jsf.ajax.request."""
    # Welche Bereiche neu gerendert werden, steht im onclick
    onclick = htmlmod.unescape(onclick)
    render = re.search(r"render:\\?'([^'\\]*)", onclick)
    render_ids = render.group(1) if render else "@form"
    execute = re.search(r"execute:\\?'([^'\\]*)", onclick)
    # Nur feste ids uebernehmen (z.B. ein anderes Formular); @this/@form wie bisher
    explicit = execute and "@" not in execute.group(1)
    execute_ids = execute.group(1).strip() if explicit else source_id
    return execute_ids, render_ids.replace("@this", source_id).strip()
