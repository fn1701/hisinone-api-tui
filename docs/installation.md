# Installation & Einrichtung

## Voraussetzungen

- **Python 3.11** oder neuer
- ein gültiger Hochschul-Account (Benutzerkennung + Passwort) an einer
  HISinOne-Hochschule
- für den Explorer ein Terminal mit Unicode und 256 Farben (Linux, macOS,
  Windows Terminal); optional `wl-copy` oder `xclip` zum Kopieren

```bash
python3 --version
```

## 1. Projekt holen

```bash
git clone https://github.com/fn1701/hisinone-api-tui.git
cd hisinone-api-tui
```

## 2. Virtuelle Umgebung und Abhängigkeiten

```bash
python3 -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Mit [uv](https://docs.astral.sh/uv/) geht es auch so:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

Abhängigkeiten: `requests` (alle Teile) und `textual` (nur der Explorer).

## 3. Zugangsdaten und Adressen in `.env`

```bash
cp .env.example .env          # Windows: copy .env.example .env
```

Dann `.env` ausfüllen:

```ini
HISINONE_USERNAME=deine-benutzerkennung
HISINONE_PASSWORD=dein-passwort

# Adresse deiner Hochschule (ohne Pfad) und des Legacy-QIS
HISINONE_BASE_URL=https://campus.example.org
HISINONE_ICMS_URL=https://campus.example.org/qisserver

# nur für die Noten-API: Studiengang-Knoten im Notenspiegel-Baum
HISINONE_NODE_ID=auswahlBaum%7Cabschluss%3Aabschl%3D84%2Cstgnr%3D1
```

- `HISINONE_BASE_URL` ist die Adresse, unter der du dich im Browser bei
  HISinOne anmeldest (z. B. `https://campus.example.org`).
- `HISINONE_ICMS_URL` braucht nur die Noten-API, falls deine Hochschule die
  Noten im alten QIS anzeigt.
- `HISINONE_NODE_ID`: Notenspiegel im Browser öffnen und den Parameter
  `nodeID=...` aus der URL übernehmen (URL-kodiert).

Hochschulspezifisches steht nur in der `.env`, nie im Code. Die `.env` ist per
`.gitignore` ausgeschlossen – **niemals committen.**

## 4. Testen

```bash
python login_test.py          # nur der Login
python explore_tui.py         # Explorer (Terminal-Oberfläche)
python hisinone_noten.py      # Notenspiegel als JSON
```

## Für Entwickler

```bash
pip install pre-commit ruff
pre-commit install
pre-commit run --all-files
```

Die Hooks prüfen Formatierung und Lint (`ruff`), Datei-/Funktionslängen
(`tools/check_lengths.py`) und dass keine `.env` oder gespeicherten Seiten
committet werden. Die Stilregeln stehen in [`CLAUDE.md`](../CLAUDE.md).
