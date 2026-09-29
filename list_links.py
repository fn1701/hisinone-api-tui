#!/usr/bin/env python3
"""
Loggt sich ins HISinOne ein und listet alle Links der Startseite (Menue,
Kacheln, ...) auf - um herauszufinden, welche Bereiche es gibt.

Benutzung (aus dem Projekt-Hauptordner, .env wie bei login_test.py):
    python list_links.py                 # Links nach stdout
    python list_links.py -o start.html   # zusaetzlich rohes HTML speichern

Achtung: start.html enthaelt persoenliche Daten - nicht committen.
"""

import argparse
import html as htmlmod
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

from hisinone_noten import HISinOneClient, HISinOneError


def main() -> int:
    ap = argparse.ArgumentParser(description="Links der HISinOne-Startseite auflisten.")
    ap.add_argument("-o", "--output", help="Rohes HTML der Startseite in diese Datei")
    args = ap.parse_args()

    try:
        c = HISinOneClient.from_env()
    except HISinOneError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 1

    s = c._new_session()
    start = s.get(f"{c.qis_base}/pages/cs/sys/portal/hisinoneStartPage.faces",
                  timeout=c.timeout)
    r = s.post(f"{c.qis_base}/rds?state=user&type=1&category=auth.login",
               data={"userInfo": "", "ajax-token": c._find_ajax_token(start.text),
                     "asdf": c.username, "fdsa": c.password, "submit": ""},
               headers={"Origin": c.base_url, "Referer": start.url},
               timeout=c.timeout)
    if "abmelden" not in r.text.lower():
        print("Login FAILED", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(r.text, encoding="utf-8")
        print(f"HTML -> {args.output}", file=sys.stderr)

    seen = set()
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S | re.I):
        href = htmlmod.unescape(m.group(1))
        if href.startswith(("#", "javascript:", "mailto:")):
            continue
        text = re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
        url = urljoin(r.url, href)
        if url in seen:
            continue
        seen.add(url)
        print(f"{text[:50]:50}  {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
