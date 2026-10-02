#!/usr/bin/env python3
"""
Beispiel: HISinOne Noten API in ein eigenes Skript einbauen.

Zeigt, wie man den Notenspiegel abruft, das zurückgegebene dict
weiterverarbeitet und die Status-/Modul-Kürzel ausschreibt. Ausführen aus
dem Projektordner:

    python examples/beispiel.py

Die Zugangsdaten werden aus der .env im Projekt-Hauptordner gelesen.
"""

import contextlib
import sys
import time
from pathlib import Path

# Damit "import hisinone_noten" funktioniert, wenn das Beispiel aus dem
# examples/-Unterordner läuft: den Projekt-Hauptordner auf den Suchpfad legen.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from legende import ART_LEGENDE, SEMESTER_LEGENDE, STATUS_LEGENDE  # noqa: E402

from hisinone_noten import HISinOneAuthError, HISinOneClient, HISinOneError  # noqa: E402

# Windows-Konsole auf UTF-8 (für Umlaute in der Legende)
with contextlib.suppress(Exception):
    sys.stdout.reconfigure(encoding="utf-8")


def komma_float(wert: str) -> float:
    """'2,5' -> 2.5 ; leere Strings -> 0.0"""
    return float(wert.replace(",", ".")) if wert else 0.0


def bedeutung(code: str, daten: dict) -> str:
    """Schreibt ein Kürzel aus: bevorzugt die vom Notenspiegel gelieferte
    daten['legende'], sonst die eingebauten Referenz-Tabellen oben."""
    leg = daten.get("legende", {})
    return (
        leg.get(code)
        or STATUS_LEGENDE.get(code)
        or ART_LEGENDE.get(code)
        or SEMESTER_LEGENDE.get(code)
        or code
    )


def noten_mit_wiederholung(versuche: int = 5, pause: int = 10) -> dict:
    """Ruft den Notenspiegel ab und fängt die sporadische "leere Seite" des
    QIS-Portals ab: bei einem HISinOneError kurz warten und erneut versuchen.
    Falsche Zugangsdaten (HISinOneAuthError) brechen sofort ab - da hilft kein
    Retry."""
    client = HISinOneClient.from_env()
    for i in range(1, versuche + 1):
        try:
            return client.get_grades()
        except HISinOneAuthError:
            raise
        except HISinOneError as e:
            if i == versuche:
                raise
            print(f"Versuch {i} fehlgeschlagen ({e}).", file=sys.stderr)
            print(f"Warte {pause}s und versuche es erneut ...", file=sys.stderr)
            time.sleep(pause)


def zeige_stammdaten(daten: dict) -> None:
    s = daten["student"]
    z = daten["zusammenfassung"]
    print(f"Student:      {s['name']} (Matrikel {s['matrikelnummer']})")
    print(f"Studiengang:  {daten['studiengang']}")
    print(f"Durchschnitt: {z['durchschnitt']}  |  Credits: {z['credits']}")
    print("-" * 60)


def pl_nach_status(daten: dict) -> dict[str, list]:
    """Nur echte Prüfungsleistungen (Art == 'PL'), nach Status gruppiert."""
    gruppen: dict[str, list] = {}
    for p in daten["pruefungen"]:
        if p["art"] == "PL":
            gruppen.setdefault(p["status"], []).append(p)
    return gruppen


def zeige_gruppen(gruppen: dict[str, list], daten: dict) -> None:
    """Das Status-Kürzel wird jeweils ausgeschrieben."""
    print(f"Prüfungen ({ART_LEGENDE['PL']}) nach Status:")
    for status in sorted(gruppen):
        items = gruppen[status]
        print(f"\n  {status} = {bedeutung(status, daten)}  ({len(items)})")
        for p in items:
            note = p["note"] or "-"
            print(f"    {p['text']:35} {note:>5}  Versuch {p['versuch']}  {p['semester']}")


def zeige_schnitt(bestanden: list) -> None:
    """Eigener, credits-gewichteter Schnitt über die benoteten Bestandenen."""
    benotet = [p for p in bestanden if p["note"]]
    summe_cp = sum(komma_float(p["credits"]) for p in benotet)
    if summe_cp:
        gewichtet = sum(komma_float(p["note"]) * komma_float(p["credits"]) for p in benotet)
        print("\n" + "-" * 60)
        print(f"Eigener gewichteter Schnitt: {gewichtet / summe_cp:.2f}  "
              f"({summe_cp:.1f} CP benotet)")  # fmt: skip


def zeige_legende(daten: dict) -> None:
    """Die im Notenspiegel gefundenen Kürzel (JSON-Feld 'legende'); fällt
    das mal leer aus, die eingebaute Referenz zeigen."""
    print("\n" + "-" * 60)
    print("Legende (Kürzel im Notenspiegel):")
    legende = daten.get("legende") or {**STATUS_LEGENDE, **ART_LEGENDE, **SEMESTER_LEGENDE}
    for code in sorted(legende):
        print(f"  {code:4} = {legende[code]}")


def main() -> int:
    # Abrufen (Zugangsdaten aus .env), mit automatischer Wiederholung bei
    # der sporadischen "leere Seite"-Zicke des QIS-Portals.
    try:
        daten = noten_mit_wiederholung()
    except HISinOneAuthError:
        print("Benutzername oder Passwort stimmt nicht.", file=sys.stderr)
        return 1
    except HISinOneError as e:
        print("Abruf endgültig fehlgeschlagen:", e, file=sys.stderr)
        return 1
    zeige_stammdaten(daten)
    gruppen = pl_nach_status(daten)
    zeige_gruppen(gruppen, daten)
    zeige_schnitt(gruppen.get("BE", []))
    zeige_legende(daten)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
