"""Kleine HTML-Helfer (Regex, nur Standardbibliothek)."""

import html as htmlmod
import re


def text_of(fragment: str) -> str:
    """Sichtbarer Text eines HTML-Fragments, Leerraum zusammengefasst."""
    without_tags = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", htmlmod.unescape(without_tags)).strip()


def attribute(tag: str, name: str) -> str:
    """Wert des Attributs `name` in einem einzelnen Tag ("" wenn fehlt)."""
    match = re.search(rf'\b{name}="([^"]*)"', tag)
    return htmlmod.unescape(match.group(1)) if match else ""


def page_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return text_of(match.group(1)) if match else ""


def link_name(label: str) -> str:
    """Linkname ohne Markierungen und Screenreader-Zusätze."""
    label = re.sub(r"^\[(permalink|iframe)\]\s*", "", label)
    for noise in ("Sie befinden sich hier:", "Zur nächsten Navigationsebene"):
        label = label.replace(noise, "")
    return label.strip()
