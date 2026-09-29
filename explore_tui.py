#!/usr/bin/env python3
"""
HISinOne-Explorer als Terminal-Oberflaeche (Textual): Links einer Seite als
Baum, per Klick oder Enter oeffnen. Die Logik (Login, Links, Baum, stabile
URLs, Speichern) kommt aus explore.py - siehe dort fuer Details.

Installation (einmalig, in die venv des Projekts):
    uv venv .venv   # falls noch keine .venv existiert
    uv pip install --python .venv/bin/python -r requirements.txt

Starten mit .venv/bin/python explore_tui.py (oder nach ". .venv/bin/activate"
einfach python explore_tui.py).

Benutzung (aus dem Projekt-Hauptordner, .env wie bei login_test.py):
    python explore_tui.py           # Baumansicht
    python explore_tui.py --flat    # flache Liste in Seitenreihenfolge
    python explore_tui.py --sort    # alphabetisch
    python explore_tui.py --save    # jede besuchte Seite nach /tmp/hisinone-explore/
    python explore_tui.py --save DIR

Bedienung:
    Klick / Enter   Link oeffnen          Leertaste / Pfeile  auf-/zuklappen
    !               flow-gebundenen oder Abmelde-Link trotzdem oeffnen
    /               Filter (Esc = zurueck zur Liste)
    b r h           zurueck / neu laden / Startseite
    t a             Baum an/aus / alphabetisch an/aus
    c               URL (markierter Link, sonst Seite) in die Zwischenablage
    o               URL im Browser oeffnen (neue Browser-Sitzung, ohne Login!)
    s               Speichern an/aus (Ordner aus --save, sonst /tmp/hisinone-explore;
                    beim Einschalten wird die aktuelle Seite gleich gespeichert)
    l               Leistungen laden, Tabelle "Leistungsdaten" im Vollbild
                    (Tasten wie l sind in der Config unter "shortcuts" einstellbar)
    q               beenden

Tabellen: Seiten mit Baum-Tabelle (Leistungen, Vorlesungsverzeichnis, ...)
oeffnen zusaetzlich alle Tabellen auf einem Bildschirm (Esc = zurueck zu den
Links). Gibt es genau einen "Alle aufklappen"-Button, wird er einmal geklickt
(1 Request). Klick auf die Titelleiste oder f = Tabelle im Vollbild, dort:
    /               Zeilenfilter: Text oder Spalte=Wert, mehrere mit Leerzeichen
                    (alle muessen passen); Klick/↓ = Vorschlagsliste
                    z.B. Art=PL, Art=PVL, Typ=Modul, Status=BE
    k               Spalten ein-/ausblenden (je Tabelle gemerkt)
    x               eigene Spalten an/aus (nur wenn es welche gibt, lila):
                    Typ (Symbol im Titel), Art (PL/PVL, nur Leistungen)
    v               nur letzter Versuch (nur Leistungen)
    e               Export der sichtbaren Zeilen/Spalten (.csv/.json)

Einstellungen (Baum, alphabetisch, Speichern an/aus + Ordner, je Tabelle
Spalten/eigene Spalten/letzter Versuch/Filter) stehen in
~/.config/hisinone-explore/config.json (0600, enthaelt ggf. Filter mit
Modulnamen). Gelesen beim Start; geschrieben beim Beenden und alle 100 s,
aber nur wenn sich etwas geaendert hat. Angegebene Optionen (--flat, --sort,
--save) gehen vor; --no-config schaltet die Datei ab.

Zwischen Schritten, die im Browser ein Klick waeren, wird zufaellig
200-1000 ms gewartet (siehe Pacer in explore.py).
"""

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import requests
from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult, SystemCommand
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (DataTable, Footer, Header, Input, OptionList, SelectionList,
                             Static, Tree)
from textual.widgets.option_list import Option

from explore import (LEISTUNGEN_PATH, TREE_TABLE, clean_url, copy_external, expand_tree_tables,
                     export_leistungen, extract_links, filter_suggestions,
                     latest_attempts_tree, link_name, login, match_rows, pacer, page_title,
                     parse_tree_tables, prepare_save_dir, save_html, tree_order)
from hisinone_noten import HISinOneClient, HISinOneError


@dataclass
class Link:
    label: str
    url: str
    flow_bound: bool

    @property
    def needs_confirm(self) -> bool:
        """Links, die nur mit "!" geoeffnet werden (nicht stabil / Abmelden)."""
        return self.flow_bound or "auth.logout" in urlsplit(self.url).query


class TableBar(Horizontal):
    """Titelleiste ueber einer Tabelle: Name mittig, Aktion rechts;
    Klick = Tabelle einzeln im Vollbild."""

    def __init__(self, index: int, text: str, clickable: bool):
        super().__init__(classes="clickable" if clickable else "")
        self.index, self.text, self.clickable = index, text, clickable

    def compose(self) -> ComposeResult:
        yield Static("▸" if self.clickable else "", classes="side")
        yield Static(self.text, classes="name")
        yield Static("erweitern (f)" if self.clickable else "", classes="side action")

    def on_click(self) -> None:
        if self.clickable:
            self.screen.open_single(self.index)


