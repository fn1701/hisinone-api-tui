"""Notenspiegel-HTML -> strukturiertes dict."""

import re
import time

from .html_table import norm_label, rows, tables

# Spalten-Codes für "Art" (siehe Legende im Notenspiegel):
#   GE = Modul, PL = Teilmodul, MB/MM = Modul Bachelor-/Masterarbeit,
#   AA = Abschlussarbeit. Nur solche Zeilen sind einzelne Prüfungen.
ART_CODES = {"GE", "PL", "MB", "MM", "AA"}
EXAM_FIELDS = ["pruefungsnummer", "text", "art", "note", "status", "vermerk",
               "credits", "versuch", "semester", "pruefungsdatum", "abgabe"]  # fmt: skip
GRADE = re.compile(r"\d,\d")


def parse_notenspiegel(html: str) -> dict:
    """Zerlegt das Notenspiegel-HTML in ein strukturiertes dict."""
    parser = NotenspiegelParser()
    for table in tables(html):
        parser.add_table(rows(table))
    return parser.result()


class NotenspiegelParser:
    """Sammelt beim Durchlaufen der Tabellen Stammdaten, Legende, Prüfungen
    und Konten; result() baut daraus das Ergebnis."""

    def __init__(self) -> None:
        self.student: dict[str, str] = {}
        self.studiengang = ""
        self.durchschnitt = ""
        self.credits = ""
        self.pruefungen: list[dict] = []
        self.seen_pruefungen: set[tuple] = set()  # exakte Doubletten filtern
        self.konten: list[dict] = []
        self.legende: dict[str, str] = {}

    def add_table(self, table_rows: list[list[str]]) -> None:
        flat = " ".join(cell for row in table_rows for cell in row)
        # Stammdaten-Tabelle: Key/Value, enthält "Matrikelnummer"
        if "Matrikelnummer" in flat and all(len(row) <= 2 for row in table_rows if row):
            self._add_student(table_rows)
        elif "Erl" in flat and "AN - angemeldet" in flat:
            self._add_legend(table_rows)
        elif GRADE.search(flat) or " PL " in f" {flat} ":
            for row in table_rows:
                self._add_grade_row(row)

    def _add_student(self, table_rows: list[list[str]]) -> None:
        for row in table_rows:
            if len(row) == 2:
                self.student[norm_label(row[0])] = row[1]

    def _add_legend(self, table_rows: list[list[str]]) -> None:
        for cell in (cell for row in table_rows for cell in row):
            match = re.match(r"^([A-Z]{2,4}|SoSe|WiSe)\s*-\s*(.+)$", cell)
            if match:
                self.legende[match.group(1)] = match.group(2).strip()

    def _add_grade_row(self, row: list[str]) -> None:
        if len(row) == 1 and "Studiengang:" in row[0]:
            match = re.search(r"Studiengang:\s*(.+)$", row[0])
            self.studiengang = (match.group(1) if match else row[0]).strip()
        if len(row) < 9 or not re.fullmatch(r"\d+", row[0] or ""):
            return  # Kopfzeile, Überschrift o. ae.
        if row[2] in ART_CODES:
            self._add_exam(row)
        else:
            self._add_account(row)

    def _add_exam(self, row: list[str]) -> None:
        padded = row + [""] * (len(EXAM_FIELDS) - len(row))
        exam = dict(zip(EXAM_FIELDS, padded, strict=False))
        # Der Notenspiegel listet PL-Zeilen in zwei Blöcken (Zusammenfassung +
        # Detailplan): exakte Doubletten überspringen, echte Mehrfachversuche
        # behalten.
        signature = tuple(exam.values())
        if signature not in self.seen_pruefungen:
            self.seen_pruefungen.add(signature)
            self.pruefungen.append(exam)

    def _add_account(self, row: list[str]) -> None:
        """Konto-/Summenzeile (z. B. "1. Studienabschnitt"). Feste Spalten:
        [2]=Durchschnitt, [5]=Credits, [6]=Semester."""
        grade = row[2] if GRADE.fullmatch(row[2]) else ""
        konto = {"nummer": row[0], "text": row[1], "durchschnitt": grade,
                 "credits": row[5], "semester": row[6]}  # fmt: skip
        self.konten.append(konto)
        if "studienabschnitt" in row[1].lower() and grade and not self.durchschnitt:
            self.durchschnitt, self.credits = grade, row[5]

    def _summary(self) -> dict[str, str]:
        if not self.durchschnitt:  # Fallback: erstes Konto mit Durchschnitt
            first = next((k for k in self.konten if k["durchschnitt"]), None)
            if first:
                self.durchschnitt, self.credits = first["durchschnitt"], first["credits"]
        return {"durchschnitt": self.durchschnitt, "credits": self.credits}

    def result(self) -> dict:
        keys = ("name", "angestrebter_abschluss", "matrikelnummer")
        return {
            "abgerufen_am": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "student": {key: self.student.get(key, "") for key in keys},
            "studiengang": self.studiengang,
            "zusammenfassung": self._summary(),
            "pruefungen": self.pruefungen,
            "konten": self.konten,
            "legende": self.legende,
        }
