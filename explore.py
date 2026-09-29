#!/usr/bin/env python3
"""
Interaktiver HISinOne-Explorer: einloggen, alle Links einer Seite
auflisten (Seitenreihenfolge oder alphabetisch), per Nummer einem Link folgen.

Der ``_flowExecutionKey`` (z. B. ``e4s1``) ist nur fuer den gerade laufenden
Flow gueltig. Aus Links mit ``_flowId`` wird er entfernt - die starten den
Flow damit einfach neu. Links ohne ``_flowId`` gehoeren zu einem laufenden
Flow, behalten ihren Key und werden mit ``[flow]`` markiert. Sie werden nur
mit ``!<Nr>`` geoeffnet, da sie keine stabile URL haben.

Oben steht je Seite die stabile URL (ohne Key); "Server:" zeigt die URL,
auf die HISinOne tatsaechlich umgeleitet hat. "b" und "r" nutzen immer die
stabile URL.

Benutzung (aus dem Projekt-Hauptordner, .env wie bei login_test.py):
    python explore.py           # Links in Seitenreihenfolge
    python explore.py --sort    # Links alphabetisch
    python explore.py --save    # jede besuchte Seite nach /tmp/hisinone-explore/
                                # als <Linkname>_<JJJJ-MM-TT_hh-mm-ss>.html
    python explore.py --save DIR    # ... oder in einen eigenen Ordner
    python explore.py --tree    # Links als Baum

Baumansicht: Die Hierarchie steckt in den URLs selbst - Navigation in
``navigationPosition=a,b,c``, Vorlesungsverzeichnis-Permalinks in
``path=title:36|title:37|...``. Links ohne beides stehen unter "Sonstige".

URLs werden als OSC-8-Terminal-Links ausgegeben: Strg+Klick oeffnet die
volle URL, auch wenn die Zeile umbricht (tmux braucht dafuer
``set -ga terminal-features "*:hyperlinks"``).

Zwischen Schritten, die im Browser ein Klick waeren, wartet das Skript
zufaellig 200-1000 ms (Pacer), damit der Server nicht in Serie getroffen wird.

Befehle:
    <Nr>        Link oeffnen
    !<Nr>       flow-gebundenen Link trotzdem oeffnen
    a           alphabetisch / Seitenreihenfolge umschalten
    t           Baumansicht an/aus
    b           zurueck
    r           Seite neu laden
    h           Startseite
    c [Nr]      URL der Seite (bzw. von Link Nr) in die Zwischenablage
    l           Leistungen komplett aufgeklappt als Tabelle (2 Requests)
    /text       Liste filtern (nur "/" = Filter aus)
    u <url>     beliebige URL/Pfad oeffnen (z. B. u /qisserver/pages/...)
    s <datei>   HTML der aktuellen Seite speichern (persoenliche Daten!)
    q           beenden
"""

import argparse
import base64
import html as htmlmod
import random
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests

from hisinone_noten import HISinOneClient, HISinOneError

SKIP_EXT = (".css", ".js", ".ico", ".png", ".gif", ".jpg", ".jpeg", ".svg", ".woff", ".woff2")
DROP_PARAMS = {"_flowExecutionKey"}


class Pacer:
    """Kurze Zufallspause (200-1000 ms) zwischen Schritten, fuer die ein Mensch
    im Browser klicken muesste (Seite -> Button -> naechste Seite ...).
    Requests innerhalb eines Seitenaufrufs (Redirects) werden nicht gebremst;
    liegt der letzte Schritt schon laenger zurueck, wird nicht gewartet."""

    def __init__(self, low: float = 0.2, high: float = 1.0):
        self.low, self.high = low, high
        self._last = 0.0
        self._lock = threading.Lock()

    def step(self) -> None:
        """Vor jedem "Klick" aufrufen."""
        with self._lock:
            wait = self._last + random.uniform(self.low, self.high) - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()


pacer = Pacer()


def login(c: HISinOneClient) -> tuple[requests.Session, requests.Response]:
    s = c._new_session()
    pacer.step()
    start = s.get(f"{c.qis_base}/pages/cs/sys/portal/hisinoneStartPage.faces",
                  timeout=c.timeout)
    pacer.step()  # Login-Formular absenden
    r = s.post(f"{c.qis_base}/rds?state=user&type=1&category=auth.login",
               data={"userInfo": "", "ajax-token": c._find_ajax_token(start.text),
                     "asdf": c.username, "fdsa": c.password, "submit": ""},
               headers={"Origin": c.base_url, "Referer": start.url},
               timeout=c.timeout)
    if "abmelden" not in r.text.lower():
        raise HISinOneError("Login fehlgeschlagen.")
    return s, r


