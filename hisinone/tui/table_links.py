"""Zeile oeffnen (o): die Detailseite der Zeile (z.B. Modulbeschreibung im
Studienplaner) in der Link-Ansicht laden."""

from textual.widgets import DataTable


class TableLinks:
    """Mixin; erwartet self.shown (sichtbare Zeilen) und app.open_from_table."""

    def action_open_row(self) -> None:
        index = self.query_one(DataTable).cursor_row
        if not 0 <= index < len(self.shown):
            return
        row = self.shown[index].row
        if not row.get("url"):
            self.notify("Diese Zeile hat keinen Link (ggf. mit r neu laden).", severity="warning")
            return
        self.app.open_from_table(row["url"], str(row.get(self.table.title_col, "")))
