#!/usr/bin/env python3
"""
HISinOne-Explorer als Terminal-Oberflaeche (Textual): Links einer Seite als
Baum, per Klick oder Enter oeffnen. Die Logik (Login, Links, Baum, stabile
URLs, Speichern) liegt in hisinone/explore - siehe explore.py.

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
    v               Seite mit Baum-Tabelle: Tabellen-Ansicht / nur Links umschalten
                    (gemerkt in der Config unter "pages")
    o               URL im Browser oeffnen (neue Browser-Sitzung, ohne Login!)
    s               Speichern an/aus (Ordner aus --save, sonst /tmp/hisinone-explore;
                    beim Einschalten wird die aktuelle Seite gleich gespeichert)
    l               Leistungen laden, Tabelle "Leistungsdaten" im Vollbild
                    (Tasten wie l sind in der Config unter "shortcuts" einstellbar)
    q               beenden

Tabellen: Seiten mit Daten-Baumtabelle (Leistungen, ...; reine Navigations-
baeume wie das Vorlesungsverzeichnis bleiben Links)
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

Einstellungen (Baum, alphabetisch, Speichern an/aus + Ordner, Shortcuts, je
Seite mit Baum-Tabelle view/expand/open_table und je Tabelle Spalten/eigene
Spalten/letzter Versuch/Filter, zugeklappte Knoten im Link-Baum je Seite -
letztere werden nur beim Beenden geschrieben) stehen in
~/.config/hisinone-explore/config.json (0600, enthaelt ggf. Filter mit
Modulnamen). Gelesen beim Start; geschrieben beim Beenden und alle 100 s,
aber nur wenn sich etwas geaendert hat. Angegebene Optionen (--flat, --sort,
--save) gehen vor; --no-config schaltet die Datei ab.

Zwischen Schritten, die im Browser ein Klick waeren, wird zufaellig
200-1000 ms gewartet (siehe hisinone/explore/pacer.py).
"""

# Der Code liegt im Paket hisinone/tui (Oberflaeche) und hisinone/explore (Logik).
from hisinone.tui.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
