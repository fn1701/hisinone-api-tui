"""Zeilen als .json oder .csv exportieren (enthaelt ggf. Noten!)."""

import csv
import json
from pathlib import Path

from .columns import column_label
from .table_model import Row


def export_rows(rows: list[Row], path: str | Path, cols: list[str]) -> Path:
    """Die Endung entscheidet das Format; Spaltennamen wie angezeigt."""
    path = Path(path)
    labels = [column_label(col) for col in cols]
    data = [{label: str(row.get(col, "")) for col, label in zip(cols, labels, strict=True)}
            for row in rows]  # fmt: skip
    suffix = path.suffix.lower()
    if suffix == ".json":
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif suffix == ".csv":
        _write_csv(path, labels, data)
    else:
        raise ValueError("Dateiendung .json oder .csv verwenden.")
    return path


def _write_csv(path: Path, labels: list[str], data: list[dict[str, str]]) -> None:
    # ";" + BOM: oeffnet in deutschem Excel/LibreOffice direkt richtig
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=labels, delimiter=";")
        writer.writeheader()
        writer.writerows(data)
