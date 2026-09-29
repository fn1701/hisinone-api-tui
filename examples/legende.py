"""Kuerzel-Legenden des Notenspiegels (fuer beispiel.py)."""

# Vollstaendige Legende der Kuerzel (aus den "Erlaeuterungen" im Notenspiegel).
# Dient als Fallback - die API liefert unter daten["legende"] die tatsaechlich
# auf der Seite gefundenen Kuerzel ohnehin dynamisch mit.
STATUS_LEGENDE = {
    "AN": "angemeldet",
    "BE": "bestanden",
    "NB": "nicht bestanden",
    "EN": "endgültig nicht bestanden",
    "AB": "abgemeldet",
    "KR": "Krankmeldung",
    "GR": "genehmigter Rücktritt",
    "NGR": "nicht genehmigter Rücktritt",
    "NE": "nicht erschienen",
    "RT": "abgemeldet über Online-Selbstbedienung",
    "ME": "mündl. Ergänzungsprüfung",
    "VZ": "Verzicht auf Wiederholung",
    "TA": "Täuschungsversuch",
    "PV": "Konto/Modul nicht vollständig",
    "FAE": "fristgerechte Arbeitsabgabe erfolgt",
}
ART_LEGENDE = {
    "GE": "Modul",
    "PL": "Teilmodul",
    "MB": "Modul Bachelorarbeit",
    "MM": "Modul Masterarbeit",
    "AA": "Abschlussarbeit (Bachelor od. Master)",
}
SEMESTER_LEGENDE = {
    "SoSe": "Sommersemester",
    "WiSe": "Wintersemester",
}
