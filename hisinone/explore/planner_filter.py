"""Filter des Studienplaners (Seitenleiste): live aus der Seite gelesen, weil
Felder und Werte je HISinOne-System und Semester verschieden sind.

Erkannt wird generisch jedes <select> und jede Radio-Gruppe im Formular der
Seitenleiste; die Beschriftung ist das letzte Label davor.
"""

import html as htmlmod
import re
from dataclasses import dataclass, field

from .html_text import attribute
from .jsf import find_form

SIDEBAR_ID = "studyPlannerSidebar"
SELECT = re.compile(r"<select\b[^>]*>.*?</select>", re.S)
OPTION = re.compile(r"<option\b([^>]*)>([^<]*)", re.S)
RADIO = re.compile(r'<input\b[^>]*type="radio"[^>]*>')
LABEL = re.compile(r'label_top_position_marked[^>]*>\s*([^<]+)')
# Uebernehmen-Button der Seitenleiste (oben und unten gleich)
APPLY = re.compile(r'<button\b[^>]*\bid="([^"]*hideSidebar)"')


@dataclass
class FilterField:
    """Ein Filter: Formularfeld, Beschriftung, (Wert, Text)-Paare, gewaehlter Wert."""

    name: str
    label: str
    options: list[tuple[str, str]] = field(default_factory=list)
    selected: str = ""


def sidebar_form(html: str) -> tuple[str, str] | None:
    """(action, inneres HTML) der Seitenleiste; None, wenn es keine gibt."""
    if f'id="{SIDEBAR_ID}"' not in html:
        return None
    return find_form(html, SIDEBAR_ID)


def apply_button(form_html: str) -> str | None:
    match = APPLY.search(form_html)
    return match.group(1) if match else None


def parse_filters(html: str) -> list[FilterField]:
    """Alle Auswahl-Filter der Seitenleiste in Seitenreihenfolge."""
    form = sidebar_form(html)
    if not form:
        return []
    form_html = form[1]
    found = [(match.start(), _select_field(form_html, match)) for match in SELECT.finditer(form_html)]
    found += _radio_fields(form_html)
    return [filter_field for _, filter_field in sorted(found, key=_position) if filter_field.options]


def _position(item: tuple[int, FilterField]) -> int:
    return item[0]


def _select_field(form_html: str, match: re.Match) -> FilterField:
    tag = match.group(0)
    result = FilterField(attribute(tag, "name"), _label_before(form_html, match.start()))
    for attrs, text in OPTION.findall(tag):
        value = attribute(f"<option {attrs}>", "value")
        result.options.append((value, htmlmod.unescape(text).strip()))
        if "selected" in attrs:
            result.selected = value
    return result


def _radio_fields(form_html: str) -> list[tuple[int, FilterField]]:
    groups: dict[str, tuple[int, FilterField]] = {}
    for match in RADIO.finditer(form_html):
        tag = match.group(0)
        name = attribute(tag, "name")
        if name not in groups:
            groups[name] = (match.start(), FilterField(name, _label_before(form_html, match.start())))
        group = groups[name][1]
        value = attribute(tag, "value")
        group.options.append((value, _radio_text(form_html, attribute(tag, "id")) or value))
        if "checked" in tag:
            group.selected = value
    return list(groups.values())


def _radio_text(form_html: str, input_id: str) -> str:
    match = re.search(rf'<label\b[^>]*for="{re.escape(input_id)}"[^>]*>([^<]*)', form_html)
    return htmlmod.unescape(match.group(1)).strip() if match else ""


def _label_before(form_html: str, position: int) -> str:
    labels = LABEL.findall(form_html, 0, position)
    return htmlmod.unescape(labels[-1]).strip() if labels else ""


def filter_key(values: dict[str, str]) -> str:
    """Teil des Cache-Schluessels: gleiche Filter = gleiche Tabelle."""
    return "&".join(f"{name}={value}" for name, value in sorted(values.items()))
