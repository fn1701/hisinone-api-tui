"""Export der angezeigten Zeilen einer Tabelle als CSV (Taste e)."""

import re
from pathlib import Path

from hisinone.explore.export import export_rows
from hisinone.explore.storage import prepare_save_dir, timestamp

from .dialogs import ExportDialog


class TableExport:
    """Mixin für SingleTableScreen: braucht self.table, self.shown_rows,
    self.state und self.app."""

    def action_export(self) -> None:
        name = re.sub(r"[^\w.-]+", "_", self.table.display_name)
        default = prepare_save_dir(self.app.save_path) / f"{name}_{timestamp()}.csv"
        rows, cols = self.shown_rows, self.state.active_cols()

        def done(path: str | None) -> None:  # Zeilen/Spalten wie beim Öffnen des Dialogs
            if path:
                self._export(rows, cols, path)

        self.app.push_screen(ExportDialog(str(default)), done)

    def _export(self, rows: list, cols: list[str], path: str) -> None:
        try:
            out = export_rows(rows, Path(path).expanduser(), cols)
        except (ValueError, OSError) as error:
            self.notify(f"Export fehlgeschlagen: {error}", severity="error")
        else:
            self.notify(f"{len(rows)} Zeilen -> {out}")
