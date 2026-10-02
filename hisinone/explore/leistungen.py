"""Leistungen (Mein Studium > Leistungen).

Die Seite ist JSF: die Tabelle ist ein Baum, der nur über Buttons
(jsf.ajax POST) aufklappt. Ablauf = 2 Requests: Seite laden (neuer Flow),
dann einmal "Alle aufklappen" wie im Browser.
"""

import requests

from hisinone.noten import HISinOneClient, HISinOneError

from .exams import earlier_attempts, exam_kind
from .expand import with_table_header
from .jsf import jsf_click
from .session import get_page
from .table_model import Row, TreeTable
from .tree_tables import parse_tree_tables

LEISTUNGEN_PATH = (
    "/pages/sul/examAssessment/personExamsReadonly.xhtml"
    "?_flowId=examsOverviewForPerson-flow"
    "&navigationPosition=hisinoneMeinStudium,examAssessmentForStudent"
)
LEISTUNGEN_FORM = "examsReadonly"
EXPAND_ALL = "examsReadonly:overviewAsTreeReadonly:tree:expandAll2"
LEISTUNGEN_COLS = ["Freigabedatum", "Nummer", "Versuch", "Rücktritt", "Bewertung", "Bonus",
                   "Malus", "Status", "Freiversuch", "Vermerk", "Vorbehalt", "Zusatzmerkmal",
                   "Aktionen"]  # fmt: skip


def parse_leistungen(html: str) -> list[Row]:
    """Zeilen des Leistungs-Baums: {ebene, tiefe (ab 1), typ, titel, art,
    <Spalten>}. Die Tabelle mit Spalte "Versuch" (der Studienverlauf-Baum
    auf derselben Seite wird übergangen)."""
    table = next((t for t in parse_tree_tables(html) if "Versuch" in t.cols), None)
    return _leistungen_rows(table) if table else []


def _leistungen_rows(table: TreeTable) -> list[Row]:
    rows = []
    for source in table.rows:
        row = {"ebene": source.get("Ebene", ""), "tiefe": source["tiefe"] + 1,
               "typ": source["typ"], "titel": source.get("Titel", "")}  # fmt: skip
        row.update({col: source.get(col, "") for col in LEISTUNGEN_COLS})
        row["art"] = exam_kind(row["titel"], row["typ"], row["Bewertung"])
        rows.append(row)
    return rows


def fetch_leistungen(session: requests.Session, client: HISinOneClient) -> tuple[list[Row], str]:
    """Lädt die Leistungen komplett aufgeklappt (2 Requests).
    Liefert (Zeilen, HTML des aufgeklappten Baums)."""
    page = get_page(session, client.qis_base + LEISTUNGEN_PATH, None, client.timeout)
    page.encoding = "utf-8"
    if f'id="{LEISTUNGEN_FORM}"' not in page.text:
        raise HISinOneError("Leistungen-Seite nicht erkannt (abgemeldet?).")
    tree_html = page.text
    if f'id="{EXPAND_ALL}"' in page.text:
        fragment = jsf_click(session, page.url, page.text, LEISTUNGEN_FORM, EXPAND_ALL,
                             client.timeout)  # fmt: skip
        tree_html = with_table_header(fragment, page.text)
    return parse_leistungen(tree_html), tree_html


def filter_leistungen(
    rows: list[Row], exams_only: bool = False, latest_only: bool = False
) -> list[Row]:
    """exams_only: nur PL/PVL. latest_only: frühere Versuche ausblenden
    (Regeln siehe earlier_attempts)."""
    drop: set[int] = set()
    if latest_only:
        drop = earlier_attempts([(r["ebene"], r["art"], r.get("Versuch", "")) for r in rows])
    return [row for index, row in enumerate(rows)
            if index not in drop and (not exams_only or row["art"])]  # fmt: skip
