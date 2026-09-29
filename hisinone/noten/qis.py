"""SSO-Handoff vom modernen HISinOne ins Legacy-QIS und Abruf der
Notenspiegel-Liste (Schritte 2-5 im Docstring von hisinone_noten.py)."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import requests

from .errors import HISinOneError

if TYPE_CHECKING:
    from .client import HISinOneClient

SSO_BRIDGE = (
    "/rds?state=redirect&sso=qis"
    "&myre=state%3Duser%26type%3D8%26topitem%3Dfunctions%26breadCrumbSource%3Dportal"
)
PORTAL = "/rds?state=user&type=8&topitem=functions&breadCrumbSource=portal&chco=y"
POS_MENU = (
    "/rds?state=change&type=1&moduleParameter=studyPOSMenu"
    "&nextdir=change&next=menu.vm&subdir=applications&xml=menu&purge=y"
    "&navigationPosition=functions%2CstudyPOSMenu&breadcrumb=studyPOSMenu"
    "&topitem=functions&subitem=studyPOSMenu"
)
NOTENSPIEGEL = "/rds?state=notenspiegelStudent&nextdir=qispos/notenspiegel/student"


class QisNotenspiegel:
    """Ein Abruf mit einer Session, die im modernen HISinOne eingeloggt ist."""

    def __init__(self, client: HISinOneClient, session: requests.Session):
        self.client = client
        self.session = session
        self.icms = client.icms_url

    def fetch(self) -> str:
        """HTML der Notenspiegel-Liste."""
        self._redeem_token(self._sso_token())
        asi = self._find_asi()
        return self._fetch_list(asi)

    def _get(self, url: str, referer: str, **kwargs) -> requests.Response:
        return self.session.get(
            url, timeout=self.client.timeout, headers={"Referer": referer}, **kwargs
        )

    def _sso_token(self) -> str:
        """SSO-Bruecke: der Location-Header enthaelt einen Einmal-Token."""
        bridge = self.session.get(
            self.client.qis_base + SSO_BRIDGE, timeout=self.client.timeout, allow_redirects=False
        )
        token = re.search(r"token=([^&]+)", bridge.headers.get("Location", ""))
        if not token:
            raise HISinOneError(f"SSO-Bruecke lieferte keinen Token (HTTP {bridge.status_code}).")
        return token.group(1)

    def _redeem_token(self, token: str) -> None:
        # Nur den Token uebernehmen, nicht den re=-Anhang aus dem Location-
        # Header (doppeltes type=8 wuerde den Token-Login aushebeln)
        home = f"{self.client.base_url}/"
        self._get(f"{self.icms}/rds?state=user&type=1&token={token}", home)

    def _find_asi(self) -> str:
        """Anwendungs-Session-Id aus Portal + POS-Menue."""
        home = f"{self.client.base_url}/"
        portal = self._get(self.icms + PORTAL, home)
        menu = self._get(self.icms + POS_MENU, self.icms + PORTAL)
        text = portal.text + menu.text
        match = re.search(
            r"state=notenspiegelStudent[^\"']*asi=([0-9A-Za-z]{6,})", text
        ) or re.search(r"asi=([0-9A-Za-z]{6,})", text)
        if not match:
            raise HISinOneError("Keine asi nach SSO-Login (Token-Einloesung fehlgeschlagen?).")
        return match.group(1)

    def _fetch_list(self, asi: str) -> str:
        # Baum zuerst initialisieren, sonst liefert die Liste leer
        tree_url = (
            f"{self.icms}{NOTENSPIEGEL}&next=tree.vm&menuid=notenspiegelStudent"
            f"&breadcrumb=notenspiegel&breadCrumbSource=menu&asi={asi}"
        )
        self._get(tree_url, self.icms + PORTAL)
        page = self._get(
            f"{self.icms}{NOTENSPIEGEL}&next=list.vm&createInfos=Y&struct=auswahlBaum"
            f"&nodeID={self.client.node_id}&expand=0&asi={asi}",
            f"{self.icms}/rds?state=notenspiegelStudent&next=tree.vm&asi={asi}",
        )
        page.encoding = "utf-8"  # QIS-Seite ist UTF-8 (Umlaute in der Legende)
        lower = page.text.lower()
        if "notenspiegel" in lower or "<table" in lower:
            return page.text
        raise HISinOneError("Notenspiegel-Seite unerwartet leer/ungueltig.")