# Spaltenauswahl je Tabelle (Name + Original-Spalten), solange die TUI laeuft
# Einstellungen je Tabelle (Spalten, eigene Spalten, letzter Versuch, Filter),
# Schluessel "Name [Spalte,Spalte,...]"; wird aus der Config geladen/gespeichert
TABLE_PREFS: dict[str, dict] = {}

CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") \
    / "hisinone-explore" / "config.json"
AUTOSAVE_SECONDS = 100

# Tasten, die eine feste Seite oeffnen (Config "shortcuts"). path: relativ zur
# HISinOne-Adresse oder volle URL; open_table_with_column: nach dem Laden die
# erste Tabelle mit dieser Spalte im Vollbild oeffnen (leer = alle Tabellen)
DEFAULT_SHORTCUTS = [{"key": "l", "description": "Leistungen", "path": LEISTUNGEN_PATH,
                      "open_table_with_column": "Versuch"}]


def load_config(path: Path = CONFIG_PATH) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        print(f"Config {path} nicht lesbar ({e}), nutze Standardwerte")
        return {}


def write_config(cfg: dict, path: Path = CONFIG_PATH) -> None:
    """Atomar schreiben (tmp + rename), nur fuer den Benutzer lesbar
    (Filter koennen Modulnamen/Noten enthalten)."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
CUSTOM_STYLE = "italic magenta"  # eigene (berechnete) Spalten


def table_name(t: dict) -> str:
    if t.get("name"):
        return t["name"]
    title_col = next((c for c in t["cols"] if c != "Ebene"), "")
    return next((r[title_col] for r in t["rows"] if r.get(title_col)), "Tabelle")


class TreeTableScreen(Screen):
    """Baum-Tabellen einer Seite unveraendert als Tabelle (Esc = zurueck).
    Ueber jeder Tabelle eine Titelleiste: Klick oder f = Tabelle im Vollbild.
    Im Vollbild: Zeilenfilter (/), Spalten (k), eigene Spalten (x),
    letzter Versuch (v), Export (e)."""
    BINDINGS = [Binding("escape", "back", "Zurueck"),
                Binding("f", "fullscreen", "Vollbild"),
                Binding("slash", "focus_filter", "Filter"),
                Binding("k", "columns", "Spalten"),
                Binding("x", "toggle_custom", "Eigene Spalten"),
                Binding("v", "toggle_latest", "Letzter Versuch"),
                Binding("e", "export", "Export"),
                Binding("down", "open_suggest", "", show=False)]
    # Alle Tabellen auf einen Bildschirm: kleine (<= 10 Zeilen) in voller Hoehe,
    # groessere teilen sich den Rest, mindestens 10 Zeilen + Kopf + ggf.
    # waagrechter Scrollbalken, mit eigenem Scrollbalken. Die aeussere
    # Scrollleiste erscheint nur, wenn das Terminal dafuer zu niedrig ist.
    # (Hoehe der grossen wird in fit_tables berechnet - "1fr" loest sich in
    # einem Scroll-Container nicht zuverlaessig auf.)
    CSS = """
    TreeTableScreen DataTable { height: auto; }
    TableBar { height: 1; background: $boost; color: $text-muted; padding: 0 1; }
    TableBar .name { width: auto; text-style: bold; }
    TableBar .side { width: 1fr; }
    TableBar .action { text-align: right; }
    TableBar.clickable:hover { background: $accent; color: $text; }
    #suggest { display: none; overlay: screen; max-height: 12; width: 60;
               border: tall $accent; background: $panel; }
    #suggest.shown { display: block; }
    """
    MIN_ROWS = 10

    def __init__(self, name: str, tables: list[dict], single: bool = False):
        super().__init__()
        self.page_name, self.tables, self.single = name, tables, single
        if single:
            t = tables[0]
            self.native, self.custom = t["cols"], t.get("custom", [])
            self.choice_key = f"{table_name(t)} [{','.join(self.native)}]"
            prefs = TABLE_PREFS.get(self.choice_key, {})
            known = self.native + self.custom
            self.col_choice = [c for c in prefs.get("cols", known) if c in known] or known
            self.custom_on = bool(prefs.get("custom_on")) and bool(self.custom)
            self.latest = bool(prefs.get("latest"))
            self.start_filter = prefs.get("filter", "")
            self.shown_rows = t["rows"]

    # -- Anzeige ---------------------------------------------------------------

    def check_action(self, action: str, parameters) -> bool | None:
        if not self.single:
            return action in ("back", "fullscreen")
        if action == "fullscreen":
            return False
        if action == "toggle_custom":
            return bool(self.custom)
        if action == "toggle_latest":
            return self.can_latest
        return True

    @property
    def can_latest(self) -> bool:
        return "Art" in self.custom and {"Ebene", "Versuch"} <= set(self.native)

    def compose(self) -> ComposeResult:
        yield Header()
        if self.single:
            yield Input(self.start_filter, id="rowfilter",
                        placeholder="Zeilen filtern: Text oder Spalte=Wert, mehrere mit "
                                    "Leerzeichen (↓ = Vorschlaege)")
            yield OptionList(id="suggest")
        with VerticalScroll():
            for i, t in enumerate(self.tables):
                bar = TableBar(i, f"{table_name(t)} · {len(t['rows'])} Zeilen",
                               clickable=not self.single)
                if i:
                    bar.styles.margin = (1, 0, 0, 0)  # Leerzeile zwischen Tabellen
                bar.tooltip = None if self.single else "Klick oder f: Vollbild"
                yield bar
                table = DataTable(zebra_stripes=True, cursor_type="row")
                self.fill(table, t["rows"], t["cols"], t)
                yield table
        yield Footer()

    def fill(self, table: DataTable, rows: list[dict], cols: list[str], t: dict) -> None:
        table.clear(columns=True)
        custom = set(t.get("custom", []))
        for c in cols:
            table.add_column(Text(c, style=CUSTOM_STYLE) if c in custom else c)
        title_col = next((c for c in t["cols"] if c != "Ebene"), None)
        for r in rows:
            cells = []
            for c in cols:
                v = str(r.get(c, ""))
                if c == title_col:
                    v = Text("  " * r["tiefe"] + v, style="bold" if r["tiefe"] == 0 else "")
                elif c in custom:
                    v = Text(v, style=CUSTOM_STYLE)
                cells.append(v)
            table.add_row(*cells)
        table.set_class(len(rows) > self.MIN_ROWS, "big")

    def on_mount(self) -> None:
        if self.single:
            self.refresh_single()
            self.query_one(DataTable).focus()  # sonst landen x/k/v/e im Filterfeld
        else:
            self.sub_title = f"{self.page_name}: {len(self.tables)} Tabelle(n)"
        self.call_after_refresh(self.fit_tables)

    def on_resize(self) -> None:
        self.call_after_refresh(self.fit_tables)

    def fit_tables(self) -> None:
        # abzueglich der Leerzeilen zwischen den Tabellen
        avail = (self.query_one(VerticalScroll).scrollable_content_region.height
                 - (len(self.tables) - 1))
        # kleine Tabellen: eigene Hoehe + 1 Zeile Titelleiste
        small = sum(t.outer_size.height + 1 for t in self.query(DataTable)
                    if not t.has_class("big"))
        for t in self.query(DataTable):
            if not t.has_class("big"):
                t.styles.height = "auto"
        # grosse: gleichmaessig teilen, aber keine hoeher als ihr Inhalt (Zeilen +
        # Kopf + waagrechter Scrollbalken); ueberschuessiger Platz geht an die
        # uebrigen. Jede bekommt mind. MIN_ROWS Zeilen. (+1 = Titelleiste)
        need = {t: t.row_count + 2 for t in self.query("DataTable.big")}
        left, rest = avail - small, dict(need)
        while rest:
            share = left // len(rest) - 1
            fits = {t: n for t, n in rest.items() if n <= share}
            if not fits:
                break
            for t, n in fits.items():
                t.styles.height = n
                left -= n + 1
                del rest[t]
        for t in rest:
            t.styles.height = max(self.MIN_ROWS + 2, left // len(rest) - 1)

    # -- Vollbild: Filter/Spalten ------------------------------------------------

    def active_cols(self) -> list[str]:
        """Angezeigte Spalten: eigene (wenn an) direkt hinter der Titelspalte."""
        cols = [c for c in self.native if c in self.col_choice]
        if self.custom_on:
            extra = [c for c in self.custom if c in self.col_choice]
            title_col = next((c for c in self.native if c != "Ebene"), None)
            at = cols.index(title_col) + 1 if title_col in cols else len(cols)
            cols[at:at] = extra
        return cols

    def filter_cols(self) -> list[str]:
        return self.native + (self.custom if self.custom_on else [])

    def refresh_single(self) -> None:
        t = self.tables[0]
        self.latest = self.latest and self.can_latest
        prefs = {"cols": self.col_choice, "custom_on": self.custom_on, "latest": self.latest,
                 "filter": self.query_one("#rowfilter", Input).value}
        # Standardzustand nicht speichern (blosses Oeffnen ist keine Aenderung)
        if prefs == {"cols": self.native + self.custom, "custom_on": False,
                     "latest": False, "filter": ""}:
            TABLE_PREFS.pop(self.choice_key, None)
        else:
            TABLE_PREFS[self.choice_key] = prefs
        rows = latest_attempts_tree(t["rows"]) if self.latest else t["rows"]
        self.shown_rows = match_rows(rows, self.filter_cols(),
                                     self.query_one("#rowfilter", Input).value)
        self.fill(self.query_one(DataTable), self.shown_rows, self.active_cols(), t)
        flags = [n for n, on_ in (("eigene Spalten", self.custom_on),
                                  ("letzter Versuch", self.latest)) if on_]
        self.sub_title = (f"{self.page_name}: {table_name(t)} · {len(self.shown_rows)} von "
                          f"{len(t['rows'])} Zeilen" + (f" ({', '.join(flags)})" if flags else ""))
        self.query_one(".name", Static).update(
            f"{table_name(t)} · {len(self.shown_rows)} von {len(t['rows'])} Zeilen")
        self.refresh_bindings()
        self.call_after_refresh(self.fit_tables)

    @on(Input.Changed, "#rowfilter")
    def rowfilter_changed(self) -> None:
        self.refresh_single()
        self.update_suggest()

    @on(Input.Submitted, "#rowfilter")
    def rowfilter_submitted(self) -> None:
        self.hide_suggest()
        self.query_one(DataTable).focus()

    # -- Vollbild: Vorschlagsliste unter dem Filter ---------------------------------

    def _last_term(self) -> str:
        v = self.query_one("#rowfilter", Input).value
        return "" if v.endswith(" ") else v.rsplit(" ", 1)[-1]

    def update_suggest(self) -> None:
        lst = self.query_one("#suggest", OptionList)
        if not lst.has_class("shown"):
            return
        last = self._last_term().lower()
        opts = [s for s in filter_suggestions(self.tables[0]["rows"], self.filter_cols())
                if last in s.lower()][:100]
        lst.clear_options()
        lst.add_options(opts or [Option("(keine Vorschlaege)", disabled=True)])

    def show_suggest(self) -> None:
        lst = self.query_one("#suggest", OptionList)
        lst.add_class("shown")
        self.update_suggest()

    def hide_suggest(self) -> None:
        self.query_one("#suggest", OptionList).remove_class("shown")

    def on_descendant_focus(self, event) -> None:
        if not self.single:
            return
        if event.widget.id == "rowfilter":
            self.show_suggest()
        elif event.widget.id != "suggest":
            self.hide_suggest()

    def on_click(self, event) -> None:
        # Klick ins schon fokussierte Filterfeld oeffnet die Liste ebenfalls
        if self.single and getattr(event.widget, "id", None) == "rowfilter":
            self.show_suggest()

    @on(OptionList.OptionSelected, "#suggest")
    def suggestion_picked(self, event: OptionList.OptionSelected) -> None:
        inp = self.query_one("#rowfilter", Input)
        last = self._last_term()
        inp.value = inp.value[:len(inp.value) - len(last)] + str(event.option.prompt) + " "
        inp.cursor_position = len(inp.value)
        inp.focus()

    @on(DataTable.HeaderSelected)
    def header_clicked(self, event: DataTable.HeaderSelected) -> None:
        """Klick auf Spaltenkopf: 'Spalte=' als letzten Filterbegriff setzen,
        Vorschlaege fuer diese Spalte zeigen."""
        if not self.single:
            return
        col = self.active_cols()[event.column_index]
        term = (f'"{col}"' if " " in col else col) + "="
        inp = self.query_one("#rowfilter", Input)
        inp.value = inp.value[:len(inp.value) - len(self._last_term())] + term
        inp.cursor_position = len(inp.value)
        inp.focus()
        self.show_suggest()

    def action_open_suggest(self) -> None:
        if self.single and self.focused and self.focused.id == "rowfilter":
            self.show_suggest()
            lst = self.query_one("#suggest", OptionList)
            if lst.highlighted is None and lst.option_count:
                lst.highlighted = 0
            lst.focus()

    # -- Aktionen ------------------------------------------------------------

    def action_back(self) -> None:
        if self.single:
            lst = self.query_one("#suggest", OptionList)
            if lst.has_class("shown"):
                self.hide_suggest()
                self.query_one("#rowfilter", Input).focus() if self.focused is lst else None
                return
            if self.focused and self.focused.id == "rowfilter":
                self.query_one(DataTable).focus()
                return
        self.app.pop_screen()

    def open_single(self, index: int) -> None:
        self.app.push_screen(TreeTableScreen(self.page_name, [self.tables[index]], single=True))

    def action_fullscreen(self) -> None:
        tables = list(self.query(DataTable))
        focused = self.focused
        # Fokus in keiner Tabelle -> die erste
        self.open_single(tables.index(focused) if focused in tables else 0)

    def action_focus_filter(self) -> None:
        self.query_one("#rowfilter", Input).focus()

    def action_toggle_custom(self) -> None:
        self.custom_on = not self.custom_on
        self.refresh_single()

    def action_toggle_latest(self) -> None:
        self.latest = not self.latest
        self.refresh_single()

    def action_columns(self) -> None:
        options = [(c, c, c in self.col_choice) for c in self.native]
        if self.custom_on:
            options += [(Text(f"{c} (eigene)", style=CUSTOM_STYLE), c, c in self.col_choice)
                        for c in self.custom]

        def done(chosen: list[str] | None) -> None:
            if chosen:
                # ausgeblendete eigene Spalten bleiben wie sie waren
                hidden_custom = [c for c in self.custom if c in self.col_choice
                                 and not self.custom_on]
                self.col_choice = chosen + hidden_custom
                self.refresh_single()
        self.app.push_screen(ColumnsDialog(options), done)

    def action_export(self) -> None:
        name = re.sub(r"[^\w.-]+", "_", table_name(self.tables[0]))
        default = (prepare_save_dir(self.app.save_path)
                   / f"{name}_{time.strftime('%Y-%m-%d_%H-%M-%S')}.csv")
        rows, cols = self.shown_rows, self.active_cols()

        def done(path: str | None) -> None:
            if not path:
                return
            try:
                out = export_leistungen(rows, Path(path).expanduser(), cols)
            except (ValueError, OSError) as e:
                self.notify(f"Export fehlgeschlagen: {e}", severity="error")
            else:
                self.notify(f"{len(rows)} Zeilen -> {out}")
        self.app.push_screen(ExportDialog(str(default)), done)


class ColumnsDialog(ModalScreen[list[str] | None]):
    """Spalten an-/abwaehlen (Leertaste), Enter = uebernehmen, Esc = abbrechen."""
    BINDINGS = [Binding("escape", "dismiss(None)", "Abbrechen"),
                Binding("enter", "apply", "Uebernehmen", priority=True)]
    CSS = "ColumnsDialog { align: center middle; } SelectionList { width: 50; height: 24; }"

    def __init__(self, options: list[tuple]):
        super().__init__()
        self.options = options  # (Anzeige, Schluessel, an?)

    def compose(self) -> ComposeResult:
        yield SelectionList[str](*self.options)
        yield Footer()

    def action_apply(self) -> None:
        chosen = self.query_one(SelectionList).selected
        # Reihenfolge wie angeboten
        self.dismiss([k for _, k, _ in self.options if k in chosen] or None)


class ExportDialog(ModalScreen[str | None]):
    """Dateipfad abfragen (.json oder .csv)."""
    BINDINGS = [Binding("escape", "dismiss(None)", "Abbrechen")]
    CSS = "ExportDialog { align: center middle; } Input { width: 80; }"

    def __init__(self, default: str):
        super().__init__()
        self.default = default

    def compose(self) -> ComposeResult:
        yield Input(value=self.default, placeholder="Pfad mit Endung .json oder .csv")
        yield Footer()

    @on(Input.Submitted)
    def submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)


class ExploreApp(App):
    TITLE = "HISinOne Explorer"
    CSS = """
    #filter { dock: top; }
    #links { width: 2fr; }
    #details { width: 1fr; border-left: solid $primary; padding: 0 1; }
    """
    BINDINGS = [
        Binding("b", "back", "Zurueck"),
        Binding("r", "reload", "Neu laden"),
        Binding("h", "home", "Startseite"),
        Binding("slash", "focus_filter", "Filter", priority=True),
        # show=False: nicht in der Fusszeile, nur Taste + Befehlspalette (Strg+P)
        Binding("t", "toggle_tree", "Baum an/aus", show=False),
        Binding("a", "toggle_sort", "Alphabetisch an/aus", show=False),
        Binding("exclamation_mark", "force_open", "Trotzdem oeffnen", show=False),
        Binding("c", "copy_url", "URL kopieren"),
        Binding("o", "browser", "Im Browser oeffnen", show=False),
        Binding("s", "toggle_save", "Speichern an/aus", show=False),
        Binding("escape", "focus_tree", "", show=False),
        Binding("q", "quit", "Beenden", show=False),
    ]

    def __init__(self, tree: bool, sort: bool, save_path: str, save_on: bool):
        super().__init__()
        self.tree_mode, self.sort = tree, sort
        # Ordner wird erst beim ersten Einschalten angelegt
        self.save_path, self.save_dir = save_path, None
        if save_on:
            self.save_dir = prepare_save_dir(save_path)
        self.session: requests.Session | None = None
        self.client: HISinOneClient | None = None
        self.home_url = ""
        self.stable_url, self.cur_name = "", ""
        self.cur_url, self.cur_html = "", ""
        self.history: list[tuple[str, str]] = []
        self.saved: Path | None = None
        self.host = ""
        self.shortcuts: list[dict] = DEFAULT_SHORTCUTS
        self.shortcuts_from_file = True  # False -> beim Beenden einmal schreiben

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="Filter (Name oder URL) ...", id="filter")
        with Horizontal():
            yield Tree("Anmelden ...", id="links")
            with VerticalScroll(id="details"):
                yield Static(id="page")
                yield Static(id="link")
        yield Footer()

    def check_action(self, action: str, parameters) -> bool | None:
        # Tasten der Link-Ansicht nur dort (auf Tabellen-Seiten gibt es kein
        # Linkbaum/Filterfeld; dort gelten deren eigene Tasten)
        if len(self.screen_stack) > 1 and action in {b.action for b in self.BINDINGS} | {"shortcut"}:
            return action == "quit"
        return True

    def get_system_commands(self, screen):
        """Alle Tasten-Befehle auch in der Befehlspalette (Strg+P)."""
        yield from super().get_system_commands(screen)
        for b in self.BINDINGS:
            if b.description:
                key = self.get_key_display(b)
                # Titel werden als Markup gelesen -> keine eckigen Klammern ("[/]")
                yield SystemCommand(f"{b.description} ({key})", f"Taste {key}",
                                    getattr(self, f"action_{b.action}"))
        for i, sc in enumerate(self.shortcuts):
            yield SystemCommand(f"{sc['description']} ({sc['key']})", f"Taste {sc['key']}",
                                lambda i=i: self.action_shortcut(i))

    def bind_shortcuts(self) -> None:
        taken = {k.strip() for b in self.BINDINGS for k in b.key.split(",")}
        for i, sc in enumerate(self.shortcuts):
            key = sc.get("key", "")
            if not key or not sc.get("path") or key in taken:
                self.notify(f"Shortcut {sc!r} ignoriert (Taste fehlt/belegt oder kein path)",
                            severity="warning")
                continue
            taken.add(key)
            self.bind(key, f"shortcut({i})", description=sc.get("description", key))

    def action_shortcut(self, i: int) -> None:
        sc = self.shortcuts[i]
        if self.session:
            path = sc["path"]
            url = path if path.startswith(("http://", "https://")) else self.client.qis_base + path
            self.open(url, sc.get("description", path),
                      open_col=sc.get("open_table_with_column", ""))

    # -- Config -----------------------------------------------------------------

    def config_snapshot(self) -> dict:
        return {"tree": self.tree_mode, "sort": self.sort, "save_on": bool(self.save_dir),
                "save_path": self.save_path, "shortcuts": self.shortcuts, "tables": TABLE_PREFS}

    def save_config(self) -> None:
        """Nur schreiben, wenn sich seit dem letzten Schreiben etwas geaendert hat."""
        snap = json.dumps(self.config_snapshot(), sort_keys=True, ensure_ascii=False)
        if snap == self.config_written:
            return
        try:
            write_config(self.config_snapshot())
            self.config_written = snap
        except OSError as e:
            self.notify(f"Config nicht speicherbar: {e}", severity="error")

    def on_unmount(self) -> None:
        self.save_config()

    def on_mount(self) -> None:
        # Ausgangsstand merken: geschrieben wird nur, was davon abweicht
        # ohne "shortcuts" in der Datei: einmal schreiben, damit die
        # Standard-Tasten dort sichtbar und editierbar sind
        self.config_written = json.dumps(self.config_snapshot(), sort_keys=True,
                                         ensure_ascii=False) if self.shortcuts_from_file else ""
        self.bind_shortcuts()
        self.set_interval(AUTOSAVE_SECONDS, self.save_config)
        tree = self.query_one("#links", Tree)
        tree.auto_expand = False  # Klick oeffnet den Link, klappt nicht nur auf
        tree.show_root = False
        tree.loading = True
        self.do_login()

    # -- Netzwerk (im Hintergrund-Thread, damit die Oberflaeche nicht haengt) --

    @work(thread=True, exclusive=True)
    def do_login(self) -> None:
        try:
            self.client = HISinOneClient.from_env()
            self.session, r = login(self.client)
        except (HISinOneError, requests.RequestException) as e:
            self.call_from_thread(self.exit, message=f"Fehler: {e}")
            return
        self.home_url = clean_url(r.url)
        self.host = urlsplit(self.home_url).netloc
        self.call_from_thread(self.show_page, self.home_url, "Startseite", r.url, r.text, False)

    @work(thread=True, exclusive=True)
    def fetch(self, url: str, name: str, push: bool = True, open_col: str = "") -> None:
        """open_col: danach die erste Tabelle mit dieser Spalte im Vollbild (Taste l)."""
        pacer.step()
        try:
            resp = self.session.get(url, timeout=self.client.timeout,
                                    headers={"Referer": self.cur_url})
        except requests.RequestException as e:
            self.call_from_thread(self.fetch_failed, f"Fehler: {e}")
            return
        resp.encoding = resp.encoding or "utf-8"
        ctype = resp.headers.get("Content-Type", "text/html")
        if "text/html" not in ctype:
            self.call_from_thread(self.fetch_failed,
                                  f"Kein HTML ({ctype}), {len(resp.content)} Bytes.")
            return
        if resp.status_code != 200:
            self.call_from_thread(self.notify, f"HTTP {resp.status_code}", severity="warning")
        name = link_name(name) or page_title(resp.text)
        self.call_from_thread(self.show_page, clean_url(url), name, resp.url, resp.text, push)
        # Seiten mit Baum-Tabelle (Leistungen, VV, ...) zusaetzlich als Tabelle,
        # wenn moeglich einmal "Alle aufklappen" (wie ein Klick im Browser)
        if TREE_TABLE.search(resp.text):
            try:
                tables, tree_html = expand_tree_tables(self.session, resp.url, resp.text,
                                                       self.client.timeout)
            except (HISinOneError, requests.RequestException) as e:
                self.call_from_thread(self.notify, f"Aufklappen fehlgeschlagen: {e}",
                                      severity="warning")
                tables, tree_html = parse_tree_tables(resp.text), resp.text
            if tables:
                self.call_from_thread(self.show_tree_tables, name, resp.url, tables,
                                      tree_html if tree_html is not resp.text else None,
                                      open_col)
        elif open_col:
            self.call_from_thread(self.notify, "Keine Tabelle auf der Seite (abgemeldet?).",
                                  severity="warning")

    def show_tree_tables(self, name: str, url: str, tables: list[dict],
                         expanded_html: str | None, open_col: str = "") -> None:
        if expanded_html and self.save_dir:
            save_html(self.save_dir, url, expanded_html, f"{name}_aufgeklappt")
        screen = TreeTableScreen(name, tables)
        self.push_screen(screen)
        # Taste l: gleich die Leistungsdaten im Vollbild (Esc -> alle Tabellen)
        idx = next((i for i, t in enumerate(tables) if open_col and open_col in t["cols"]), None)
        if idx is not None:
            screen.open_single(idx)

    def open(self, url: str, name: str, push: bool = True, open_col: str = "") -> None:
        self.query_one("#links", Tree).loading = True
        self.fetch(url, name, push, open_col)

    def fetch_failed(self, msg: str) -> None:
        self.query_one("#links", Tree).loading = False
        self.notify(msg, severity="error")

    # -- Anzeige --------------------------------------------------------------

    def show_page(self, stable: str, name: str, server_url: str, html: str, push: bool) -> None:
        if push and self.stable_url:
            self.history.append((self.stable_url, self.cur_name))
        self.stable_url, self.cur_name = stable, name
        self.cur_url, self.cur_html = server_url, html
        self.saved = save_html(self.save_dir, server_url, html, name) if self.save_dir else None
        # Neue Seite -> Filter zuruecksetzen (sonst sieht man ggf. nichts)
        with self.prevent(Input.Changed):
            self.query_one("#filter", Input).value = ""
        self.rebuild()
        tree = self.query_one("#links", Tree)
        tree.loading = False
        # Waehrend des Ladens ist der Baum gesperrt und der Fokus wandert ins
        # Filterfeld - danach zurueck in den Baum, damit Tasten Befehle sind.
        tree.focus()

    def rebuild(self) -> None:
        """Baut Baum/Liste aus der aktuellen Seite neu auf (auch nach Filter/Toggle)."""
        flt = self.query_one("#filter", Input).value.strip().casefold()
        links = extract_links(self.cur_html, self.cur_url, sort=self.sort and not self.tree_mode)
        total = len(links)
        if flt:
            links = [x for x in links if flt in x[0].casefold() or flt in x[1].casefold()]
        rows = (tree_order(links, sort=self.sort) if self.tree_mode
                else [(lab, url, fb, 0) for lab, url, fb in links])

        tree = self.query_one("#links", Tree)
        tree.clear()
        # Tiefe -> Elternknoten: jeder Eintrag haengt am letzten flacheren Knoten
        stack = [(-1, tree.root)]
        for lab, url, fb, depth in rows:
            while stack[-1][0] >= depth:
                stack.pop()
            parent = stack[-1][1]
            if url:
                node = parent.add(self.label(Link(lab, url, fb)), data=Link(lab, url, fb),
                                  expand=True)
            else:
                node = parent.add(Text(lab.lstrip("─ "), style="bold"), expand=True)
            stack.append((depth, node))
        for node in list(tree.root.children):
            self._leafify(node)
        tree.root.expand()

        self.sub_title = self.cur_name
        mode = ("Baum" if self.tree_mode else "Liste") + (", A-Z" if self.sort else "")
        info = Text()
        info.append(page_title(self.cur_html) + "\n\n", style="bold")
        info.append("Stabil: ", style="green")
        info.append(self.stable_url, style=f"link {self.stable_url}")
        info.append("\n")
        if self.cur_url != self.stable_url:
            info.append("Server: ", style="dim")
            info.append(self.cur_url, style=f"link {self.cur_url}")
            info.append("\n")
        info.append(f"\n{total} Links ({mode})")
        if flt:
            info.append(f", {len(links)} passen zu \"{flt}\"")
        info.append("\nSpeichern: ", style="dim")
        info.append(f"an ({self.save_dir})" if self.save_dir else "aus (Taste s)")
        if self.saved:
            info.append("\nGespeichert: ", style="dim")
            info.append(str(self.saved))
        self.query_one("#page", Static).update(info)
        self.query_one("#link", Static).update("")

    def _leafify(self, node) -> None:
        """Knoten ohne Kinder als Blatt darstellen (kein Aufklapp-Pfeil)."""
        if not node.children:
            node.allow_expand = False
        for child in node.children:
            self._leafify(child)

    def label(self, link: Link) -> Text:
        text = Text(link_name(link.label) or link.label)
        p = urlsplit(link.url)
        if p.netloc != self.host:
            text.append(" ext", style="yellow")
        if link.label.startswith("[permalink]"):
            text.append(" ◆", style="cyan")
        if link.flow_bound:
            text.append(" [flow]", style="magenta")
        if "auth.logout" in p.query:
            text.stylize("red")
        return text

    # -- Ereignisse -----------------------------------------------------------

    @on(Tree.NodeSelected, "#links")
    def node_selected(self, event: Tree.NodeSelected) -> None:
        link: Link | None = event.node.data
        if link is None:
            event.node.toggle()  # Gruppen-Ueberschrift
        elif link.needs_confirm:
            self.notify("Keine stabile URL bzw. Abmelden - mit ! trotzdem oeffnen.",
                        severity="warning")
        else:
            self.open(link.url, link.label)

    @on(Tree.NodeHighlighted, "#links")
    def node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        link: Link | None = event.node.data
        out = Text()
        if link:
            p = urlsplit(link.url)
            out.append("\n\nMarkierter Link\n", style="bold")
            out.append(link_name(link.label) + "\n")
            out.append(link.url if p.netloc != self.host
                       else urlunsplit(("", "", p.path, p.query, "")),
                       style=f"dim link {link.url}")
        self.query_one("#link", Static).update(out)

    @on(Input.Changed, "#filter")
    def filter_changed(self) -> None:
        if self.cur_html:
            self.rebuild()

    @on(Input.Submitted, "#filter")
    def filter_submitted(self) -> None:
        self.action_focus_tree()

    # -- Aktionen -------------------------------------------------------------

    def action_back(self) -> None:
        if self.history:
            url, name = self.history.pop()
            self.open(url, name, push=False)
        else:
            self.notify("Kein Verlauf.")

    def action_reload(self) -> None:
        if self.stable_url:
            self.open(self.stable_url, self.cur_name, push=False)

    def action_home(self) -> None:
        if self.home_url:
            self.open(self.home_url, "Startseite")

    def action_force_open(self) -> None:
        node = self.query_one("#links", Tree).cursor_node
        if node and node.data:
            self.open(node.data.url, node.data.label)

    def current_url(self) -> str:
        """URL des markierten Links, sonst die stabile URL der Seite."""
        node = self.query_one("#links", Tree).cursor_node
        return node.data.url if node and node.data else self.stable_url

    def action_copy_url(self) -> None:
        url = self.current_url()
        if not url:
            return
        # Externes Tool (wl-copy/xclip) bevorzugt, sonst OSC 52 ueber das Terminal
        tool = copy_external(url)
        if not tool:
            self.copy_to_clipboard(url)
            tool = "OSC 52"
        self.notify(f"Kopiert ({tool}): {url}")

    def action_browser(self) -> None:
        if url := self.current_url():
            self.open_url(url)

    def action_toggle_save(self) -> None:
        if self.save_dir:
            self.save_dir, self.saved = None, None
            self.notify("Speichern aus")
        else:
            try:
                self.save_dir = prepare_save_dir(self.save_path)
            except OSError as e:
                self.notify(f"Ordner nicht anlegbar: {e}", severity="error")
                return
            # aktuelle Seite gleich mitspeichern
            if self.cur_html:
                self.saved = save_html(self.save_dir, self.cur_url, self.cur_html, self.cur_name)
            self.notify(f"Speichern an: {self.save_dir}")
        self.rebuild()

    def action_toggle_tree(self) -> None:
        self.tree_mode = not self.tree_mode
        self.rebuild()

    def action_toggle_sort(self) -> None:
        self.sort = not self.sort
        self.rebuild()

    def action_focus_filter(self) -> None:
        inp = self.query_one("#filter", Input)
        if self.focused is inp:
            inp.insert_text_at_cursor("/")  # im Filterfeld ist "/" normaler Text
        else:
            inp.focus()

    def action_focus_tree(self) -> None:
        self.query_one("#links", Tree).focus()


def main() -> int:
    ap = argparse.ArgumentParser(description="HISinOne als Terminal-Oberflaeche erkunden.")
    # Optionen ueberschreiben die Config nur, wenn sie angegeben sind
    ap.add_argument("--flat", dest="tree", action="store_const", const=False,
                    help="flache Liste statt Baum (Taste t)")
    ap.add_argument("--sort", action="store_const", const=True, help="alphabetisch (Taste a)")
    ap.add_argument("--save", nargs="?", const="", metavar="DIR",
                    help="Jede besuchte Seite als HTML speichern "
                         "(Standard-Ordner: aus Config, sonst /tmp/hisinone-explore; "
                         "Taste s schaltet um)")
    ap.add_argument("--no-config", action="store_true",
                    help=f"{CONFIG_PATH} weder lesen noch schreiben")
    args = ap.parse_args()
    cfg = {} if args.no_config else load_config()
    TABLE_PREFS.update(cfg.get("tables", {}))
    app = ExploreApp(
        tree=cfg.get("tree", True) if args.tree is None else args.tree,
        sort=cfg.get("sort", False) if args.sort is None else args.sort,
        save_path=args.save or cfg.get("save_path", "/tmp/hisinone-explore"),
        save_on=args.save is not None or cfg.get("save_on", False))
    app.shortcuts = cfg.get("shortcuts", DEFAULT_SHORTCUTS)
    app.shortcuts_from_file = "shortcuts" in cfg
    if args.no_config:
        app.save_config = lambda: None
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
