"""Links einer Seite im Tree-Widget: Beschriftung, Aufbau, gemerktes Zuklappen."""

from urllib.parse import urlsplit, urlunsplit

from rich.text import Text
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from hisinone.explore.html_text import link_name
from hisinone.explore.link_tree import TreeEntry
from hisinone.explore.links import Link


def link_label(link: Link, host: str) -> Text:
    text = Text(link_name(link.label) or link.label)
    if urlsplit(link.url).netloc != host:
        text.append(" ext", style="yellow")
    if link.label.startswith("[permalink]"):
        text.append(" ◆", style="cyan")
    if link.flow_bound:
        text.append(" [flow]", style="magenta")
    if link.is_logout:
        text.stylize("red")
    return text


def link_details(link: Link | None, host: str) -> Text:
    """Rechte Spalte: markierter Link (eigener Server ohne Host)."""
    out = Text()
    if link:
        parts = urlsplit(link.url)
        shown = (
            link.url if parts.netloc != host else urlunsplit(("", "", parts.path, parts.query, ""))
        )
        out.append("\n\nMarkierter Link\n", style="bold")
        out.append(link_name(link.label) + "\n")
        out.append(shown, style=f"dim link {link.url}")
    return out


class LinkTreeFiller:
    """Füllt den Baum aus TreeEntry-Zeilen. Jeder Knoten bekommt einen Pfad
    aus Beschriftungen ("Eltern › Kind"), unter dem sein Zuklappen gemerkt wird."""

    def __init__(self, tree: Tree, host: str, collapsed: set[str]):
        self.tree, self.host, self.collapsed = tree, host, collapsed
        self.node_paths: dict = {}  # Knoten-ID -> Pfad

    def fill(self, entries: list[TreeEntry]) -> dict:
        self.tree.clear()
        # Tiefe -> Elternknoten: jeder Eintrag hängt am letzten flacheren Knoten
        stack: list[tuple[int, TreeNode, str]] = [(-1, self.tree.root, "")]
        for entry in entries:
            while stack[-1][0] >= entry.depth:
                stack.pop()
            _, parent, parent_path = stack[-1]
            node, path = self._add(parent, parent_path, entry)
            stack.append((entry.depth, node, path))
        for node in list(self.tree.root.children):
            _leafify(node)
        self.tree.root.expand()
        return self.node_paths

    def _add(self, parent: TreeNode, parent_path: str, entry: TreeEntry) -> tuple[TreeNode, str]:
        link = entry.link
        plain = (link_name(entry.label) or entry.label) if link else entry.label.lstrip("─ ")
        path = f"{parent_path} › {plain}" if parent_path else plain
        expand = path not in self.collapsed
        if link:
            node = parent.add(link_label(link, self.host), data=link, expand=expand)
        else:  # Gruppen-Überschrift
            node = parent.add(Text(plain, style="bold"), expand=expand)
        self.node_paths[node.id] = path
        return node, path


def _leafify(node: TreeNode) -> None:
    """Knoten ohne Kinder als Blatt darstellen (kein Aufklapp-Pfeil)."""
    if not node.children:
        node.allow_expand = False
    for child in node.children:
        _leafify(child)
