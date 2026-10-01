"""Studienplaner laden: wie im Browser erst den Studiengang waehlen (Link
"doChangeDepp"), dann alle obersten Knoten auf eine Seite holen (der Baum
blaettert sonst zu je 10), dann "Alle aufklappen" - zusammen 2-3 Requests.

Der Baum steht nicht in der Seite, sondern kommt erst per Ajax nach dem Klick
auf den Studiengang.
"""

import html as htmlmod
import re
from urllib.parse import urljoin

import requests

from hisinone.noten import HISinOneError

from .jsf import find_form, jsf_partial, jsf_updates
from .planner_tree import parse_planner_tree
from .table_model import TreeTable

FORM_ID = "studyPlanner"
CONTENT = "studyPlanner:container:content-container"
COURSE_LINK = re.compile(rf'<a\b[^>]*\bid="({CONTENT}:studentCourseOfStudySelection:[^"]*'
                         r':doChangeDepp)"')  # fmt: skip
EXPAND_BTN = f"{CONTENT}:expandAllBtn"
TREE_ID = f"{CONTENT}:studyPlannerTree"
# Blaettern im Baum: PrimeFaces.cw("TreeTable", ..., paginator:{..., rows:10, rowCount:24
PAGINATOR = re.compile(r"paginator:\{[^}]*?\brows:(\d+),rowCount:(\d+)")


def is_study_planner(html: str) -> bool:
    return f'id="{FORM_ID}"' in html and bool(COURSE_LINK.search(html))


class PlannerLoader:
    """Klickt sich durch den Studienplaner; merkt sich Formular und ViewState
    zwischen den Klicks (der Server erwartet jeweils den neuesten)."""

    def __init__(self, session: requests.Session, page_url: str, html: str, timeout: int):
        self.session = session
        self.page_url = page_url
        self.timeout = timeout
        action, self.form_html = find_form(html, FORM_ID)
        self.post_url = urljoin(page_url, action)
        self.course_link = COURSE_LINK.search(html).group(1)

    def load(self, expand: bool = True) -> tuple[list[TreeTable], str]:
        """(Tabellen, HTML des Baums); expand=False: nur der Studiengang."""
        tree_html = self._click(self.course_link).get("contentFrame", "")
        self.form_html += tree_html
        tree_html = self._all_top_nodes(tree_html)
        if expand:
            tree_html = self._click(EXPAND_BTN).get(TREE_ID, tree_html)
        tables = parse_planner_tree(tree_html)
        if not tables:
            raise HISinOneError("Studienplaner: kein Baum in der Antwort.")
        return tables, tree_html

    def _all_top_nodes(self, tree_html: str) -> str:
        """Alle obersten Knoten auf eine Seite (1 Request, nur wenn geblaettert
        wird); der Server merkt sich die Seitengroesse fuer "Alle aufklappen"."""
        paging = PAGINATOR.search(tree_html)
        if not paging or int(paging.group(2)) <= int(paging.group(1)):
            return tree_html
        fields = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": TREE_ID,
            "javax.faces.partial.execute": TREE_ID,
            "javax.faces.partial.render": TREE_ID,
            f"{TREE_ID}_pagination": "true",
            f"{TREE_ID}_first": "0",
            f"{TREE_ID}_rows": paging.group(2),
        }
        return self._remember_view_state(self._post(fields)).get(TREE_ID, tree_html)

    def _post(self, fields: dict[str, str]) -> dict[str, str]:
        return jsf_partial(self.session, self.post_url, self.page_url, self.form_html, fields,
                           self.timeout)  # fmt: skip

    def _click(self, source_id: str) -> dict[str, str]:
        updates = jsf_updates(self.session, self.post_url, self.page_url, self.form_html,
                              source_id, self.timeout)  # fmt: skip
        return self._remember_view_state(updates)

    def _remember_view_state(self, updates: dict[str, str]) -> dict[str, str]:
        view_state = next((html for key, html in updates.items() if "ViewState" in key), None)
        if view_state:  # neues Feld vorn: hidden_fields nimmt das erste
            value = htmlmod.escape(view_state, quote=True)
            field = f'<input type="hidden" name="javax.faces.ViewState" value="{value}">'
            self.form_html = field + self.form_html
        return updates
