"""Spalten der Leistungen-Ausgabe: Schluessel in den Zeilen <-> Anzeigename."""

# "art" = PL/PVL (berechnet)
COLUMNS = [("ebene", "Ebene"), ("typ", "Typ"), ("art", "Art"), ("titel", "Titel"),
           ("Nummer", "Nummer"), ("Versuch", "Versuch"), ("Bewertung", "Note"),
           ("Bonus", "CP"), ("Malus", "Malus"), ("Status", "Status"),
           ("Freigabedatum", "Freigabe"), ("Rücktritt", "Rücktritt"),
           ("Freiversuch", "Freiversuch"), ("Vermerk", "Vermerk"),
           ("Vorbehalt", "Vorbehalt"), ("Zusatzmerkmal", "Zusatzmerkmal")]  # fmt: skip
DEFAULT_COLS = ["titel", "art", "Nummer", "Versuch", "Bewertung", "Bonus", "Status",
                "Freigabedatum"]  # fmt: skip
COL_LABEL = dict(COLUMNS)


def column_label(key: str) -> str:
    """Anzeigename; Baum-Tabellen-Spalten heissen schon wie angezeigt."""
    return COL_LABEL.get(key, key)


def parse_cols(spec: str) -> list[str]:
    """ "titel,Note,CP" -> Schluessel; akzeptiert Schluessel oder Anzeigenamen."""
    lookup = {key.casefold(): key for key, _ in COLUMNS}
    lookup |= {label.casefold(): key for key, label in COLUMNS}
    cols = []
    for part in filter(None, (p.strip() for p in spec.split(","))):
        if part.casefold() not in lookup:
            known = ", ".join(label for _, label in COLUMNS)
            raise ValueError(f"Unbekannte Spalte {part!r} (moeglich: {known})")
        cols.append(lookup[part.casefold()])
    return cols
