"""Bedienleiste des Studienplaners: Studiengang, Filter der Seitenleiste
(live aus der Seite) und der Button zum Übernehmen."""

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Label, Select

from hisinone.explore.planner_courses import parse_courses
from hisinone.explore.planner_filter import FilterField, parse_filters

from .planner_choice import PlannerChoice

APPLY_LABEL = "Übernehmen (l)"


class PlannerControls(Vertical):
    """Zeile 1: Studiengang + Button, Zeile 2: alle Filter nebeneinander."""

    DEFAULT_CSS = """
    PlannerControls { height: auto; padding: 0 1; }
    PlannerControls Horizontal { height: auto; }
    PlannerControls .field { width: 1fr; height: auto; }
    PlannerControls Button { margin: 1 0 0 1; }
    """

    def __init__(self, page, choice: PlannerChoice):
        super().__init__()
        self.page, self.choice = page, choice
        self.filters: list[FilterField] = parse_filters(page.html)

    def set_page(self, page, choice: PlannerChoice) -> None:
        """Nach dem Laden: Seite mit allen Filtern (manche gibt es erst,
        wenn ein Studiengang gewählt ist)."""
        self.page, self.choice, self.filters = page, choice, parse_filters(page.html)
        self.refresh(recompose=True)

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(classes="field"):
                yield Label("Studiengang")
                yield self._course_select()
            yield Button(APPLY_LABEL, id="load", variant="primary")
        with Horizontal():
            for index, filter_field in enumerate(self.filters):
                with Vertical(classes="field"):
                    yield Label(filter_field.label or filter_field.name)
                    yield self._filter_select(index, filter_field)

    def _course_select(self) -> Select:
        courses = parse_courses(self.page.html)
        labels = [course.label for course in courses]
        value = self.choice.course if self.choice.course in labels else labels[0]
        options = [(course.name, course.label) for course in courses]
        return Select(options, value=value, allow_blank=False, id="course")

    def _filter_select(self, index: int, filter_field: FilterField) -> Select:
        options = [(label, value) for value, label in filter_field.options]
        values = [value for value, _ in filter_field.options]
        value = self.choice.filters.get(filter_field.name, filter_field.current)
        value = value if value in values else values[0]
        return Select(options, value=value, allow_blank=False, id=f"filter-{index}")

    def chosen(self) -> PlannerChoice:
        """Aktuelle Auswahl aller Listen."""
        filters: dict[str, str] = {}
        for index, filter_field in enumerate(self.filters):
            filters[filter_field.name] = str(self.query_one(f"#filter-{index}", Select).value)
        return PlannerChoice(str(self.query_one("#course", Select).value), filters)
