"""Studiengänge im Studienplaner: je einer ein Link "doChangeDepp", dessen
Text aus Name und Zusatzzeilen (z.B. Abschluss, PO) besteht."""

import html as htmlmod
import re
from dataclasses import dataclass

CONTENT = "studyPlanner:container:content-container"
COURSE_LINK = re.compile(rf'<a\b[^>]*\bid="({CONTENT}:studentCourseOfStudySelection:[^"]*'
                         r':doChangeDepp)"[^>]*>(.*?)</a>', re.S)  # fmt: skip


@dataclass
class Course:
    """Ein wählbarer Studiengang: Link-id in der Seite und lesbarer Name."""

    link_id: str
    label: str

    @property
    def name(self) -> str:
        """Nur der Name (erster Textteil, ohne Zusatzzeilen) für Auswahllisten."""
        return self.label.split(" · ")[0]


def parse_courses(html: str) -> list[Course]:
    """Alle Studiengänge der Seite in Seitenreihenfolge."""
    return [Course(match.group(1), _text(match.group(2))) for match in COURSE_LINK.finditer(html)]


def _text(inner_html: str) -> str:
    """Textteile des Links, getrennt mit " · " (statt <br>/<small>)."""
    parts = [htmlmod.unescape(part).strip() for part in re.split(r"<[^>]*>", inner_html)]
    return " · ".join(part for part in parts if part)
