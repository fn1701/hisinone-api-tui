"""Seite des Studienplaners: oben Studiengang und Filter, darunter die
geladene Tabelle mit allem, was die Vollbild-Tabelle kann (Zeilenfilter,
Regex, Auf-/Zuklappen, Spalten, Export)."""

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Button

from hisinone.explore.table_model import TreeTable

from .page_config import TablePrefs
from .planner_choice import PlannerChoice
from .planner_controls import PlannerControls
from .single_table_screen import SingleTableScreen
from .table_state import TableViewState


class PlannerScreen(SingleTableScreen):
    """Tabelle anfangs leer; "Uebernehmen" ruft app.load_planner(Seite,
    Auswahl, frisch), das Ergebnis kommt ueber show_table."""

    BINDINGS = [
        Binding("l", "load(False)", "Übernehmen"),
        Binding("r", "load(True)", "Neu laden"),
        Binding("f", "fullscreen", "Vollbild"),
    ]

    BAR_CLICKABLE = True

    def __init__(self, page, choice: PlannerChoice):
        super().__init__(page.name, TreeTable("Studienplaner", ["Titel"], []), {})
        self.page, self.choice = page, choice

    def compose_top(self) -> ComposeResult:
        yield PlannerControls(self.page, self.choice)

    def show_table(self, page, table: TreeTable, prefs: dict[str, TablePrefs]) -> None:
        """Geladene Tabelle einsetzen; Zeilenfilter usw. aus den Einstellungen."""
        self.table = table  # self.page bleibt die aktuellere Seite aus set_page
        self.state = TableViewState(table, prefs)
        self.filter_input.value = self.state.filter
        self.page_name = page.title_with_time()
        self.refresh_table()
        self.focus_rows()  # Tasten (g, o, t, ...) gleich fuer die Tabelle

    def set_page(self, page, choice: PlannerChoice) -> None:
        """Seite nach dem Laden (mit allen Filtern): fuer die Listen und fuer
        das naechste Laden, das deren Seitenleiste abschickt."""
        self.page = page
        self.query_one(PlannerControls).set_page(page, choice)

    def action_fullscreen(self) -> None:
        """Dieselbe Tabelle ohne Studiengang/Filter; Einstellungen gemeinsam."""
        self.app.push_screen(SingleTableScreen(self.page_name, self.table, self.state.page_prefs))

    def open_single(self, index: int) -> None:
        """Klick auf die Titelleiste wie Taste f."""
        self.action_fullscreen()

    def on_screen_resume(self) -> None:
        """Zurueck aus dem Vollbild: dort geaenderte Filter/Spalten uebernehmen."""
        if self.table.rows:
            self.show_table(self.page, self.table, self.state.page_prefs)

    @on(Button.Pressed, "#load")
    def load_pressed(self) -> None:
        self.action_load(False)

    def action_load(self, fresh: bool) -> None:
        self.app.load_planner(self.page, self.query_one(PlannerControls).chosen(), fresh)
