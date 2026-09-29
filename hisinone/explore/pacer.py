"""Zufallspausen zwischen "Klicks", damit der Server nicht in Serie getroffen wird."""

import random
import threading
import time


class Pacer:
    """Kurze Zufallspause (200-1000 ms) zwischen Schritten, fuer die ein Mensch
    im Browser klicken muesste (Seite -> Button -> naechste Seite ...).
    Requests innerhalb eines Seitenaufrufs (Redirects) werden nicht gebremst;
    liegt der letzte Schritt schon laenger zurueck, wird nicht gewartet."""

    def __init__(self, low: float = 0.2, high: float = 1.0):
        self.low, self.high = low, high
        self._last = 0.0
        self._lock = threading.Lock()  # TUI laedt in Hintergrund-Threads

    def step(self) -> None:
        """Vor jedem "Klick" aufrufen."""
        with self._lock:
            wait = self._last + random.uniform(self.low, self.high) - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()


# Eine gemeinsame Instanz fuer das ganze Programm (alle Requests an denselben Server)
pacer = Pacer()
