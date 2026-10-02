# Konfiguration, Cache und Dateien

## Config-Datei

`~/.config/hisinone-explore/config.json` (bzw. `$XDG_CONFIG_HOME/…`), nur für
den eigenen Benutzer lesbar (0600), da Filter Modulnamen enthalten können. Der
Explorer schreibt sie selbst (regelmäßig und beim Beenden); `--no-config`
schaltet das ab. Kommandozeilen-Optionen gelten nur für den Lauf, Tasten
ändern die Config.

| Schlüssel | Bedeutung |
| --- | --- |
| `tree`, `sort`, `regex` | Baum statt Liste, alphabetisch, Regex-Filter |
| `save_on`, `save_path` | besuchte Seiten als HTML speichern, Ordner |
| `no_cache`, `cache_ttl`, `cache_min_load_ms` | [Cache](#cache) |
| `shortcuts` | Tasten für feste Seiten (s. u.) |
| `pages` | gelernte Seiten, Schlüssel = stabile URL (s. u.) |
| `collapsed`, `collapsed_overrides` | zugeklappte Knoten im Link-Baum (global bzw. je Seite) |

### Shortcuts

```json
"shortcuts": [
  {"key": "l", "description": "Leistungen",
   "path": "/pages/...", "open_table_with_column": "Versuch"}
]
```

`path` ist relativ zur HISinOne-Adresse oder eine volle URL;
`open_table_with_column` öffnet nach dem Laden die erste Tabelle mit dieser
Spalte gleich im Vollbild.

### Seiten (`pages`)

Beim ersten Besuch einer Seite mit Baum-Tabelle trägt der Explorer ein:

- `view`: `"table"` (Tabellen-Ansicht) oder `"tree"` (nur Links, z. B. reine
  Navigationsbäume) – Taste `v`
- `expand`: einmal „Alle aufklappen“ klicken
- `open_table`: diese Tabelle gleich im Vollbild
- `tables`: je Tabelle Spalten, Filter, Ansicht (`table`/`tree`/`flat`),
  Sortierung, zugeklappte Knoten, eigene Spalten, letzter Versuch

Alle Werte dürfen von Hand geändert werden; danach gilt, was in der Config
steht.

## Cache

Seiten, die länger als `cache_min_load_ms` (Standard 250 ms) laden, werden in
`/tmp/hisinone-cache` abgelegt (Dateiname = Hash der stabilen URL, nur für den
Benutzer lesbar) und mit Abrufzeit angezeigt. `cache_ttl` (Sekunden, 0 =
unbegrenzt bis zum Neustart) bestimmt, wann neu geladen wird. `r` lädt immer
neu; `--no-cache` schaltet den Cache ganz ab.

## Dateien in `/tmp`

| Pfad | Inhalt |
| --- | --- |
| `/tmp/hisinone-cache/` | Seiten-Cache |
| `/tmp/hisinone-explore/` | gespeicherte Seiten (`s` / `--save`), Exporte |
| `/tmp/hisinone-log/explore.log` | alle Meldungen mit Uhrzeit |

Alle Ordner werden mit 0700 angelegt. Gespeicherte Seiten und Exporte
enthalten **persönliche Daten (Noten)** – nicht weitergeben, nicht committen.
