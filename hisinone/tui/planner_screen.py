"""Zwischenseite des Studienplaners: Studiengang und Filter als Auswahllisten,
dann die Tabelle laden (im Vollbild; Esc fuehrt hierher zurueck)."""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Select, Static

from hisinone.explore.planner_courses import parse_courses
from hisinone.explore.planner_filter import FilterField, parse_filters

from .planner_choice import PlannerChoice

HINT = "Filter wie in der Seitenleiste im Browser; die Werte kommen live von der Seite."


class PlannerScreen(Screen):
    """Zeigt die Auswahl; "Laden" ruft app.load_planner(Seite, Auswahl, frisch)."""

    BINDINGS = [
        Binding("escape", "back", "Zurueck"),
        Binding("l", "load(False)", "Laden"),
        Binding("r", "load(True)", "Neu laden"),
    ]
    CSS = """
    PlannerScreen VerticalScroll { padding: 1 2; }
    PlannerScreen Select { width: 90; margin-bottom: 1; }
    """

    def __init__(self, page, choice: PlannerChoice):
        super().__init__()
        self.page, self.choice = page, choice
        self.filters: list[FilterField] = parse_filters(page.html)

    def set_page(self, page, choice: PlannerChoice) -> None:
        """Nach dem Laden: Seite mit allen Filtern (manche gibt es erst,
        wenn ein Studiengang gewaehlt ist)."""
        self.page, self.choice, self.filters = page, choice, parse_filters(page.html)
        self.refresh(recompose=True)

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Static(HINT if self.filters else "Keine Filter auf der Seite gefunden.")
            yield Label("Studiengang")
            yield self._course_select()
            for index, filter_field in enumerate(self.filters):
                yield Label(filter_field.label or filter_field.name)
                yield self._filter_select(index, filter_field)
            yield Button("Tabelle laden (l)", id="load", variant="primary")
        yield Footer()

    def _course_select(self) -> Select:
        labels = [course.label for course in parse_courses(self.page.html)]
        value = self.choice.course if self.choice.course in labels else labels[0]
        options = [(label, label) for label in labels]
        return Select(options, value=value, allow_blank=False, id="course")

    def _filter_select(self, index: int, filter_field: FilterField) -> Select:
        options = [(label, value) for value, label in filter_field.options]
        values = [value for value, _ in filter_field.options]
        value = self.choice.filters.get(filter_field.name, filter_field.selected)
        value = value if value in values else values[0]
        return Select(options, value=value, allow_blank=False, id=f"filter-{index}")

    def on_mount(self) -> None:
        self.sub_title = self.page.title_with_time()

    def chosen(self) -> PlannerChoice:
        """Aktuelle Auswahl aller Listen."""
        filters: dict[str, str] = {}
        for index, filter_field in enumerate(self.filters):
            filters[filter_field.name] = str(self.query_one(f"#filter-{index}", Select).value)
        return PlannerChoice(str(self.query_one("#course", Select).value), filters)

    @on(Button.Pressed, "#load")
    def load_pressed(self) -> None:
        self.action_load(False)

    def action_load(self, fresh: bool) -> None:
        self.app.load_planner(self.page, self.chosen(), fresh)

    def action_back(self) -> None:
        self.app.pop_screen()
