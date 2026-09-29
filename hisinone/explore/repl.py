"""Interaktive Befehlsschleife des Kommandozeilen-Explorers (Befehle siehe
Docstring von explore.py)."""

from pathlib import Path
from urllib.parse import urljoin

import requests

from hisinone.noten import HISinOneError

from .browser import PageBrowser
from .clipboard import copy_to_clipboard
from .console import hyperlink, print_leistungen, show_links
from .html_text import page_title
from .leistungen import LEISTUNGEN_PATH, fetch_leistungen
from .link_tree import TreeEntry, flat_entries, tree_order
from .links import clean_url, extract_links

HELP = "Unbekannter Befehl (Nr, !Nr, a, t, b, r, h, c [Nr], l, /text, u <url>, s <datei>, q)."


class ExplorerRepl:
    """Zeigt die Links der aktuellen Seite und fuehrt einen Befehl aus."""

    def __init__(self, browser: PageBrowser, sort: bool, tree: bool):
        self.browser = browser
        self.sort, self.tree = sort, tree
        self.text_filter = ""
        self.entries: list[TreeEntry] = []  # angezeigte Liste (Nummer = Index + 1)
        # Befehle ohne Argument
        self.simple_commands = {
            "b": browser.back, "r": browser.reload, "h": browser.home,
            "a": self.toggle_sort, "t": self.toggle_tree, "l": self.show_leistungen,
        }  # fmt: skip

    def run(self) -> int:
        while True:
            self.render()
            try:
                command = input("\n> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if command == "q":
                return 0
            self.execute(command)

    def render(self) -> None:
        page = self.browser.page
        links = extract_links(page.html, page.server_url, sort=self.sort and not self.tree)
        self.entries = tree_order(links, sort=self.sort) if self.tree else flat_entries(links)
        print("\n" + "=" * 100)
        print(page_title(page.html))
        print(f"Stabil: {hyperlink(page.stable_url, page.stable_url)}")
        if page.server_url != page.stable_url:
            print(f"Server: {hyperlink(page.server_url, page.server_url)}")
        order = "alphabetisch" if self.sort else "Seitenreihenfolge"
        extras = (", Baum" if self.tree else "") + (
            f"  (Filter: {self.text_filter})" if self.text_filter else "")  # fmt: skip
        print(f"{len(links)} Links, {order}{extras}")
        print("-" * 100)
        show_links(self.entries, self.browser.host, self.text_filter)

    def execute(self, command: str) -> None:
        prefix_commands = {"/": self.set_filter, "u ": self.open_path, "s ": self.save_to}
        if command in self.simple_commands:
            self.simple_commands[command]()
        elif command == "c" or command.startswith("c "):
            self.copy_url(command[1:].strip())
        elif command.lstrip("!").isdigit():
            self.open_number(command)
        elif prefix := next((p for p in prefix_commands if command.startswith(p)), None):
            prefix_commands[prefix](command[len(prefix) :].strip())
        elif command:
            print(HELP)

    def toggle_sort(self) -> None:
        self.sort = not self.sort

    def toggle_tree(self) -> None:
        self.tree = not self.tree

    def set_filter(self, text: str) -> None:
        self.text_filter = text.casefold()

    def open_path(self, target: str) -> None:
        self.browser.open(clean_url(urljoin(self.browser.page.server_url, target)))

    def save_to(self, file_name: str) -> None:
        Path(file_name).write_text(self.browser.page.html, encoding="utf-8")
        print(f"Gespeichert: {file_name}")

    def _entry_url(self, number: int) -> str:
        """URL von Link Nr (0 = aktuelle Seite), "" wenn es keinen gibt."""
        if number == 0:
            return self.browser.page.stable_url
        link = self.entries[number - 1].link if number <= len(self.entries) else None
        return link.url if link else ""

    def copy_url(self, argument: str) -> None:
        if not argument:
            url = self.browser.page.stable_url
        elif argument.isdigit():
            url = self._entry_url(int(argument))
        else:
            url = ""
        if url:
            print(f"Kopiert ({copy_to_clipboard(url)}): {url}")
        else:
            print("Keine URL unter dieser Nummer.")
        input("[Enter] ")

    def open_number(self, command: str) -> None:
        number = int(command.lstrip("!"))
        if not 1 <= number <= len(self.entries):
            print(HELP)
            return
        link = self.entries[number - 1].link
        if link is None:
            print("Das ist eine Gruppen-Ueberschrift, kein Link.")
        elif link.flow_bound and not command.startswith("!"):
            print(f"'{link.label}' ist flow-gebunden (_flowExecutionKey, keine stabile URL)."
                  f"\nTrotzdem folgen mit !{command}")  # fmt: skip
            input("[Enter] ")
        else:
            self.browser.open(link.url, link.label)

    def show_leistungen(self) -> None:
        browser = self.browser
        try:
            rows, tree_html = fetch_leistungen(browser.session, browser.client)
        except (HISinOneError, requests.RequestException) as error:
            print(f"Fehler: {error}")
        else:
            url = browser.client.qis_base + LEISTUNGEN_PATH
            browser.save(url, tree_html, "Leistungen_aufgeklappt")
            print_leistungen(rows)
        input("[Enter] ")
