"""Alle Zeilen mit eigener Seite (◆) der sichtbaren Tabelle bzw. des Baums
auf einmal laden und cachen (p), z.B. alle Modulbeschreibungen im
Studienplaner; danach öffnen sie ohne Wartezeit."""

from urllib.parse import urljoin

from textual import work

from hisinone.explore.links import clean_url

PROGRESS_EVERY = 10  # Zwischenstand alle n Seiten melden


class TablePrefetch:
    """Mixin; erwartet shown_rows und table (Tabellen-Screen) sowie app mit
    page, store und _fetch_linked (DetailLoading)."""

    def action_prefetch_rows(self) -> None:
        links = self._row_links()
        if not links:
            self.notify("Keine sichtbaren Zeilen mit eigener Seite (◆).", severity="warning")
            return
        self.notify(f"Lade {len(links)} Seiten in den Cache ...")
        self._prefetch(links)

    def _row_links(self) -> list[tuple[str, str]]:
        """(absolute URL, Name) je sichtbarer Zeile mit Link, ohne Doppelte."""
        links: dict[str, str] = {}
        for row in self.shown_rows:
            if row.get("url"):
                url = urljoin(self.app.page.server_url, row["url"])
                links.setdefault(url, str(row.get(self.table.title_col, "")))
        return list(links.items())

    @work(thread=True, exclusive=True, group="prefetch")
    def _prefetch(self, links: list[tuple[str, str]]) -> None:
        """Nacheinander laden (Pausen macht der Pacer); Gecachtes überspringen."""
        counts = {"geladen": 0, "schon im Cache": 0, "fehlgeschlagen": 0}
        for number, (url, name) in enumerate(links, start=1):
            counts[self._prefetch_one(url, name)] += 1
            if number % PROGRESS_EVERY == 0:
                self.app.call_from_thread(self.notify, f"{number} von {len(links)} Seiten ...")
        summary = ", ".join(f"{count} {label}" for label, count in counts.items() if count)
        self.app.call_from_thread(self.notify, f"Fertig: {summary}")

    def _prefetch_one(self, url: str, name: str) -> str:
        if self.app.store.get(clean_url(url), ""):
            return "schon im Cache"
        return "fehlgeschlagen" if self.app._fetch_linked(url, name) is None else "geladen"
