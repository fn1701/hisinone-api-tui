# Studienplaner und Detailseiten

## Studienplaner

Der Link „Studienplaner“ öffnet eine eigene Seite: oben Studiengang und die
Filter der Seitenleiste (Semester, Studiensemester, Veranstaltungen,
Prüfungen …), darunter die geladene Tabelle mit allem, was die
[Vollbild-Tabelle](explorer.md#tabellen) kann.

| Taste | Aktion |
| --- | --- |
| `l` / „Übernehmen“ | Auswahl laden (aus dem Cache, falls vorhanden) |
| `r` | Auswahl neu vom Server laden |
| `f` / Klick auf die Titelleiste | Tabelle im Vollbild (ohne Auswahlfelder) |
| `g` | Modulbeschreibung o. Ä. der Zeile öffnen |

- Wie im Browser werden fehlende Filter erst nach dem Studiengang gesetzt;
  Filter, die die Seite nicht anbietet, bleiben beim Seitenstand.
- Die Spalten kommen nach Position aus dem Markup: Info-Spalten `1..n`,
  Status-Badges `A, B, C …`.
- Die Tabelle wird unter der angefragten und der tatsächlich geladenen Auswahl
  gecacht; nach einem Neustart öffnet dieselbe Auswahl ohne Anfrage.
- Im Vollbild geänderte Filter/Spalten gelten nach `Esc` auch im Planer.

## Detailseiten

Zeilen mit eigener Seite sind mit ◆ markiert. `g` öffnet sie in der App, z. B.
eine Modulbeschreibung. Detailseiten werden als lesbarer Text gezeigt.

| Taste | Aktion |
| --- | --- |
| `1`–`9` | Registerkarte wählen |
| `i` | Inhaltsverzeichnis an/aus |
| `e` | Export als Markdown |
| `r` | Registerkarte neu laden |
| `o` | Seite im Browser öffnen |
| `Esc` | zurück (z. B. zum Studienplaner) |

Registerkarten haben in HISinOne keine eigenen URLs; der Explorer schickt das
Formular wie der Browser ab und cacht jede Karte einzeln. Tabellen der Karten
erscheinen als Markdown-Tabellen; ein ◆-Link darin öffnet die verlinkte Seite
in der App.
