"""Alle Meldungen der App (auch Fehler aus Hintergrund-Ladevorgängen) mit
Uhrzeit in eine Logdatei; Fehler bleiben länger stehen."""

import time

from hisinone.explore.storage import prepare_save_dir

LOG_DIR = "/tmp/hisinone-log"  # wie Cache/Speicherordner nur für den eigenen User
LOG_FILE = "explore.log"
ERROR_SECONDS = 20  # Standard (5 s) reicht zum Lesen langer Fehlertexte nicht


class MessageLog:
    """Mixin vor App: ersetzt notify, damit jede Meldung auch im Log steht."""

    def notify(self, message: str, *, title: str = "", severity: str = "information",
               timeout: float | None = None, markup: bool = True) -> None:  # fmt: skip
        _append(f"{severity.upper():11} {title + ': ' if title else ''}{message}")
        if timeout is None and severity == "error":
            timeout = ERROR_SECONDS
        super().notify(message, title=title, severity=severity, timeout=timeout, markup=markup)


def _append(line: str) -> None:
    """Logfehler (z.B. /tmp voll) dürfen die App nicht stoppen."""
    try:
        path = prepare_save_dir(LOG_DIR) / LOG_FILE
        with path.open("a", encoding="utf-8") as log:
            log.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {line}\n")
        path.chmod(0o600)
    except OSError:
        pass
