"""Detailansicht (Formular ``detailViewData``, z.B. Modulbeschreibung aus dem
Studienplaner) als Abschnitte lesen: Ueberschrift (``<legend>``, Ebene nach
Verschachtelung der Fieldsets), Felder "Bezeichnung: Wert" und Freitext.

Nur die gerade aktive Registerkarte steht in der Seite; die anderen sind
Formular-Knoepfe ohne eigene URL und werden daher nicht gezeigt.
"""

import html as htmlmod
import re
from dataclasses import dataclass, field

from .html_text import text_of

FORM_START = re.compile(r'<form\b[^>]*\bid="detailViewData"')
LEGEND = re.compile(r"<legend\b[^>]*>(.*?)</legend>", re.S)
FIELDSET = re.compile(r"<(/?)fieldset\b")
FIELD = re.compile(r'<label\b[^>]*class="labelWithBG[^"]*"[^>]*>(.*?)</label>\s*'
                   r'<div\b[^>]*class="answer[^"]*"[^>]*>(.*?)</div>', re.S)  # fmt: skip
# Kein Inhalt: Ueberschriften (doppelt zur legend), Knoepfe, Skripte
NOISE = re.compile(r"<(h\d|button|script|legend)\b.*?</\1>", re.S)
LINE_END = re.compile(r"<br\b[^>]*>|</(p|li|div|tr)>", re.I)


@dataclass
class DetailSection:
    """Ein Abschnitt: Ueberschrift, Ebene (1 = oberste), Felder, Freitext."""

    title: str
    level: int
    fields: list[tuple[str, str]] = field(default_factory=list)
    text: str = ""


def has_detail_view(html: str) -> bool:
    return bool(FORM_START.search(html))


def parse_detail(html: str) -> list[DetailSection]:
    """Abschnitte der aktiven Registerkarte; leere Rahmen-Abschnitte bleiben
    als Ueberschrift fuer ihre Unterabschnitte."""
    start = FORM_START.search(html)
    if not start:
        return []
    form = html[start.start() : html.find("</form>", start.start())]
    legends = list(LEGEND.finditer(form))
    sections = []
    for index, legend in enumerate(legends):
        end = legends[index + 1].start() if index + 1 < len(legends) else len(form)
        level = _depth(form[: legend.start()])
        sections.append(_section(text_of(legend.group(1)), level, form[legend.end() : end]))
    return sections


def _depth(before: str) -> int:
    """Wie viele Fieldsets an dieser Stelle offen sind."""
    depth = 0
    for match in FIELDSET.finditer(before):
        depth += -1 if match.group(1) else 1
    return max(depth, 1)


def _section(title: str, level: int, fragment: str) -> DetailSection:
    fields = [(text_of(label), text_of(value)) for label, value in FIELD.findall(fragment)]
    rest = FIELD.sub("", fragment)
    return DetailSection(title, level, fields, block_text(rest))


def block_text(fragment: str) -> str:
    """Text mit Zeilenumbruechen (<br>, Absaetze), Leerraum je Zeile
    zusammengefasst, hoechstens eine Leerzeile am Stueck."""
    fragment = LINE_END.sub("\n", NOISE.sub("", fragment))
    plain = htmlmod.unescape(re.sub(r"<[^>]+>", " ", fragment))
    lines = [re.sub(r"[ \t\xa0]+", " ", line).strip() for line in plain.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def detail_title(sections: list[DetailSection], fallback: str) -> str:
    """Erstes Feld "Titel" (Seitentitel ist nur "Detailansicht - ...")."""
    for section in sections:
        for label, value in section.fields:
            if label == "Titel" and value:
                return value
    return fallback


def detail_markdown(title: str, sections: list[DetailSection]) -> str:
    """Alles als Markdown (Anzeige in der TUI, Export)."""
    parts = [f"# {title}"]
    top = min((section.level for section in sections), default=1)
    for section in sections:
        parts.append(_section_markdown(section, section.level - top + 2))
    return "\n\n".join(parts) + "\n"


def _section_markdown(section: DetailSection, heading: int) -> str:
    """heading: Markdown-Ebene (2 = oberster Abschnitt unter dem Titel)."""
    lines = ["#" * min(heading, 6) + " " + section.title]
    lines += [f"- **{label}**: {value}" for label, value in section.fields]
    for paragraph in section.text.split("\n\n") if section.text else []:
        lines += ["", paragraph.replace("\n", "  \n")]  # Zeilenumbruch bleibt
    return "\n".join(lines)
