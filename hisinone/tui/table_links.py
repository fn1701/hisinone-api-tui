"""Zeile öffnen: g lädt die Seite der Zeile (z.B. Modulbeschreibung im
Studienplaner) in der App, o öffnet sie im Browser (wie im Link-Baum),
p lädt die Seiten aller sichtbaren Zeilen in den Cache (TablePrefetch)."""

from .table_prefetch import TablePrefetch


class TableLinks(TablePrefetch):
    """Mixin; erwartet current_row/row_url (TableViews) und app.open_from_table."""

    def action_open_row(self) -> None:
        row = self._linked_row()
        if row is not None:
            self.app.open_from_table(row["url"], str(row.get(self.table.title_col, "")))

    def action_browse_row(self) -> None:
        row = self._linked_row()
        if row is not None:
            self.app.open_url(self.row_url(row))

    def _linked_row(self) -> dict | None:
        row = self.current_row()
        if row is None or not row.get("url"):
            self.notify("Diese Zeile hat keinen Link (ggf. mit r neu laden).", severity="warning")
            return None
        return row
