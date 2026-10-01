"""Seiten mit eigener Ansicht statt Tabellen: Studienplaner (erst Studiengang
und Filter waehlen) und Detailseiten (z.B. Modulbeschreibung)."""

from hisinone.explore.detail_view import has_detail_view
from hisinone.explore.planner import is_study_planner

from .current_page import CurrentPage
from .detail_loading import DetailLoading
from .detail_screen import DetailScreen
from .planner_app import PlannerLoading


class SpecialPages(DetailLoading, PlannerLoading):
    """Mixin fuer LoadingApp."""

    def show_special(self, page: CurrentPage) -> bool:
        """True = eigene Ansicht gezeigt (dann keine Tabellen laden)."""
        if is_study_planner(page.html):  # Baum erst nach Studiengang/Filtern
            self.show_planner(page)
        elif has_detail_view(page.html):
            self.push_screen(DetailScreen(page))
        else:
            return False
        return True
