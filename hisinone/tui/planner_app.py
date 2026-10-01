"""Studienplaner in der App: Zwischenseite mit Studiengang und Filtern,
laden (mit Fortschritt im Dialog), dann die Tabelle im Vollbild.

Je Studiengang und Filter-Kombination ein eigener Cache-Eintrag; die
Filterwerte selbst stehen im HTML der Seite und werden mit ihr gecacht.
"""

import dataclasses
import functools
import time

import requests
from textual import work

from hisinone.explore.page_tables import load_tables
from hisinone.explore.planner_courses import parse_courses
from hisinone.noten import HISinOneError

from .current_page import CurrentPage, LoadedTables
from .loading_dialog import LoadingDialog
from .planner_choice import PlannerChoice
from .planner_screen import PlannerScreen


class PlannerLoading:
    """Mixin fuer LoadingApp (nutzt session, client, store, _get, show_tree_tables)."""

    planner_choices: dict[str, PlannerChoice]  # stabile URL -> zuletzt gewaehlt

    def show_planner(self, page: CurrentPage, course: str = "") -> None:
        """Zwischenseite; gleich laden, wenn der Studiengang klar ist (nur
        einer, im Baum gewaehlt oder schon einmal gewaehlt)."""
        choice = self.planner_choices.get(page.stable_url, PlannerChoice())
        choice = dataclasses.replace(choice, course=course or choice.course)
        self.planner_screen = PlannerScreen(page, choice)
        self.push_screen(self.planner_screen)
        if choice.course or len(parse_courses(page.html)) == 1:
            self.load_planner(page, choice, False)

    def load_planner(self, page: CurrentPage, choice: PlannerChoice, fresh: bool) -> None:
        self.planner_choices[page.stable_url] = choice
        dialog = LoadingDialog(choice.course or page.name)
        self.push_screen(dialog)
        self._planner_worker(page, choice, dialog, fresh)

    @work(thread=True, exclusive=True)
    def _planner_worker(
        self, page: CurrentPage, choice: PlannerChoice, dialog: LoadingDialog, fresh: bool
    ) -> None:
        key = choice.cache_key(page.stable_url)
        cached = None if fresh else self.store.get_tables(key)
        if cached:
            shown = dataclasses.replace(page, pulled_at=cached[0], from_cache=True)
            self.call_from_thread(self._planner_loaded, dialog, shown, cached[1], None, None)
            return
        started = time.monotonic()
        result = self._load_planner(page, choice, dialog)
        if not result:
            self.call_from_thread(self._planner_loaded, dialog, page, [], None, None)
            return
        shown, tables, html = result
        self.store.put_tables(key, shown, tables, time.monotonic() - started)
        refreshed = self._refresh_planner_page(shown, dialog)
        self.call_from_thread(self._planner_loaded, dialog, shown, tables, html, refreshed)

    def _load_planner(self, page: CurrentPage, choice: PlannerChoice, dialog: LoadingDialog):
        """(Seite, Tabellen, HTML) oder None; eine Seite aus dem Cache hat einen
        alten ViewState, daher vor den Klicks frisch holen."""
        progress = functools.partial(self.call_from_thread, dialog.step)
        try:
            if page.from_cache and not (page := self._fresh_page(page, progress)):
                return None
            course_id = choice.course_id(parse_courses(page.html))
            tables, html = load_tables(self.session, page.server_url, page.html,
                                       self.client.timeout, True, choice.filters, progress,
                                       course_id)  # fmt: skip
        except (HISinOneError, requests.RequestException) as error:
            self.call_from_thread(self.notify, f"Laden fehlgeschlagen: {error}",
                                  severity="error")  # fmt: skip
            return None
        return dataclasses.replace(page, pulled_at=time.time(), from_cache=False), tables, html

    def _fresh_page(self, page: CurrentPage, progress) -> CurrentPage | None:
        progress("Seite neu holen")
        response = self._get(page.stable_url)
        if response is None:
            return None
        return CurrentPage(page.stable_url, page.name, response.url, response.text,
                           pulled_at=time.time())  # fmt: skip

    def _refresh_planner_page(self, page: CurrentPage, dialog: LoadingDialog):
        """Seite nach der Wahl des Studiengangs: erst jetzt stehen alle Filter
        darin (z.B. Studiensemester); fuer die Zwischenseite und den Cache."""
        progress = functools.partial(self.call_from_thread, dialog.step)
        refreshed = self._fresh_page(page, progress)
        if refreshed:
            self.store.put(refreshed, [], float("inf"))
        return refreshed

    def _planner_loaded(self, dialog: LoadingDialog, page: CurrentPage, tables, html,
                        refreshed: CurrentPage | None) -> None:  # fmt: skip
        dialog.dismiss()
        if refreshed:
            self.planner_screen.set_page(refreshed, self.planner_choices[page.stable_url])
        if tables:
            self.show_tree_tables(LoadedTables(page, tables, html, ""))
