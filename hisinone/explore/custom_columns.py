"""Eigene (berechnete) Spalten, die es auf der Seite nicht gibt. Sie stehen
in TreeTable.custom und werden nur auf Wunsch angezeigt."""

from collections.abc import Callable
from dataclasses import dataclass

from .exams import exam_kind
from .table_model import Row, TreeTable

# Spalten reiner Navigations-Baeume (z.B. Vorlesungsverzeichnis)
NAV_COLS = {"Ebene", "Aktionen", ""}


@dataclass
class CustomColumn:
    name: str
    needs: set[str]  # gilt fuer Tabellen mit diesen Original-Spalten
    value: Callable[[Row], str]


def _kind_icon(row: Row) -> str:
    return row.get("typ", "")


def _exam_kind(row: Row) -> str:
    return exam_kind(row.get("Titel", ""), row.get("typ", ""), row.get("Bewertung", ""))


CUSTOM_COLUMNS = [
    # alle Baum-Tabellen: Typ aus dem Symbol im Titel (Modul, Pruefung, Konto, ...)
    CustomColumn("Typ", set(), _kind_icon),
    # Leistungen: PL/PVL (Regeln siehe exam_kind)
    CustomColumn("Art", {"Titel", "Versuch", "Bewertung", "Freiversuch"}, _exam_kind),
]


def is_data_table(table: TreeTable) -> bool:
    """False fuer reine Navigations-Baeume (nur Ebene, Titel, Aktionen) -
    die bleiben in der Link-Ansicht."""
    return len([col for col in table.cols if col not in NAV_COLS]) > 1


def add_custom_columns(table: TreeTable) -> None:
    """Berechnet die passenden eigenen Spalten in die Zeilen."""
    table.custom = []
    for column in CUSTOM_COLUMNS:
        if not column.needs <= set(table.cols) or column.name in table.cols:
            continue
        values = [column.value(row) for row in table.rows]
        if not any(values):  # nichts zu zeigen -> Spalte gar nicht anbieten
            continue
        for row, value in zip(table.rows, values, strict=True):
            row[column.name] = value
        table.custom.append(column.name)
