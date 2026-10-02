"""Allgemeine Seitenansicht: der Inhaltsbereich einer HISinOne-Seite (ohne
Navigation, Kopf und Fuß) als Markdown. Gilt für jede Seite, die keine eigene
Ansicht hat (Studienplaner, Detailseite, Baum-Tabellen)."""

import re

from .detail_tables import absolute_links
from .html_markdown import html_to_markdown

# Rahmen des Seiteninhalts im HISinOne-Layout; fehlt er, gilt der ganze <body>
CONTENT_START = re.compile(r'<div\b[^>]*\bid="contentFrame"')
BODY_START = re.compile(r"<body\b", re.I)
DIV_TAG = re.compile(r"<(/?)div\b", re.I)
# Seiten, die erst der Browser per JavaScript füllt (z.B. Angular), sind leer
EMPTY_NOTE = (
    "*Diese Seite enthält ohne Browser keinen lesbaren Inhalt (sie wird "
    "vermutlich erst per JavaScript aufgebaut). Taste o öffnet sie im Browser.*"
)


def content_fragment(html: str) -> str:
    """HTML des Inhaltsbereichs bis zum passenden </div>."""
    start = CONTENT_START.search(html)
    if not start:
        body = BODY_START.search(html)
        return html[body.start() :] if body else html
    depth = 0
    for tag in DIV_TAG.finditer(html, start.start()):
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            return html[start.start() : tag.end()]
    return html[start.start() :]


def page_markdown(html: str, title: str, base_url: str) -> str:
    """Markdown mit absoluten Links; Titel nur, wenn die Seite keinen hat."""
    markdown = html_to_markdown(content_fragment(html)) or EMPTY_NOTE
    if not re.search(r"^# ", markdown, re.M):
        markdown = f"# {title}\n\n{markdown}"
    return absolute_links(markdown, base_url) + "\n"
