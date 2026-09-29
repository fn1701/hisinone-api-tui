# Hinweise fuer Claude

## Git

- Niemals `Co-Authored-By`-Zeilen (oder andere Attributionen) in Commit-Messages
  oder PR-Beschreibungen einfuegen.
- An jedem stabilen/sinnvollen/modularen Punkt (Feature fertig und getestet,
  in sich abgeschlossene Aenderung) einen Commit vorschlagen: Dateien +
  Commit-Message nennen, nach Zustimmung lokal committen.
- Nicht pushen, solange nicht ausdruecklich gewuenscht.
- Niemals committen: `.env`, gespeicherte Seiten/Exporte (enthalten Noten).

## Code-Stil (Clean Code, lesbar mit C++/OO-Hintergrund)

Gilt fuer alle Python-Dateien. Durchgesetzt per pre-commit
(`pre-commit install`, einmalig alles: `pre-commit run --all-files`).

- **Groessen** (Hook `check-lengths`, `tools/check_lengths.py`):
  - Datei hoechstens 150 Zeilen -> lieber mehr kleine Module in Paketen.
  - Methode/Funktion hoechstens 20 Code-Zeilen (Rumpf ohne Signatur,
    Docstring, Kommentar- und Leerzeilen); Ziel ~10.
  - Zyklomatische Komplexitaet hoechstens 10 (ruff C901).
- **Struktur wie in C++**: Klassen mit einer klaren Verantwortung;
  zusammengehoerige Daten als `@dataclass` statt loser `dict`s/Tupel;
  Hilfsmethoden "privat" mit `_`-Praefix; keine Logik auf Modulebene.
- **Explizit statt clever**: Typ-Annotationen an allen Signaturen; sprechende
  Namen (keine Ein-Buchstaben-Namen ausser Schleifenindex); keine
  verschachtelten Comprehensions, keine Lambdas mit Logik, kein `nonlocal`.
- **Kommentare** erklaeren die Absicht (*warum*), nicht das *was*; Docstring
  an jeder Klasse und oeffentlichen Methode. Sprache wie der umgebende Code
  (Deutsch, ohne Umlaute in Bezeichnern).
- **Formatierung/Lint**: `ruff format` und `ruff check` (Regeln in
  `pyproject.toml`: E, F, W, I, N, UP, B, SIM, C90; Zeilenlaenge 100).
- Oeffentliche API/CLIs bleiben stabil (`from hisinone_noten import
  HISinOneClient, ...`, `python hisinone_noten.py`, `explore*.py`,
  `leistungen.py`).
