# Kommandozeilen-Skripte

Alle Skripte werden aus dem Projekt-Hauptordner gestartet und lesen die
Zugangsdaten aus der `.env` (siehe [Installation](installation.md)).

| Skript | Zweck |
| --- | --- |
| `explore_tui.py` | Explorer als Terminal-Oberfläche – siehe [Explorer](explorer.md) |
| `explore.py` | derselbe Explorer als einfache Text-Konsole (REPL) |
| `leistungen.py` | Leistungen komplett aufgeklappt als Tabelle, JSON oder CSV |
| `hisinone_noten.py` | Notenspiegel aus dem Legacy-QIS als JSON – siehe [Noten-API](noten-api.md) |
| `login_test.py` | prüft nur den Login |
| `list_links.py` | listet die Links der Startseite |
| `debug_leistungen.py` | Struktur der Leistungen-Seite (ohne Noten) zur Fehlersuche |

## `explore.py`

```bash
python explore.py           # Links in Seitenreihenfolge
python explore.py --sort    # alphabetisch
python explore.py --tree    # als Baum
python explore.py --save [DIR]   # jede besuchte Seite als HTML speichern
```

Links werden nummeriert; `<Nr>` öffnet, `!<Nr>` öffnet einen Link ohne
stabile URL, `u <url>` eine beliebige Adresse. Weitere Befehle: `a`
(alphabetisch), `t` (Baum), `b` (zurück), `r` (neu laden), `h` (Startseite),
`c [Nr]` (URL kopieren), `l` (Leistungen), `/text` (filtern), `s <datei>`
(Seite speichern), `q` (beenden). Die Liste steht im Kopf von `explore.py`. URLs
erscheinen als anklickbare Terminal-Links (OSC 8; in tmux
`set -ga terminal-features "*:hyperlinks"`).

## `leistungen.py`

Vier Anfragen: Login (2), Seite, „Alle aufklappen“ – mit Zufallspausen.

```bash
python leistungen.py                         # Baum als Tabelle
python leistungen.py --pl                    # nur Prüfungen (PL/PVL), flach
python leistungen.py --pl --latest           # nur der letzte Versuch
python leistungen.py --cols titel,Note,CP,Status
python leistungen.py --pl -o leistungen.csv  # oder .json
```

Spalten für `--cols`: Ebene, Typ, Art, Titel, Nummer, Versuch, Note, CP,
Malus, Status, Freigabe, Rücktritt, Freiversuch, Vermerk, Vorbehalt,
Zusatzmerkmal.

## `list_links.py`, `login_test.py`, `debug_leistungen.py`

```bash
python login_test.py
python list_links.py [-o start.html]
python debug_leistungen.py    # Rohdaten nach /tmp/hisinone-explore/
```

Ausgaben und gespeicherte Seiten enthalten **persönliche Daten** – nicht
committen (`*.html`, `*.csv`, `*.json` stehen in `.gitignore`).
