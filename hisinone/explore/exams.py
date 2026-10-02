"""Prüfungsart (PL/PVL) und Versuche erkennen."""

import re

from .table_model import Row

GRADE_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def exam_kind(title: str, kind_icon: str, grade: str) -> str:
    """ "PL"/"PVL" laut Titel-Endung; sonst "PL", wenn eine Note (Zahl) drin
    steht - außer bei Modul/Konto (die tragen nur zusammengefasste Noten)."""
    match = re.search(r"\((PVL|PL)\)\s*$", title)
    if match:
        return match.group(1)
    if GRADE_NUMBER.fullmatch(grade) and kind_icon not in ("Modul", "Konto"):
        return "PL"
    return ""


def earlier_attempts(items: list[tuple[str, str, str]]) -> set[int]:
    """Indizes früherer Versuche; items = [(Ebene, Art, Versuch)] je Zeile.
    Versuche sind Geschwister im Baum (gleicher Elternknoten, gleiche Art);
    je Gruppe bleibt der höchste. Kommt eine Versuchsnummer doppelt vor,
    sind es verschiedene Prüfungen -> Gruppe bleibt komplett. Nur Zeilen
    mit Art zählen."""
    groups: dict[tuple[str, str], list[int]] = {}
    for index, (level, kind, _) in enumerate(items):
        if kind:
            groups.setdefault((level.rsplit(".", 1)[0], kind), []).append(index)
    drop: set[int] = set()
    for indices in groups.values():
        attempts = [_attempt_number(items[i][2]) for i in indices]
        if len(indices) > 1 and len(set(attempts)) == len(attempts):
            best = indices[attempts.index(max(attempts))]
            drop.update(i for i in indices if i != best)
    return drop


def _attempt_number(text: str) -> int:
    return int(text) if text.isdigit() else 0


def latest_attempts_tree(rows: list[Row]) -> list[Row]:
    """Frühere Versuche ausblenden, für Zeilen aus parse_tree_tables
    (Spalten Ebene/Art/Versuch)."""
    items = [(row.get("Ebene", ""), row.get("Art", ""), row.get("Versuch", "")) for row in rows]
    drop = earlier_attempts(items)
    return [row for index, row in enumerate(rows) if index not in drop]
