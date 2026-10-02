# Filter

Link-Baum und Tabellen haben ein Filterfeld (`/`). Es kennt zwei Arten.

## Normal

Begriffe mit Leerzeichen getrennt, jeder muss vorkommen (ohne Groß-/
Kleinschreibung). `"Spalte"=Wert` sucht nur in einer Spalte. Die Vorschläge
(`↓`) bieten die Spalten an.

## Regex

Häkchen „Regex“ oder `Strg+R` (gilt für alle Seiten): Python-`re`.
Groß-/Kleinschreibung ist egal, der Ausdruck kann irgendwo im Text passen.
Bei eingeschalteter Regex zeigen die Vorschläge (`↓`) Beispiele.

In Tabellen sieht die Regex jede Zeile **samt ihren Eltern** als einen Text.
Die Eltern stehen zuerst, leere Spalten fehlen:

```text
Titel=Modul X | A=Bestanden | Titel=Prüfung Y | 1=PL | A=Bestanden
```

Passt eine Zeile, gilt das auch für alles darunter: Ein Treffer im Modul zeigt
seine Prüfungen, ein Ausschluss blendet den ganzen Teilbaum aus. Mitgezeigt
werden die Eltern der Treffer. Badge-Spalten heißen `A`, `B`, `C` usw.,
Info-Spalten `1`, `2` usw.

| Ausdruck | Bedeutung |
| --- | --- |
| `Bestanden` | enthält „Bestanden“ |
| `^(?!.*Bestanden)` | enthält **nicht** „Bestanden“ |
| `^(?=.*\bPL\b)(?!.*Bestanden)` | enthält „PL“ (als Wort), aber nicht „Bestanden“ |
| `\bA=Bestanden` | Spalte `A` ist „Bestanden“ |
| `Titel=[^\|]*PV(?!.*\bA=Bestanden)` | „PV“ in der Spalte Titel und Spalte A nicht „Bestanden“ |
| `Mathe\|Programm` | enthält eins von beiden |
| `^Titel=Mathe` | oberster Elternknoten beginnt mit „Mathe“ |

Im Link-Baum ist der Text „Beschriftung URL“; Beispiel: `_flowId=.*exam`
findet Links, deren URL einen Ablauf mit „exam“ im Namen startet.

## Ansichten

Der Filter wirkt in allen Tabellen-Ansichten gleich. In der aufklappbaren
Tabelle und im Baum erscheinen Treffer mit ihren Eltern (das Filterergebnis
hat einen eigenen Auf-/Zu-Zustand), in der flachen Liste nur die Treffer.
Der Filter wird je Tabelle gespeichert.
