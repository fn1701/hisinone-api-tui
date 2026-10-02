# Explorer (Terminal-Oberfläche)

`explore_tui.py` loggt sich mit den Daten aus der `.env` ein und zeigt jede
HISinOne-Seite als **Link-Baum**, Seiten mit Tabellen (Leistungen,
Studienplaner, Vorlesungsverzeichnis …) als **aufklappbare Tabellen**. Alles
ist nur lesend: Belegen, Anmelden o. Ä. löst der Explorer nicht aus.

```bash
python explore_tui.py              # Baumansicht
python explore_tui.py --flat       # flache Liste statt Baum
python explore_tui.py --sort       # Links alphabetisch
python explore_tui.py --save [DIR] # jede besuchte Seite als HTML speichern
python explore_tui.py --no-cache   # Seiten-Cache aus
python explore_tui.py --cache-ttl 600 --cache-min-load 250
python explore_tui.py --no-config  # Config weder lesen noch schreiben
```

Alle Optionen lassen sich auch per Taste umschalten und werden in der
[Config](konfiguration.md) gemerkt.

## Link-Ansicht

Links der Baum, rechts die Seitenleiste: in der ersten Zeile der Name des
markierten Eintrags (Klick oder `n` kopiert ihn), darunter Seite, stabile URL,
Server-URL, Anzahl Links, Abrufzeit und der markierte Link.

Die Hierarchie steckt in den URLs: Navigation in `navigationPosition=a,b,c`,
Vorlesungsverzeichnis-Permalinks in `path=title:…|title:…`. Links ohne beides
stehen unter „Sonstige“.

| Taste | Aktion |
| --- | --- |
| `Enter` / Klick | Link öffnen |
| `/` | Filterfeld (siehe [Filter](filter.md)) |
| `Strg+R` | Regex-Filter an/aus |
| `b` | zurück |
| `h` | Startseite |
| `r` | Seite neu laden (am Cache vorbei) |
| `t` | Baum / Liste |
| `a` | alphabetisch an/aus |
| `v` | Tabelle / nur Links (für Seiten mit Tabellen) |
| `c` | URL kopieren |
| `n` | Namen des markierten Eintrags kopieren |
| `o` | im Browser öffnen |
| `s` | Speichern besuchter Seiten an/aus |
| `!` | Link ohne stabile URL trotzdem öffnen |
| `l` | Leistungen (Shortcut, frei konfigurierbar) |
| `q` | beenden |

**Stabile URLs:** Der `_flowExecutionKey` gilt nur für den gerade laufenden
Ablauf. Links mit `_flowId` starten den Ablauf neu und werden ohne Key
gespeichert. Links ohne `_flowId` hängen an einem laufenden Ablauf; sie öffnen
nur mit `!`. Abmelde-Links ebenso.

## Tabellen

Seiten mit Baum-Tabellen werden erkannt und als Tabellen gezeigt; der Explorer
klickt dabei einmal „Alle aufklappen“, wenn es genau einen solchen Knopf gibt.
Die Titelleiste über einer Tabelle (oder `f`) öffnet sie im Vollbild.

Im Vollbild:

| Taste | Aktion |
| --- | --- |
| `/` | Zeilenfilter |
| `t` | Ansicht: aufklappbare Tabelle → Baum → flache Liste |
| `a` | Geschwister alphabetisch (A–Z) an/aus |
| `Leertaste` / Klick | Knoten auf/zu |
| `+` / `-` | alles auf / alles zu |
| `k` | Spalten wählen |
| `x` | eigene Spalten (Typ, Art) an/aus – nur bei Leistungen |
| `v` | nur letzter Prüfungsversuch – nur bei Leistungen |
| `g` | Seite der Zeile in der App öffnen (Zeilen mit ◆) |
| `o` | Seite der Zeile im Browser öffnen |
| `n` | Titel der Zeile kopieren |
| `e` | Export als CSV oder JSON |
| `Esc` | zurück |

In Baum und Liste zeigt die Seitenleiste den Titel (kopierbar) und alle
übrigen Spalten der markierten Zeile. Ansicht, Spalten, Filter, Sortierung und
zugeklappte Knoten werden **je Tabelle** in der Config gespeichert.

## Studienplaner und Detailseiten

Siehe [Studienplaner](studienplaner.md).

## Meldungen

Alle Meldungen (auch Ladefehler) stehen mit Uhrzeit in
`/tmp/hisinone-log/explore.log`; Fehler bleiben 20 Sekunden sichtbar.

## Rücksicht auf den Server

Zwischen Schritten, die im Browser ein Klick wären, wartet der Explorer
zufällig 200–1000 ms. Langsame Seiten landen im [Cache](konfiguration.md#cache)
und öffnen danach ohne Anfrage; `r` lädt bewusst neu.
