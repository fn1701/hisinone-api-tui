"""Beliebiges HTML-Fragment als Markdown, für Seiten ohne eigene Ansicht:
Überschriften, Absätze, Listen und Links; Tabellen wie in Detailseiten
(detail_tables). Nur Standardbibliothek (HTMLParser), kein Seitenmuster."""

import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .detail_tables import replace_tables

# Bedienelemente und Unsichtbares tragen keinen lesbaren Inhalt
SKIPPED = {"script", "style", "noscript", "button", "select", "textarea", "head"}
HIDDEN_CLASS = re.compile(r"\b(visibilityOnlyForScreenreader|hidden)\b")
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6, "legend": 3}
LINE_TAGS = {"div", "p", "tr", "dt", "dd", "label", "fieldset", "form", "section", "ul", "ol"}
VOID = {"br", "img", "input", "hr", "meta", "link", "col", "wbr"}
TABLE_MARK = re.compile(r"\s*\x00(\d+)\x00\s*")


class MarkdownWriter(HTMLParser):
    """Sammelt Markdown-Stücke beim Durchlaufen der Tags."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._skip: list[str] = []  # offene Tags, deren Inhalt wegfällt
        self._link_start: int | None = None
        self._link_href = ""
        self._list_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        hidden = tag in SKIPPED or HIDDEN_CLASS.search(dict(attrs).get("class") or "")
        if self._skip or hidden:
            if tag not in VOID:  # Void-Tags haben kein Ende, das das Auslassen beendet
                self._skip.append(tag)
            return
        self._open(tag, dict(attrs))

    def handle_endtag(self, tag: str) -> None:
        if not self._skip:
            self._close(tag)
        elif tag in self._skip:  # bis zum passenden Tag schließen (auch bei kaputtem HTML)
            while self._skip.pop() != tag:
                pass

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(re.sub(r"\s+", " ", data))

    def _open(self, tag: str, attrs: dict[str, str | None]) -> None:
        if tag in HEADINGS:
            self.parts.append("\n\n" + "#" * HEADINGS[tag] + " ")
        elif tag == "li":
            self.parts.append("\n" + "  " * max(self._list_depth - 1, 0) + "- ")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "a":
            self._start_link(attrs.get("href") or "")
        elif tag in LINE_TAGS:
            self._list_depth += tag in ("ul", "ol")
            self.parts.append("\n")

    def _close(self, tag: str) -> None:
        if tag in HEADINGS or tag == "p":
            self.parts.append("\n\n")
        elif tag == "a":
            self._end_link()
        elif tag in LINE_TAGS or tag == "li":
            self._list_depth -= tag in ("ul", "ol")
            self.parts.append("\n")

    def _start_link(self, href: str) -> None:
        """Nur echte Ziele: "#"/javascript: sind Skript-Knöpfe, Abmelden nie."""
        usable = href and not href.startswith(("#", "javascript:"))
        if usable and "auth.logout" not in urlsplit(href).query:
            self._link_start, self._link_href = len(self.parts), href
            self.parts.append("[")

    def _end_link(self) -> None:
        """Linktext auf eine Zeile; Link ohne Text (nur Symbol) fällt weg."""
        if self._link_start is None:
            return
        text = re.sub(r"\s+", " ", "".join(self.parts[self._link_start + 1 :])).strip()
        del self.parts[self._link_start :]
        if text:
            self.parts.append(f"[{text}]({self._link_href.replace(' ', '%20')})")
        self._link_start = None


def html_to_markdown(fragment: str) -> str:
    """Markdown eines HTML-Fragments; Link-Ziele bleiben wie im HTML."""
    tables: list[str] = []
    writer = MarkdownWriter()
    writer.feed(replace_tables(fragment, tables))
    writer.close()
    text = _tidy("".join(writer.parts))

    def _table(match: re.Match[str]) -> str:
        return f"\n\n{tables[int(match.group(1))]}\n\n"

    return re.sub(r"\n{3,}", "\n\n", TABLE_MARK.sub(_table, text)).strip()


def _tidy(text: str) -> str:
    """Leerraum je Zeile kürzen, leere und doppelte Überschriften weg,
    Zeilen eines Absatzes mit hartem Umbruch."""
    lines = _without_repeats([line.strip() for line in text.split("\n")])
    for index in range(len(lines) - 1):
        if lines[index] and lines[index + 1] and not lines[index + 1].startswith(("-", "#")):
            lines[index] += "  "
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines))


def _without_repeats(lines: list[str]) -> list[str]:
    """Überschrift wie die vorige (h2 + legend) oder ohne Text weglassen;
    ein Listenpunkt, dessen Inhalt erst in der nächsten Zeile steht, wird eins."""
    result: list[str] = []
    last_heading = ""
    for line in lines:
        heading = line.lstrip("#").strip() if line.startswith("#") else None
        if heading is not None and heading in ("", last_heading):
            continue
        last_heading = heading if heading is not None else (last_heading if not line else "")
        if line and result and result[-1] == "-":
            result[-1] = f"- {line}"
        elif line or not (result and result[-1] == "-"):
            result.append(line)
    return result
