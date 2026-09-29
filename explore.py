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

Der Code liegt im Paket ``hisinone/explore/``; dieses Skript startet nur
hisinone.explore.cli.main.

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

from hisinone.explore.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
