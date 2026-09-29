"""Baum-Tabellen einer Seite per "Alle aufklappen" komplett laden.

Geklickt wird nur, wenn es genau einen globalen Button gibt (nicht die vielen
pro Knoten im Vorlesungsverzeichnis).
"""

import re

import requests

from .jsf import jsf_click
from .table_model import TreeTable
from .tree_tables import TREE_TABLE, parse_tree_tables

EXPAND_ALL_BTN = re.compile(r'<button\b[^>]*\bid="([^"]*:expandAll\d*)"')


def can_expand_all(html: str) -> bool:
    return len(set(EXPAND_ALL_BTN.findall(html))) == 1


def expand_tree_tables(
    session: requests.Session, page_url: str, html: str, timeout: int, expand: bool = True
) -> tuple[list[TreeTable], str]:
    """Liefert (Tabellen, HTML das sie enthaelt - Seite oder Ajax-Fragment).
    Mit expand und genau einem Button: 1 Request."""
    tables = parse_tree_tables(html)
    buttons = set(EXPAND_ALL_BTN.findall(html))
    form = _form_of(html, next(iter(buttons))) if len(buttons) == 1 else None
    if not tables or not expand or not form:
        return tables, html
    fragment = jsf_click(session, page_url, html, form, next(iter(buttons)), timeout)
    fragment = with_table_header(fragment, html)
    expanded = parse_tree_tables(fragment)
    _copy_names(expanded, tables)
    # Nicht aufgeklappte weitere Baeume der Seite behalten
    rest = [t for t in tables if all(t.cols != e.cols for e in expanded)]
    return expanded + rest, fragment


def _form_of(html: str, button_id: str) -> str | None:
    """Formular, zu dem der Button gehoert (JSF-ids: "<form>:...")."""
    form_ids = re.findall(r'<form\b[^>]*\bid="([^"]*)"', html)
    return next((form for form in form_ids if button_id.startswith(form + ":")), None)


def with_table_header(fragment: str, page_html: str) -> str:
    """Das Fragment enthaelt ggf. nur Zeilen; Tabellenkopf aus der Seite davor."""
    if TREE_TABLE.search(fragment):
        return fragment
    header = re.search(TREE_TABLE.pattern + r".*?</tr>", page_html, re.S)
    return (header.group(0) if header else "") + fragment


def _copy_names(expanded: list[TreeTable], originals: list[TreeTable]) -> None:
    # Fragment hat keine Ueberschriften -> Namen von der passenden Seiten-Tabelle
    for table in expanded:
        if not table.name:
            same = (t.name for t in originals if t.cols == table.cols)
            table.name = next(same, "")
