#!/usr/bin/env python3
"""
Debug fuer die Leistungen-Seite: Login, Leistungen laden, einmal "Alle
aufklappen" (4 Requests, mit Pacer-Pausen). Gibt nur Struktur/Zaehler aus,
keine Noten. Rohdaten landen in /tmp/hisinone-explore/ (0700, persoenlich!).

    .venv/bin/python debug_leistungen.py
"""

import explore
from hisinone_noten import HISinOneClient

c = HISinOneClient.from_env()
s, _ = explore.login(c)
print("Login OK")
d = explore.prepare_save_dir("/tmp/hisinone-explore")

explore.pacer.step()
page = s.get(c.qis_base + explore.LEISTUNGEN_PATH, timeout=c.timeout)
page.encoding = "utf-8"
print(f"GET {page.status_code} {page.url}")
print("  Formular examsReadonly:", 'id="examsReadonly"' in page.text)
print("  Button Alle aufklappen:", f'id="{explore.EXPAND_ALL}"' in page.text)
print("  Zeilen (zugeklappt):", len(explore.parse_leistungen(page.text)))
print("  ->", explore.save_html(d, page.url, page.text, "debug_get"))

# Antwort des POST mitschneiden, auch wenn jsf_click sie nicht versteht
captured = {}
orig_post = s.post


def post(*a, **kw):
    captured["r"] = r = orig_post(*a, **kw)
    return r


s.post = post
try:
    frag = explore.jsf_click(s, page.url, page.text, explore.LEISTUNGEN_FORM,
                             explore.EXPAND_ALL, c.timeout)
    rows = explore.parse_leistungen(frag)
    print("Zeilen (aufgeklappt):", len(rows))
    print("  Tiefe/Typ:", sorted({(r["tiefe"], r["typ"]) for r in rows}))
except Exception as e:  # noqa: BLE001 - Debug
    print("FEHLER:", type(e).__name__, e)
r = captured.get("r")
if r is not None:
    print(f"POST {r.status_code} {r.headers.get('Content-Type')} {len(r.text)} Zeichen")
    print("  Anfang:", r.text[:300].replace("\n", " "))
    print("  ->", explore.save_html(d, r.url, r.text, "debug_post"))
