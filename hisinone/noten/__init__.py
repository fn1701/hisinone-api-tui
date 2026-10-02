"""Notenspiegel einer HISinOne/QIS-Installation als dict/JSON.

Öffentliche API (auch über das Modul hisinone_noten erreichbar):
    HISinOneClient, HISinOneError, HISinOneAuthError, parse_notenspiegel, load_env
"""

from .client import HISinOneClient
from .env import load_env
from .errors import HISinOneAuthError, HISinOneError
from .parser import parse_notenspiegel

__all__ = [
    "HISinOneAuthError",
    "HISinOneClient",
    "HISinOneError",
    "load_env",
    "parse_notenspiegel",
]
