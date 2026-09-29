"""Links als Baum ordnen.

Die Hierarchie steckt in den URLs selbst - Navigation in
``navigationPosition=a,b,c``, Vorlesungsverzeichnis-Permalinks in
``path=title:36|title:37|...``. Links ohne beides stehen unter "Sonstige".
"""

from dataclasses import dataclass
from urllib.parse import parse_qsl, urlsplit

from .links import Link

TreeKey = tuple[str, ...]


@dataclass
class TreeEntry:
    """Eine Zeile des Baums: Link oder Gruppen-Ueberschrift (link=None)."""

    label: str
    depth: int
    link: Link | None = None


def tree_key(url: str) -> TreeKey | None:
    """Position eines Links in der Hierarchie, direkt aus der URL."""
    query = dict(parse_qsl(urlsplit(url).query))
    if query.get("path"):
        return ("Vorlesungsverzeichnis", *query["path"].split("|"))
    nav = query.get("navigationPosition", "")
    if "," in nav or (nav and not nav.startswith(("link_", "switchTo"))):
        return ("Navigation", *nav.split(","))
    return None


def tree_order(links: list[Link], sort: bool = False) -> list[TreeEntry]:
    """Geschwister bleiben in Seitenreihenfolge (alphabetisch mit sort=True)."""
    return LinkTreeBuilder(links, sort).entries()


class LinkTreeBuilder:
    """Gruppiert Links nach tree_key und gibt den Baum in Tiefensuche aus."""

    def __init__(self, links: list[Link], sort: bool):
        self.sort = sort
        self.keyed: dict[TreeKey, list[Link]] = {}
        self.other: list[Link] = []
        for link in links:
            key = tree_key(link.url)
            if key is None:
                self.other.append(link)
            else:
                self.keyed.setdefault(key, []).append(link)
        self.children = self._link_children()

    def _link_children(self) -> dict[TreeKey, list[TreeKey]]:
        children: dict[TreeKey, list[TreeKey]] = {}
        for key in self.keyed:
            children.setdefault(self._nearest_parent(key), []).append(key)
        if self.sort:
            for kids in children.values():
                kids.sort(key=lambda kid: self.keyed[kid][0].label.casefold())
        return children

    def _nearest_parent(self, key: TreeKey) -> TreeKey:
        # Zwischenebenen koennen fehlen -> naechsten vorhandenen Vorfahren nehmen
        parent = key[:-1]
        while len(parent) > 1 and parent not in self.keyed:
            parent = parent[:-1]
        return parent

    def entries(self) -> list[TreeEntry]:
        out: list[TreeEntry] = []
        for root in dict.fromkeys(key[0] for key in self.keyed):
            out.append(TreeEntry(f"── {root}", 0))
            self._walk((root,), 1, out)
        if self.other:
            out.append(TreeEntry("── Sonstige", 0))
            other = sorted(self.other, key=lambda link: link.label.casefold()) \
                if self.sort else self.other  # fmt: skip
            out.extend(TreeEntry(link.label, 1, link) for link in other)
        return out

    def _walk(self, parent: TreeKey, depth: int, out: list[TreeEntry]) -> None:
        for key in self.children.get(parent, []):
            out.extend(TreeEntry(link.label, depth, link) for link in self.keyed[key])
            self._walk(key, depth + 1, out)


def flat_entries(links: list[Link]) -> list[TreeEntry]:
    """Flache Liste (ohne Baum) im selben Format."""
    return [TreeEntry(link.label, 0, link) for link in links]
