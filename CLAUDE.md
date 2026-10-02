# Hinweise für Claude

## Git

- Niemals `Co-Authored-By`-Zeilen (oder andere Attributionen) in Commit-Messages
  oder PR-Beschreibungen einfügen.
- An jedem stabilen/sinnvollen/modularen Punkt (Feature fertig und getestet,
  in sich abgeschlossene Änderung) einen Commit vorschlagen: Dateien +
  Commit-Message nennen, nach Zustimmung lokal committen.
- Nicht pushen, solange nicht ausdrücklich gewünscht.
- Niemals committen: `.env`, gespeicherte Seiten/Exporte (enthalten Noten).

## Code-Stil (Clean Code, lesbar mit C++/OO-Hintergrund)

Gilt für alle Python-Dateien. Durchgesetzt per pre-commit
(`pre-commit install`, einmalig alles: `pre-commit run --all-files`).

- **Größen** (Hook `check-lengths`, `tools/check_lengths.py`):
  - Datei höchstens 150 Zeilen -> lieber mehr kleine Module in Paketen.
  - Methode/Funktion höchstens 20 Code-Zeilen (Rumpf ohne Signatur,
    Docstring, Kommentar- und Leerzeilen); Ziel ~10.
  - Zyklomatische Komplexität höchstens 10 (ruff C901).
- **Struktur wie in C++**: Klassen mit einer klaren Verantwortung;
  zusammengehörige Daten als `@dataclass` statt loser `dict`s/Tupel;
  Hilfsmethoden "privat" mit `_`-Präfix; keine Logik auf Modulebene.
- **Explizit statt clever**: Typ-Annotationen an allen Signaturen; sprechende
  Namen (keine Ein-Buchstaben-Namen außer Schleifenindex); keine
  verschachtelten Comprehensions, keine Lambdas mit Logik, kein `nonlocal`.
- **Kommentare** erklären die Absicht (*warum*), nicht das *was*; Docstring
  an jeder Klasse und öffentlichen Methode. Sprache wie der umgebende Code
  (Deutsch).
- **Umlaute**: In Text für Menschen echte Umlaute und ß (ä ö ü ß) –
  Kommentare, Docstrings, Oberflächentexte/Meldungen, Markdown,
  Commit-Messages. In Bezeichnern (Variablen, Methoden, Klassen), Datei- und
  Modulnamen sowie Config-/JSON-Schlüsseln dagegen keine Umlaute
  (ae/oe/ue/ss).
- **Formatierung/Lint**: `ruff format` und `ruff check` (Regeln in
  `pyproject.toml`: E, F, W, I, N, UP, B, SIM, C90; Zeilenlänge 100).
- **Allgemein für alle HISinOne-Systeme**, nicht nur eine Hochschule: keine
  Hochschul-Hosts, -Pfade oder -IDs im Code oder in Test-/Probe-Skripten
  hartkodieren; Adressen aus `.env`/Client (`base_url`, `qis_base`) bzw. aus
  der geladenen Seite ableiten. Hochschulspezifisches nur in Config/`.env`.
- Öffentliche API/CLIs bleiben stabil (`from hisinone_noten import
  HISinOneClient, ...`, `python hisinone_noten.py`, `explore*.py`,
  `leistungen.py`).
