"""Studienplaner im Link-Baum: beim Auswaehlen die Studiengaenge als Kinder
anzeigen; nur einer -> gleich laden."""

import time

from textual import work
from textual.widgets.tree import TreeNode

from hisinone.explore.html_text import link_name
from hisinone.explore.links import Link, clean_url
from hisinone.explore.planner_courses import parse_courses

from .current_page import CurrentPage
from .planner_choice import PlannerCourse


class PlannerNodes:
    """Mixin fuer LoadingApp (nutzt store, _get, show_planner, link_tree)."""

    def planner_link_selected(self, node: TreeNode, link: Link) -> None:
        """Erst Auswahl: Studiengaenge holen; danach nur auf-/zuklappen."""
        if node.children:
            node.toggle()
            return
        self.link_tree.loading = True
        self._planner_courses(node, link)

    def planner_course_selected(self, item: PlannerCourse) -> None:
        self.show_planner(item.page, item.label)

    @work(thread=True, exclusive=True)
    def _planner_courses(self, node: TreeNode, link: Link) -> None:
        """Planer-Seite wie jede Seite: aus dem Cache oder neu (dann ggf. gecacht)."""
        cached = self.store.get(clean_url(link.url), "tree")
        page = cached[0] if cached else None
        if page is None:
            started = time.monotonic()
            response = self._get(link.url)
            if response is None:
                return
            page = CurrentPage(clean_url(link.url), link_name(link.label) or link.label,
                               response.url, response.text, pulled_at=time.time())  # fmt: skip
            self.store.put(page, [], time.monotonic() - started)
        self.call_from_thread(self._courses_found, node, page)

    def _courses_found(self, node: TreeNode, page: CurrentPage) -> None:
        self.link_tree.loading = False
        courses = parse_courses(page.html)
        if len(courses) <= 1:
            self.show_planner(page)  # einziger Studiengang: direkt laden
            return
        node.allow_expand = True
        for course in courses:
            node.add_leaf(course.label, data=PlannerCourse(page, course.label, page.stable_url))
        node.expand()
