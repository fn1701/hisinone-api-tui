"""HISinOneClient: Login ins moderne HISinOne und Abruf des Notenspiegels."""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable

import requests

from .env import load_env
from .errors import HISinOneAuthError, HISinOneError
from .parser import parse_notenspiegel
from .qis import QisNotenspiegel

DEFAULT_BASE_URL = "https://campusmanagement.hs-hannover.de"
DEFAULT_ICMS_URL = "https://icms.hs-hannover.de/qisserver"
DEFAULT_NODE_ID = "auswahlBaum%7Cabschluss%3Aabschl%3D84%2Cstgnr%3D1"
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)
START_PAGE = "/pages/cs/sys/portal/hisinoneStartPage.faces"
LOGIN_ACTION = "/rds?state=user&type=1&category=auth.login"

# (Umgebungsvariable, Konstruktor-Parameter, Standardwert) fuer from_env
ENV_SETTINGS = [
    ("HISINONE_USERNAME", "username", ""),
    ("HISINONE_PASSWORD", "password", ""),
    ("HISINONE_BASE_URL", "base_url", DEFAULT_BASE_URL),
    ("HISINONE_ICMS_URL", "icms_url", DEFAULT_ICMS_URL),
    ("HISINONE_NODE_ID", "node_id", DEFAULT_NODE_ID),
    ("HISINONE_USER_AGENT", "user_agent", DEFAULT_UA),
]


def _no_pause() -> None:
    """Standard fuer login(): zwischen den Schritten nicht warten."""


class HISinOneClient:
    """Zugangsdaten + Adressen einer HISinOne-Installation."""

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = DEFAULT_BASE_URL,
        icms_url: str = DEFAULT_ICMS_URL,
        node_id: str = DEFAULT_NODE_ID,
        user_agent: str = DEFAULT_UA,
        timeout: int = 25,
    ):
        if not username or not password:
            raise HISinOneError("Benutzername/Passwort fehlen (.env pruefen).")
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip("/")
        self.qis_base = self.base_url + "/qisserver"
        self.icms_url = icms_url.rstrip("/")
        self.node_id = node_id
        self.user_agent = user_agent
        self.timeout = timeout

    @classmethod
    def from_env(cls, env_path: str | os.PathLike | None = None) -> HISinOneClient:
        load_env(env_path)
        settings = {param: os.environ.get(var, default) for var, param, default in ENV_SETTINGS}
        return cls(**settings)

    @staticmethod
    def find_ajax_token(html: str) -> str:
        for match in re.finditer(r"<input\b[^>]*>", html):
            if "ajax-token" in match.group(0):
                value = re.search(r'value="([^"]*)"', match.group(0))
                if value:
                    return value.group(1)
        return ""

    def new_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        return session

    def login(
        self, session: requests.Session, pause: Callable[[], None] = _no_pause
    ) -> requests.Response:
        """Login im modernen HISinOne: Startseite (ajax-token + Cookie), dann
        Formular absenden. pause() laeuft vor jedem Schritt (Explorer: Pacer).
        Falsche Zugangsdaten -> HISinOneAuthError."""
        pause()
        start = session.get(self.qis_base + START_PAGE, timeout=self.timeout)
        pause()
        response = session.post(
            self.qis_base + LOGIN_ACTION,
            data=self._login_form(start.text),
            headers={"Origin": self.base_url, "Referer": start.url},
            timeout=self.timeout,
        )
        if "abmelden" not in response.text.lower():
            raise HISinOneAuthError("Login fehlgeschlagen (Zugangsdaten falsch/abgelaufen?).")
        return response

    def _login_form(self, start_html: str) -> dict[str, str]:
        # Feldnamen asdf/fdsa sind so im HISinOne-Formular
        token = self.find_ajax_token(start_html)
        return {"userInfo": "", "ajax-token": token, "asdf": self.username,
                "fdsa": self.password, "submit": ""}  # fmt: skip

    def _fetch_once(self) -> str:
        # Nur EIN SSO-Handoff pro Login: schnelles Nachfassen verwirrt die
        # QIS-Session eher. Wiederholt wird aussen mit frischer Session.
        session = self.new_session()
        self.login(session)
        return QisNotenspiegel(self, session).fetch()

    def fetch_notenspiegel_html(self, attempts: int = 3) -> str:
        """Bis zu `attempts` Versuche, jeder mit frischer Session + Login und
        wachsender Pause dazwischen. Der QIS-Notenspiegel ist sporadisch nicht
        erreichbar (liefert dann eine leere/Gast-Seite); schnelles Nachfassen
        hilft dann wenig, mit etwas Abstand meist schon."""
        last: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                return self._fetch_once()
            except HISinOneAuthError:
                raise  # falsche Zugangsdaten -> sofort abbrechen, kein Retry
            except Exception as error:  # noqa: BLE001 - bewusst breit fuer Retry
                last = error
                if attempt < attempts:
                    time.sleep(3 * attempt)  # 3s, 6s, ... Abstand statt Haemmern
        raise HISinOneError(
            f"Notenspiegel konnte nach {attempts} Versuchen nicht geladen werden "
            f"({last}). Das QIS-Portal hat gerade eine leere Seite geliefert - "
            f"das passiert sporadisch. Bitte in ein paar Sekunden erneut starten."
        )

    def get_grades(self, attempts: int = 3) -> dict:
        """Ruft den Notenspiegel ab und gibt ihn als strukturiertes dict zurueck."""
        return parse_notenspiegel(self.fetch_notenspiegel_html(attempts=attempts))
