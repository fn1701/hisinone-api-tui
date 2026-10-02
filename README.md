# HISinOne API & TUI

Inoffizielle Werkzeuge für das Campus-Management-System
[HISinOne](https://www.his.de/) – im Terminal statt im Browser:

- **Explorer (TUI):** jede HISinOne-Seite als Link-Baum, Tabellen wie
  Leistungen oder Studienplaner als aufklappbare, filterbare Tabellen,
  Modulbeschreibungen als lesbarer Text – mit Cache, Export und Tastaturbedienung.
- **Noten-API:** den Notenspiegel als JSON abrufen, als CLI oder
  Python-Bibliothek.
- **Skripte:** Leistungen als Tabelle/CSV/JSON, Link-Listen, Login-Test.

> **Inoffiziell und nur lesend.** Das Projekt nutzt ausschließlich die normale
> Web-Oberfläche mit **deinen eigenen** Zugangsdaten. Es belegt, meldet an oder
> ändert nichts. Nutzung auf eigene Verantwortung, nur für den eigenen Account.

## Features

- Login ins moderne HISinOne, auf Wunsch SSO-Übergabe ins Legacy-QIS
- **Link-Baum** aus der Navigation (`navigationPosition`) und Permalinks;
  stabile URLs ohne flüchtige Ablauf-Schlüssel
- **Baum-Tabellen** generisch erkannt und aufgeklappt; Ansichten Tabelle,
  Baum und Liste; Spaltenwahl, A–Z-Sortierung, Export als CSV/JSON
- **Filter** mit Spalten-Syntax oder Regex über Zeile samt Eltern
- **Studienplaner** mit Studiengang und Filtern, Detailseiten mit
  Registerkarten, Inhaltsverzeichnis und Markdown-Export
- **Cache** für langsame Seiten, zufällige Pausen zwischen Anfragen
- Einstellungen je Seite und Tabelle in einer Config-Datei; frei belegbare
  Shortcuts; Meldungs-Log in `/tmp`
- Hochschul-unabhängig: Adressen nur in der `.env`

## Schnellstart

```bash
git clone https://github.com/fn1701/hisinone-api-tui.git
cd hisinone-api-tui
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # Zugangsdaten und Adresse deiner Hochschule eintragen
python explore_tui.py
```

Python 3.11 oder neuer. Details: [Installation](docs/installation.md).

## Dokumentation

| Thema | Inhalt |
| --- | --- |
| [Installation](docs/installation.md) | Voraussetzungen, `.env`, Entwickler-Setup |
| [Explorer](docs/explorer.md) | Oberfläche, Tasten, Tabellen |
| [Filter](docs/filter.md) | Filter-Syntax und Regex-Beispiele |
| [Studienplaner](docs/studienplaner.md) | Planer, Detailseiten, Registerkarten |
| [Konfiguration](docs/konfiguration.md) | Config-Datei, Cache, Dateien in `/tmp` |
| [Noten-API](docs/noten-api.md) | Notenspiegel als JSON, Bibliothek, Fehlerbehandlung |
| [Skripte](docs/skripte.md) | `explore.py`, `leistungen.py` und weitere CLIs |

## Projektstatus

- Hervorgegangen aus [Dirtez03/hisinone-noten-api](https://github.com/Dirtez03/hisinone-noten-api)
  (Noten-API, getestet an der Hochschule Hannover); Explorer, Skripte und
  Pakete sind in diesem Fork entstanden.
- HISinOne wird an jeder Hochschule anders konfiguriert. Getestet ist der
  Stand an einzelnen Installationen; andere können funktionieren, sind aber
  **nicht garantiert**.
- Der Code wurde mit Hilfe eines KI-Assistenten erstellt. Vor produktivem
  Einsatz selbst prüfen.

## Sicherheit und Datenschutz

- Die `.env` mit deinen Zugangsdaten ist per `.gitignore` ausgeschlossen –
  **niemals committen.**
- Gespeicherte Seiten, Exporte, Cache und Config enthalten persönliche Daten
  (Noten, Modulnamen); sie liegen nur für deinen Benutzer lesbar in `/tmp`
  bzw. `~/.config`. Ein pre-commit-Hook verhindert, dass sie ins Repository
  gelangen.

## Lizenz

MIT – siehe [LICENSE](LICENSE).