def clean_url(url: str) -> str:
    """Entfernt fluechtige Parameter (_flowExecutionKey) und den Standard-Port
    (Permalinks enthalten z. B. ``campus.example.org:443``) aus der URL."""
    p = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in DROP_PARAMS]
    netloc = p.netloc.removesuffix(":443") if p.scheme == "https" else p.netloc
    return urlunsplit((p.scheme, netloc, p.path, urlencode(q), ""))


def _text(fragment: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def _attr(tag: str, name: str) -> str:
    m = re.search(rf'\b{name}="([^"]*)"', tag)
    return htmlmod.unescape(m.group(1)) if m else ""


def extract_links(html: str, base: str, sort: bool = False) -> list[tuple[str, str, bool]]:
    """Liefert [(beschriftung, url, flow_gebunden)], dedupliziert, in
    Seitenreihenfolge (oder alphabetisch mit sort=True). flow_gebunden = Link
    hatte einen _flowExecutionKey, aber keine _flowId (nicht neu startbar)."""
    found: dict[str, tuple[str, bool]] = {}

    def add(label: str, href: str) -> None:
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return
        raw = urljoin(base, href)
        query = urlsplit(raw).query
        flow_bound = "_flowExecutionKey=" in query and "_flowId=" not in query
        # Flow-gebundene Links brauchen den aktuellen Key, alle anderen nicht
        url = urlunsplit(urlsplit(raw)._replace(fragment="")) if flow_bound else clean_url(raw)
        if urlsplit(url).path.lower().endswith(SKIP_EXT):
            return
        label = label or urlsplit(url).path.rsplit("/", 1)[-1] or url
        # Bei Doubletten die laengere (aussagekraeftigere) Beschriftung behalten
        if len(label) > len(found.get(url, ("", False))[0]):
            found[url] = (label, flow_bound)

    # <a>, <iframe>, Permalinks und Baum-Namen gemeinsam durchlaufen, damit die
    # Seitenreihenfolge stimmt. Permalinks stehen als verstecktes
    # <input value="...startFlow.xhtml?_flowId=...">; ihr Name steht im
    # vorangehenden "treeElementName" (z. B. im Vorlesungsverzeichnis).
    tree_name = ""
    pattern = (r"(<a\b[^>]*>)(.*?)</a>"
               r"|<iframe\b[^>]*>"
               r'|class="treeElementName"(.*?)</td>'
               r'|<input\b[^>]*\bvalue="[^"]*_flowId=[^"]*"[^>]*>')
    for m in re.finditer(pattern, html, re.S | re.I):
        tag = m.group(0)
        if m.group(1):
            add(_text(m.group(2)) or _attr(m.group(1), "title") or _attr(m.group(1), "aria-label"),
                _attr(m.group(1), "href"))
        elif tag.lower().startswith("<iframe"):
            add("[iframe] " + _attr(tag, "title"), _attr(tag, "src"))
        elif m.group(3) is not None:
            tree_name = _text("<x " + m.group(3))
        else:
            add(f"[permalink] {tree_name}".strip(), _attr(tag, "value"))

    links = [(lab, url, fb) for url, (lab, fb) in found.items()]
    if sort:
        links.sort(key=lambda x: (x[0].casefold(), x[1]))
    return links


def tree_key(url: str) -> tuple[str, ...] | None:
    """Position eines Links in der Hierarchie, direkt aus der URL:
    Navigation: navigationPosition=a,b,c   Vorlesungsverzeichnis: path=x|y|z"""
    q = dict(parse_qsl(urlsplit(url).query))
    if q.get("path"):
        return ("Vorlesungsverzeichnis",) + tuple(q["path"].split("|"))
    nav = q.get("navigationPosition", "")
    if "," in nav or (nav and not nav.startswith(("link_", "switchTo"))):
        return ("Navigation",) + tuple(nav.split(","))
    return None


def tree_order(links, sort: bool = False) -> list[tuple[str, str, bool, int]]:
    """Ordnet die Links als Baum: [(beschriftung, url, flow_gebunden, tiefe)].
    Geschwister bleiben in Seitenreihenfolge (alphabetisch mit sort=True);
    Links ohne Hierarchie-Info landen unter "Sonstige"."""
    keyed: dict[tuple, list] = {}
    other = []
    for link in links:
        k = tree_key(link[1])
        if k is None:
            other.append(link)
        else:
            keyed.setdefault(k, []).append(link)

    children: dict[tuple, list[tuple]] = {}
    for k in keyed:
        # naechsten vorhandenen Vorfahren suchen (Zwischenebenen koennen fehlen)
        parent = k[:-1]
        while len(parent) > 1 and parent not in keyed:
            parent = parent[:-1]
        children.setdefault(parent, []).append(k)
    if sort:
        for kids in children.values():
            kids.sort(key=lambda k: keyed[k][0][0].casefold())

    out: list[tuple[str, str, bool, int]] = []

    def walk(parent: tuple, depth: int) -> None:
        for k in children.get(parent, []):
            for lab, url, fb in keyed[k]:
                out.append((lab, url, fb, depth))
            walk(k, depth + 1)

    for root in dict.fromkeys(k[0] for k in keyed):
        out.append((f"── {root}", "", False, 0))
        walk((root,), 1)
    if other:
        out.append(("── Sonstige", "", False, 0))
        for lab, url, fb in (sorted(other, key=lambda x: x[0].casefold()) if sort else other):
            out.append((lab, url, fb, 1))
    return out


def link_name(label: str) -> str:
    """Linkname ohne Markierungen und Screenreader-Zusaetze."""
    label = re.sub(r"^\[(permalink|iframe)\]\s*", "", label)
    label = label.replace("Sie befinden sich hier:", "").replace("Zur nächsten Navigationsebene", "")
    return label.strip()


def page_title(html: str) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    return _text(m.group(1)) if m else ""


def hyperlink(text: str, url: str) -> str:
    """OSC-8-Terminal-Link: der Text ist klickbar und traegt die volle URL,
    egal wie das Terminal umbricht (tmux: terminal-features "*:hyperlinks")."""
    if not sys.stdout.isatty():
        return text
    return f"\033]8;;{url}\033\\{text}\033]8;;\033\\"


def copy_external(text: str) -> str | None:
    """Kopiert per wl-copy/xclip/xsel; liefert den Tool-Namen oder None."""
    for cmd in (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-bi"]):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode(), check=True, timeout=5)
                return cmd[0]
            except (OSError, subprocess.SubprocessError):
                pass
    return None


def copy_to_clipboard(text: str) -> str:
    """Kopiert in die Zwischenablage; ohne Tool per OSC 52 ueber das Terminal
    (tmux: set -g set-clipboard on)."""
    tool = copy_external(text)
    if tool:
        return tool
    sys.stdout.write(f"\033]52;c;{base64.b64encode(text.encode()).decode()}\a")
    sys.stdout.flush()
    return "OSC 52"


def show(links, host: str, flt: str) -> None:
    """links: [(beschriftung, url, flow_gebunden)] oder mit Tiefe als 4. Wert
    (Baumansicht). Eintraege ohne URL sind Gruppen-Ueberschriften."""
    for i, (label, url, flow_bound, *rest) in enumerate(links, 1):
        indent = "  " * (rest[0] if rest else 0)
        if not url:
            if not flt:
                print(f"\n      {label}")
            continue
        if flt and flt not in label.casefold() and flt not in url.casefold():
            continue
        label = indent + label
        p = urlsplit(url)
        marks = ""
        if p.netloc != host:
            marks += "[ext] "
        elif flow_bound:
            marks += "[flow] "
        if "auth.logout" in p.query:
            marks += "[LOGOUT] "
        short = url if p.netloc != host else urlunsplit(("", "", p.path, p.query, ""))
        print(f"{i:4}  {marks}{label[:60]:60}  {hyperlink(short, url)}")


def prepare_save_dir(path: str) -> Path:
    """Legt den Speicherordner an. Seiten enthalten persoenliche Daten ->
    Ordner nur fuer den eigenen User lesbar."""
    d = Path(path)
    d.mkdir(mode=0o700, parents=True, exist_ok=True)
    d.chmod(0o700)
    return d


def save_html(save_dir: Path, url: str, html: str, name: str) -> Path:
    """Speichert als <angeklickter Linkname>_<Datum>.html und liefert den Pfad."""
    name = re.sub(r"[^\w.-]+", "_", link_name(name) or page_title(html) or "seite")
    base = f"{name.strip('_')[:80]}_{time.strftime('%Y-%m-%d_%H-%M-%S')}"
    path = save_dir / f"{base}.html"
    n = 2
    while path.exists():  # mehrere Seiten in derselben Sekunde
        path = save_dir / f"{base}_{n}.html"
        n += 1
    path.write_text(f"<!-- {url} -->\n{html}", encoding="utf-8")
    return path


# -- Leistungen (Mein Studium > Leistungen) ------------------------------------
#
# Die Seite ist JSF: die Tabelle ist ein Baum, der nur ueber Buttons
# (jsf.ajax POST) aufklappt. Ablauf = 2 Requests: Seite laden (neuer Flow),
# dann einmal "Alle aufklappen" wie im Browser.

LEISTUNGEN_PATH = ("/pages/sul/examAssessment/personExamsReadonly.xhtml"
                   "?_flowId=examsOverviewForPerson-flow"
                   "&navigationPosition=hisinoneMeinStudium,examAssessmentForStudent")
LEISTUNGEN_FORM = "examsReadonly"
EXPAND_ALL = "examsReadonly:overviewAsTreeReadonly:tree:expandAll2"
LEISTUNGEN_COLS = ["Freigabedatum", "Nummer", "Versuch", "Rücktritt", "Bewertung", "Bonus",
                   "Malus", "Status", "Freiversuch", "Vermerk", "Vorbehalt", "Zusatzmerkmal",
                   "Aktionen"]


def _form(html: str, form_id: str) -> tuple[str, str]:
    """(action, inneres HTML) des Formulars mit dieser id."""
    m = re.search(rf'<form\b[^>]*\bid="{re.escape(form_id)}"[^>]*>(.*?)</form>', html, re.S)
    if not m:
        raise HISinOneError(f"Formular {form_id} nicht gefunden.")
    return _attr(m.group(0)[:m.group(0).find(">") + 1], "action"), m.group(1)


def _hidden_fields(form_html: str) -> dict[str, str]:
    fields = {}
    for tag in re.findall(r'<input\b[^>]*type="hidden"[^>]*>', form_html):
        if name := _attr(tag, "name"):
            fields.setdefault(name, _attr(tag, "value"))
    return fields


def jsf_click(s: requests.Session, page_url: str, html: str, form_id: str,
              button_id: str, timeout: int) -> str:
    """Klickt einen JSF-Ajax-Button wie jsf.ajax.request im Browser und liefert
    das HTML aller aktualisierten Bereiche (partial-response)."""
    action, form_html = _form(html, form_id)
    btn = re.search(rf'<button\b[^>]*\bid="{re.escape(button_id)}"[^>]*>', form_html)
    if not btn:
        raise HISinOneError(f"Button {button_id} nicht gefunden.")
    onclick = htmlmod.unescape(_attr(btn.group(0), "onclick"))
    render = re.search(r"render:\\?'([^'\\]*)", onclick)
    data = _hidden_fields(form_html)
    data.update({
        button_id: _attr(btn.group(0), "value"),
        "javax.faces.source": button_id,
        "javax.faces.partial.event": "click",
        "javax.faces.partial.execute": button_id,
        "javax.faces.partial.render": (render.group(1) if render else "@form").replace(
            "@this", button_id).strip(),
        "javax.faces.behavior.event": "action",
        "javax.faces.partial.ajax": "true",
    })
    pacer.step()
    r = s.post(urljoin(page_url, action), data=data, timeout=timeout,
               headers={"Faces-Request": "partial/ajax", "X-Requested-With": "XMLHttpRequest",
                        "Referer": page_url})
    r.encoding = "utf-8"
    parts = re.findall(r"<update\b[^>]*><!\[CDATA\[(.*?)\]\]></update>", r.text, re.S)
    if not parts:
        raise HISinOneError(f"Unerwartete Antwort auf {button_id} (HTTP {r.status_code}).")
    return "\n".join(parts)


def parse_leistungen(html: str) -> list[dict]:
    """Zeilen des Leistungs-Baums: [{ebene, tiefe, typ, titel, art, <Spalten>}].
    Nutzt parse_tree_tables (die Tabelle mit Spalte "Versuch"; der
    Studienverlauf-Baum auf derselben Seite wird uebergangen)."""
    table = next((t for t in parse_tree_tables(html) if "Versuch" in t["cols"]), None)
    if not table:
        return []
    out = []
    for r in table["rows"]:
        row = {"ebene": r.get("Ebene", ""), "tiefe": r["tiefe"] + 1, "typ": r["typ"],
               "titel": r.get("Titel", "")}
        row.update({c: r.get(c, "") for c in LEISTUNGEN_COLS})
        row["art"] = exam_kind(row)
        out.append(row)
    return out


def fetch_leistungen(s: requests.Session, c: HISinOneClient) -> tuple[list[dict], str]:
    """Laedt die Leistungen komplett aufgeklappt (2 Requests).
    Liefert (Zeilen, HTML des aufgeklappten Baums)."""
    pacer.step()
    page = s.get(c.qis_base + LEISTUNGEN_PATH, timeout=c.timeout)
    page.encoding = "utf-8"
    if f'id="{LEISTUNGEN_FORM}"' not in page.text:
        raise HISinOneError("Leistungen-Seite nicht erkannt (abgemeldet?).")
    tree_html = page.text
    if f'id="{EXPAND_ALL}"' in page.text:
        tree_html = jsf_click(s, page.url, page.text, LEISTUNGEN_FORM, EXPAND_ALL, c.timeout)
        # Kopfzeile steckt ggf. nur in der ganzen Seite
        if 'class="treeTableWithIcons"' not in tree_html:
            hm = re.search(r'class="treeTableWithIcons".*?</tr>', page.text, re.S)
            tree_html = (f"<table {hm.group(0)}" if hm else "") + tree_html
    return parse_leistungen(tree_html), tree_html


# -- Allgemeine Baum-Tabellen (treeTableWithIcons) ------------------------------
#
# Leistungen, Vorlesungsverzeichnis usw. nutzen dasselbe Markup. Spalten werden
# ueber colspan den Kopfzeilen zugeordnet (der Titel-Kopf ueberspannt z.B. auch
# die Auf-/Zuklapp-Symbole). "Alle aufklappen" wird nur geklickt, wenn es einen
# einzigen globalen Button gibt (nicht die vielen pro Knoten im VV).

TREE_TABLE = re.compile(r'<table\b[^>]*class="[^"]*\btreeTableWithIcons\b[^"]*"[^>]*>')
EXPAND_ALL_BTN = re.compile(r'<button\b[^>]*\bid="([^"]*:expandAll\d*)"')


def _colspan(tag: str) -> int:
    return int(_attr(tag, "colspan") or 1) if (_attr(tag, "colspan") or "1").isdigit() else 1


def parse_tree_tables(html: str) -> list[dict]:
    """Alle Baum-Tabellen:
    [{"name": Ueberschrift, "cols": [Kopf...], "rows": [{"tiefe", "typ", Kopf: Text}]}]."""
    starts = [m.start() for m in TREE_TABLE.finditer(html)]
    tables = []
    for i, start in enumerate(starts):
        seg = html[start:starts[i + 1] if i + 1 < len(starts) else len(html)]
        # Name = letzte Ueberschrift/Legende vor der Tabelle (nach der vorigen)
        before = html[starts[i - 1] if i else 0:start]
        heads_before = re.findall(r"<(h[1-6]|legend|caption)\b[^>]*>(.*?)</\1>", before, re.S)
        name = _text(heads_before[-1][1]) if heads_before else ""
        # Kopf: Positionen der Spalten (mit colspan)
        heads, pos = [], 0
        hm = re.search(r"<tr\b[^>]*>(.*?)</tr>", seg, re.S)
        for tag, inner in re.findall(r"(<th\b[^>]*>)(.*?)</th>", hm.group(1) if hm else "", re.S):
            heads.append((pos, pos + _colspan(tag), _text(inner) or f"Spalte {len(heads) + 1}"))
            pos += _colspan(tag)
        rows = []
        for m in re.finditer(r'<tr\b[^>]*class="treeTableCellLevel(\d+)[^"]*"[^>]*>(.*?)</tr>',
                             seg, re.S):
            row, pos = {"tiefe": int(m.group(1)), "typ": ""}, 0
            for tag, inner in re.findall(r"(<td\b[^>]*>)(.*?)</td>", m.group(2), re.S):
                col = next((h for a, b, h in heads if a <= pos < b), None)
                pos += _colspan(tag)
                if not row["typ"]:
                    img = re.search(r'<img\b[^>]*\balt="([^"]+)"', inner)
                    row["typ"] = img.group(1) if img else ""
                if col and (t := _text(inner)):
                    row[col] = f"{row[col]} {t}" if row.get(col) else t
            rows.append(row)
        if rows:
            base = min(r["tiefe"] for r in rows)
            for r in rows:
                r["tiefe"] -= base
            table = {"name": name, "cols": [h for _, _, h in heads], "rows": rows}
            add_custom_columns(table)
            tables.append(table)
    return tables


# Eigene (berechnete) Spalten, die es auf der Seite nicht gibt:
# (Name, gilt fuer Tabellen mit diesen Original-Spalten, Wert je Zeile).
# Sie stehen in table["custom"] und werden nur auf Wunsch angezeigt.
CUSTOM_COLUMNS = [
    # alle Baum-Tabellen: Typ aus dem Symbol im Titel (Modul, Pruefung, Konto, ...)
    ("Typ", set(), lambda r: r.get("typ", "")),
    # Leistungen: PL/PVL (Regeln siehe exam_kind)
    ("Art", {"Titel", "Versuch", "Bewertung", "Freiversuch"},
     lambda r: exam_kind({"titel": r.get("Titel", ""), "typ": r.get("typ", ""),
                          "Bewertung": r.get("Bewertung", "")})),
]


NAV_COLS = {"Ebene", "Aktionen", ""}


def is_data_table(table: dict) -> bool:
    """False fuer reine Navigations-Baeume (z.B. Vorlesungsverzeichnis: nur
    Ebene, Titel, Aktionen) - die bleiben in der Link-Ansicht."""
    return len([c for c in table["cols"] if c not in NAV_COLS]) > 1


def add_custom_columns(table: dict) -> None:
    """Berechnet die passenden eigenen Spalten in die Zeilen; Namen in table["custom"]."""
    table["custom"] = []
    for name, needs, value in CUSTOM_COLUMNS:
        if needs <= set(table["cols"]) and name not in table["cols"]:
            values = [value(r) for r in table["rows"]]
            if not any(values):  # nichts zu zeigen -> Spalte gar nicht anbieten
                continue
            for r, v in zip(table["rows"], values):
                r[name] = v
            table["custom"].append(name)


def can_expand_all(html: str) -> bool:
    """Genau ein "Alle aufklappen" (VV hat je Knoten einen -> nicht klicken)."""
    return len(set(EXPAND_ALL_BTN.findall(html))) == 1


def expand_tree_tables(s: requests.Session, page_url: str, html: str,
                       timeout: int, expand: bool = True) -> tuple[list[dict], str]:
    """Baum-Tabellen der Seite, falls moeglich (und expand) per "Alle
    aufklappen" (1 Request). Liefert (Tabellen, HTML das angezeigt wurde -
    Seite oder Fragment)."""
    tables = parse_tree_tables(html)
    btns = set(EXPAND_ALL_BTN.findall(html))
    if not tables or not expand or len(btns) != 1:
        return tables, html
    btn = btns.pop()
    form = next((f for f in re.findall(r'<form\b[^>]*\bid="([^"]*)"', html)
                 if btn.startswith(f + ":")), None)
    if not form:
        return tables, html
    frag = jsf_click(s, page_url, html, form, btn, timeout)
    if not TREE_TABLE.search(frag):
        # Kopfzeile steckt nur in der ganzen Seite
        hm = re.search(TREE_TABLE.pattern + r".*?</tr>", html, re.S)
        frag = (hm.group(0) if hm else "") + frag
    expanded = parse_tree_tables(frag)
    # Fragment hat keine Ueberschriften -> Namen von der passenden Seiten-Tabelle
    for e in expanded:
        e["name"] = e["name"] or next((t["name"] for t in tables if t["cols"] == e["cols"]), "")
    # Nicht aufgeklappte weitere Baeume der Seite behalten
    rest = [t for t in tables if all(t["cols"] != e["cols"] for e in expanded)]
    return expanded + rest, frag


# Spalten: (Schluessel in den Zeilen, Anzeigename). "art" = PL/PVL (berechnet)
COLUMNS = [("ebene", "Ebene"), ("typ", "Typ"), ("art", "Art"), ("titel", "Titel"),
           ("Nummer", "Nummer"), ("Versuch", "Versuch"), ("Bewertung", "Note"),
           ("Bonus", "CP"), ("Malus", "Malus"), ("Status", "Status"),
           ("Freigabedatum", "Freigabe"), ("Rücktritt", "Rücktritt"),
           ("Freiversuch", "Freiversuch"), ("Vermerk", "Vermerk"),
           ("Vorbehalt", "Vorbehalt"), ("Zusatzmerkmal", "Zusatzmerkmal")]
DEFAULT_COLS = ["titel", "art", "Nummer", "Versuch", "Bewertung", "Bonus", "Status",
                "Freigabedatum"]
COL_LABEL = dict(COLUMNS)


def parse_cols(spec: str) -> list[str]:
    """"titel,Note,CP" -> Schluessel; akzeptiert Schluessel oder Anzeigenamen."""
    lookup = {k.casefold(): k for k, _ in COLUMNS} | {v.casefold(): k for k, v in COLUMNS}
    cols = []
    for part in filter(None, (p.strip() for p in spec.split(","))):
        if part.casefold() not in lookup:
            raise ValueError(f"Unbekannte Spalte {part!r} (moeglich: "
                             + ", ".join(v for _, v in COLUMNS) + ")")
        cols.append(lookup[part.casefold()])
    return cols


def exam_kind(row: dict) -> str:
    """"PL"/"PVL" laut Titel-Endung; sonst "PL", wenn eine Note (Zahl) drin
    steht - ausser bei Modul/Konto (die tragen nur zusammengefasste Noten)."""
    m = re.search(r"\((PVL|PL)\)\s*$", row["titel"])
    if m:
        return m.group(1)
    if (re.fullmatch(r"\d+(?:[.,]\d+)?", row.get("Bewertung", ""))
            and row["typ"] not in ("Modul", "Konto")):
        return "PL"
    return ""


def filter_leistungen(rows: list[dict], exams_only: bool = False,
                      latest_only: bool = False) -> list[dict]:
    """exams_only: nur PL/PVL. latest_only: fruehere Versuche ausblenden -
    Versuche sind Geschwister im Baum (gleicher Elternknoten, gleiche Art);
    je Gruppe bleibt der hoechste Versuch. Kommt eine Versuchsnummer doppelt
    vor, sind es verschiedene Pruefungen -> Gruppe bleibt komplett."""
    rows = [r | {"art": r.get("art") or exam_kind(r)} for r in rows]
    drop = earlier_attempts([(r["ebene"], r["art"], r.get("Versuch", "")) for r in rows]) \
        if latest_only else set()
    return [r for i, r in enumerate(rows)
            if i not in drop and (not exams_only or r["art"])]


def earlier_attempts(items: list[tuple[str, str, str]]) -> set[int]:
    """Indizes frueherer Versuche; items = [(Ebene, Art, Versuch)] je Zeile.
    Regeln siehe filter_leistungen (nur Zeilen mit Art zaehlen)."""
    groups: dict[tuple, list[int]] = {}
    for i, (ebene, art, _) in enumerate(items):
        if art:
            groups.setdefault((ebene.rsplit(".", 1)[0], art), []).append(i)
    drop: set[int] = set()
    for idx in groups.values():
        tries = [int(items[i][2]) if items[i][2].isdigit() else 0 for i in idx]
        if len(idx) > 1 and len(set(tries)) == len(tries):
            best = idx[tries.index(max(tries))]
            drop.update(i for i in idx if i != best)
    return drop


def latest_attempts_tree(rows: list[dict]) -> list[dict]:
    """Wie filter_leistungen(latest_only=True) fuer Zeilen aus parse_tree_tables
    (Spalten Ebene/Art/Versuch)."""
    drop = earlier_attempts([(r.get("Ebene", ""), r.get("Art", ""), r.get("Versuch", ""))
                             for r in rows])
    return [r for i, r in enumerate(rows) if i not in drop]


def _terms(query: str) -> list[str]:
    try:
        return shlex.split(query)
    except ValueError:  # offenes Anfuehrungszeichen beim Tippen
        return query.replace('"', " ").split()


def match_rows(rows: list[dict], cols: list[str], query: str) -> list[dict]:
    """Zeilenfilter: Begriffe mit Leerzeichen getrennt, alle muessen passen
    (Gross-/Kleinschreibung egal). "Spalte=Wert" sucht nur in dieser Spalte,
    sonst in allen. Werte mit Leerzeichen in Anfuehrungszeichen."""
    by_name = {c.lower(): c for c in cols}
    checks = []
    for term in _terms(query):
        col, sep, val = term.partition("=")
        if sep and col.lower() in by_name:
            checks.append(([by_name[col.lower()]], val.lower()))
        else:
            checks.append((cols, term.lower()))
    return [r for r in rows
            if all(any(v in str(r.get(c, "")).lower() for c in cs) for cs, v in checks)]


def filter_suggestions(rows: list[dict], cols: list[str], max_values: int = 40) -> list[str]:
    """Vorschlaege "Spalte=Wert" fuer Spalten mit wenigen verschiedenen Werten."""
    out = []
    for c in cols:
        vals = sorted({str(r.get(c, "")) for r in rows} - {""})
        if 1 < len(vals) <= max_values:
            out += [f"{c}={shlex.quote(v) if ' ' in v else v}" for v in vals]
    return out


def export_leistungen(rows: list[dict], path: str | Path, cols: list[str]) -> Path:
    """Schreibt .json oder .csv (Endung entscheidet); Spaltennamen wie angezeigt."""
    import csv
    import json
    path = Path(path)
    # Leistungen-Schluessel -> Anzeigename; Baum-Tabellen haben schon Namen
    label = lambda c: COL_LABEL.get(c, c)  # noqa: E731
    data = [{label(c): str(r.get(c, "")) for c in cols} for r in rows]
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif path.suffix.lower() == ".csv":
        # ";" + BOM: oeffnet in deutschem Excel/LibreOffice direkt richtig
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=[label(c) for c in cols], delimiter=";")
            w.writeheader()
            w.writerows(data)
    else:
        raise ValueError("Dateiendung .json oder .csv verwenden.")
    return path


def print_leistungen(rows: list[dict], cols: list[str] | None = None,
                     tree: bool = True) -> None:
    cols = cols or DEFAULT_COLS
    cells = [[("  " * (r["tiefe"] - 1) if tree and c == "titel" else "") + str(r.get(c, ""))
              for c in cols] for r in rows]
    widths = [min(60, max([len(COL_LABEL[c])] + [len(x[i]) for x in cells]))
              for i, c in enumerate(cols)]
    print("  ".join(f"{COL_LABEL[c]:{w}}" for c, w in zip(cols, widths)))
    for x in cells:
        print("  ".join(f"{v[:w]:{w}}" for v, w in zip(x, widths)))


def main() -> int:
    ap = argparse.ArgumentParser(description="HISinOne interaktiv erkunden.")
    ap.add_argument("--sort", action="store_true",
                    help="Links alphabetisch statt in Seitenreihenfolge (Befehl: a)")
    ap.add_argument("--save", nargs="?", const="/tmp/hisinone-explore", metavar="DIR",
                    help="Jede besuchte Seite als HTML speichern "
                         "(Standard-Ordner: /tmp/hisinone-explore)")
    ap.add_argument("--tree", action="store_true",
                    help="Links als Baum (Navigation / Vorlesungsverzeichnis) (Befehl: t)")
    args = ap.parse_args()

    save_dir = prepare_save_dir(args.save) if args.save else None

    def save_page(url: str, html: str, name: str) -> None:
        if save_dir:
            print(f"[gespeichert: {save_html(save_dir, url, html, name)}]")

    try:
        c = HISinOneClient.from_env()
        s, r = login(c)
    except HISinOneError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1

    home_url = clean_url(r.url)
    host = urlsplit(home_url).netloc
    # history/stable_url enthalten nur stabile URLs (ohne _flowExecutionKey),
    # damit "b" und "r" nie einen veralteten Flow-Key wiederverwenden.
    # history: [(stabile URL, Name)] - der Name ist der angeklickte Linkname
    history: list[tuple[str, str]] = []
    stable_url, cur_name = home_url, "Startseite"
    cur_url, cur_html = r.url, r.text  # cur_url = tatsaechliche Server-URL
    flt = ""
    sort = args.sort
    tree = args.tree
    save_page(cur_url, cur_html, cur_name)

    def open_url(url: str, name: str = "") -> bool:
        nonlocal cur_url, cur_html, stable_url, cur_name
        pacer.step()
        try:
            resp = s.get(url, timeout=c.timeout, headers={"Referer": cur_url})
        except requests.RequestException as e:
            print(f"Fehler: {e}")
            return False
        resp.encoding = resp.encoding or "utf-8"
        if "text/html" not in resp.headers.get("Content-Type", "text/html"):
            print(f"Kein HTML ({resp.headers.get('Content-Type')}), {len(resp.content)} Bytes.")
            return False
        history.append((stable_url, cur_name))
        stable_url, cur_name = clean_url(url), link_name(name) or page_title(resp.text)
        cur_url, cur_html = resp.url, resp.text
        save_page(cur_url, cur_html, cur_name)
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}")
        return True

    while True:
        links = extract_links(cur_html, cur_url, sort=sort and not tree)
        count = len(links)
        if tree:
            links = tree_order(links, sort=sort)
        print("\n" + "=" * 100)
        print(page_title(cur_html))
        print(f"Stabil: {hyperlink(stable_url, stable_url)}")
        if cur_url != stable_url:
            print(f"Server: {hyperlink(cur_url, cur_url)}")
        print(f"{count} Links, {'alphabetisch' if sort else 'Seitenreihenfolge'}"
              + (", Baum" if tree else "") + (f"  (Filter: {flt})" if flt else ""))
        print("-" * 100)
        show(links, host, flt)

        try:
            cmd = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        if cmd == "q":
            return 0
        elif cmd == "b":
            if history:
                prev_url, prev_name = history.pop()
                if open_url(prev_url, prev_name):
                    history.pop()  # open_url hat cur_url erneut angehaengt
            else:
                print("Kein Verlauf.")
        elif cmd == "r":
            if open_url(stable_url, cur_name):
                history.pop()
        elif cmd == "a":
            sort = not sort
        elif cmd == "t":
            tree = not tree
        elif cmd == "h":
            open_url(home_url, "Startseite")
        elif cmd.startswith("/"):
            flt = cmd[1:].strip().casefold()
        elif cmd == "c" or (cmd.startswith("c ") and cmd[2:].strip().isdigit()):
            n = int(cmd[2:]) if cmd != "c" else 0
            url = stable_url if n == 0 else (links[n - 1][1] if n <= len(links) else "")
            if url:
                print(f"Kopiert ({copy_to_clipboard(url)}): {url}")
            else:
                print("Keine URL unter dieser Nummer.")
            input("[Enter] ")
        elif cmd == "l":
            try:
                rows, tree_html = fetch_leistungen(s, c)
            except (HISinOneError, requests.RequestException) as e:
                print(f"Fehler: {e}")
            else:
                save_page(c.qis_base + LEISTUNGEN_PATH, tree_html, "Leistungen_aufgeklappt")
                print_leistungen(rows)
            input("[Enter] ")
        elif cmd.startswith("u "):
            open_url(clean_url(urljoin(cur_url, cmd[2:].strip())))
        elif cmd.startswith("s "):
            Path(cmd[2:].strip()).write_text(cur_html, encoding="utf-8")
            print(f"Gespeichert: {cmd[2:].strip()}")
        elif cmd.lstrip("!").isdigit() and 1 <= int(cmd.lstrip("!")) <= len(links):
            label, url, flow_bound, *_ = links[int(cmd.lstrip("!")) - 1]
            if not url:
                print("Das ist eine Gruppen-Ueberschrift, kein Link.")
            elif flow_bound and not cmd.startswith("!"):
                print(f"'{label}' ist flow-gebunden (_flowExecutionKey, keine stabile URL)."
                      f"\nTrotzdem folgen mit !{cmd}")
                input("[Enter] ")
            else:
                open_url(url, label)
        elif cmd:
            print("Unbekannter Befehl (Nr, !Nr, a, t, b, r, h, c [Nr], l, /text, u <url>, "
                  "s <datei>, q).")


if __name__ == "__main__":
    raise SystemExit(main())
