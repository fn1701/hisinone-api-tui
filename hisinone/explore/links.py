"""Links einer Seite finden und stabile URLs bilden.

Der ``_flowExecutionKey`` (z. B. ``e4s1``) gilt nur für den gerade laufenden
Flow. Aus Links mit ``_flowId`` wird er entfernt - die starten den Flow damit
einfach neu. Links ohne ``_flowId`` gehören zu einem laufenden Flow, behalten
ihren Key und gelten als flow-gebunden (keine stabile URL).
"""

import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from .html_text import attribute, text_of

SKIP_EXT = (".css", ".js", ".ico", ".png", ".gif", ".jpg", ".jpeg", ".svg", ".woff", ".woff2")
SKIP_SCHEMES = ("#", "javascript:", "mailto:", "tel:")
DROP_PARAMS = {"_flowExecutionKey"}

# <a>, <iframe>, Baum-Namen und Permalinks in einem Durchlauf, damit die
# Seitenreihenfolge stimmt. Permalinks stehen als verstecktes
# <input value="...startFlow.xhtml?_flowId=...">; ihr Name steht im
# vorangehenden "treeElementName" (z. B. im Vorlesungsverzeichnis).
LINK_PATTERN = re.compile(
    r"(?P<a_tag><a\b[^>]*>)(?P<a_text>.*?)</a>"
    r"|(?P<iframe><iframe\b[^>]*>)"
    r'|class="treeElementName"(?P<tree_name>.*?)</td>'
    r'|(?P<permalink><input\b[^>]*\bvalue="[^"]*_flowId=[^"]*"[^>]*>)',
    re.S | re.I,
)


@dataclass
class Link:
    label: str
    url: str
    flow_bound: bool  # hatte _flowExecutionKey, aber keine _flowId

    @property
    def needs_confirm(self) -> bool:
        """Nur mit "!" öffnen (nicht stabil / Abmelden)."""
        return self.flow_bound or self.is_logout

    @property
    def is_logout(self) -> bool:
        return "auth.logout" in urlsplit(self.url).query


def clean_url(url: str) -> str:
    """Entfernt flüchtige Parameter (_flowExecutionKey) und den Standard-Port
    (Permalinks enthalten z. B. ``campus.example.org:443``) aus der URL."""
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if key not in DROP_PARAMS]  # fmt: skip
    netloc = parts.netloc.removesuffix(":443") if parts.scheme == "https" else parts.netloc
    return urlunsplit((parts.scheme, netloc, parts.path, urlencode(query), ""))


def extract_links(html: str, base: str, sort: bool = False) -> list[Link]:
    """Links dedupliziert in Seitenreihenfolge (oder alphabetisch mit sort=True)."""
    collector = LinkCollector(base)
    collector.scan(html)
    links = collector.links()
    if sort:
        links.sort(key=lambda link: (link.label.casefold(), link.url))
    return links


class LinkCollector:
    """Sammelt Links einer Seite, je URL einer (mit der längsten Beschriftung)."""

    def __init__(self, base: str):
        self.base = base
        self.found: dict[str, Link] = {}
        self.tree_name = ""  # Name des zuletzt gesehenen Baum-Knotens

    def links(self) -> list[Link]:
        return list(self.found.values())

    def scan(self, html: str) -> None:
        for match in LINK_PATTERN.finditer(html):
            self._handle(match)

    def _handle(self, match: re.Match) -> None:
        if match.group("a_tag"):
            tag = match.group("a_tag")
            label = text_of(match.group("a_text")) or attribute(tag, "title")
            self.add(label or attribute(tag, "aria-label"), attribute(tag, "href"))
        elif match.group("iframe"):
            tag = match.group("iframe")
            self.add("[iframe] " + attribute(tag, "title"), attribute(tag, "src"))
        elif match.group("tree_name") is not None:
            self.tree_name = text_of("<x " + match.group("tree_name"))
        else:
            self.add(f"[permalink] {self.tree_name}".strip(),
                     attribute(match.group("permalink"), "value"))  # fmt: skip

    def add(self, label: str, href: str) -> None:
        if not href or href.startswith(SKIP_SCHEMES):
            return
        raw = urljoin(self.base, href)
        query = urlsplit(raw).query
        flow_bound = "_flowExecutionKey=" in query and "_flowId=" not in query
        # Flow-gebundene Links brauchen den aktuellen Key, alle anderen nicht
        url = urlunsplit(urlsplit(raw)._replace(fragment="")) if flow_bound else clean_url(raw)
        path = urlsplit(url).path
        if path.lower().endswith(SKIP_EXT):
            return
        label = label or path.rsplit("/", 1)[-1] or url
        # Bei Doubletten die längere (aussagekräftigere) Beschriftung behalten
        known = self.found.get(url)
        if known is None or len(label) > len(known.label):
            self.found[url] = Link(label, url, flow_bound)


def match_links(links: list[Link], query: str, regex: bool) -> list[Link]:
    """Links, deren Beschriftung oder URL passt (Text oder regulärer
    Ausdruck, Groß-/Kleinschreibung egal); re.error bei ungültigem."""
    if not query:
        return links
    if regex:
        pattern = re.compile(query, re.IGNORECASE)
        return [link for link in links if pattern.search(f"{link.label} {link.url}")]
    text = query.casefold()
    return [link for link in links
            if text in link.label.casefold() or text in link.url.casefold()]  # fmt: skip
