"""Welche Ansicht eine Seite bekommt, erkannt am Seitenaufbau (nicht an der
URL), in dieser Reihenfolge: Studienplaner (erst Studiengang und Filter
wählen), Detailseite (z.B. Modulbeschreibung), Baum-Tabellen; alles andere
als Markdown (PageScreen). Die Startseite bleibt der Link-Baum."""

from hisinone.explore.detail_view import has_detail_view
from hisinone.explore.page_tables import has_tables
from hisinone.explore.planner import is_study_planner

from .current_page import CurrentPage
from .detail_loading import DetailLoading
from .detail_screen import DetailScreen
from .page_screen import PageScreen
from .planner_app import PlannerLoading


class SpecialPages(DetailLoading, PlannerLoading):
    """Mixin für LoadingApp."""

    def show_special(self, page: CurrentPage) -> bool:
        """True = eigene Ansicht gezeigt (dann keine Tabellen laden);
        Seiten mit Baum-Tabellen gehen an die Tabellen-Ansicht weiter."""
        if is_study_planner(page.html):  # Baum erst nach Studiengang/Filtern
            self.show_planner(page)
        elif has_detail_view(page.html):
            self.push_screen(DetailScreen(page))
        elif not has_tables(page.html) and page.stable_url != self.home_url:
            self.push_screen(PageScreen(page))
        else:
            return False
        return True
