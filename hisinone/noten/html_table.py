"""Tabellen aus HTML als Text-Zellen (nur Standardbibliothek)."""

import html as htmlmod
import re


def row_cells(row_html: str) -> list[str]:
    cells = []
    for match in re.finditer(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", row_html, re.S | re.I):
        text = htmlmod.unescape(re.sub(r"<[^>]+>", " ", match.group(1)))
        cells.append(re.sub(r"\s+", " ", text).strip())
    return cells


def tables(html: str) -> list[str]:
    return re.findall(r"(?is)<table\b.*?</table>", html)


def rows(table_html: str) -> list[list[str]]:
    return [row_cells(row) for row in re.findall(r"(?is)<tr\b.*?</tr>", table_html)]


def norm_label(label: str) -> str:
    """Macht aus einem Tabellen-Label einen schlanken JSON-Key."""
    lowered = label.lower()
    lowered = lowered.replace("(angestrebter) abschluss", "angestrebter_abschluss")
    lowered = lowered.replace("geburtsdatum und -ort", "geburtsdatum")
    return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
