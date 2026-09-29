"""Config-Datei ~/.config/hisinone-explore/config.json lesen/schreiben."""

import json
import os
from pathlib import Path

CONFIG_PATH = (
    Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    / "hisinone-explore"
    / "config.json"
)
AUTOSAVE_SECONDS = 100


def load_config(path: Path = CONFIG_PATH) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        print(f"Config {path} nicht lesbar ({error}), nutze Standardwerte")
        return {}


def write_config(config: dict, path: Path = CONFIG_PATH) -> None:
    """Atomar schreiben (tmp + rename), nur fuer den Benutzer lesbar
    (Filter koennen Modulnamen/Noten enthalten)."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
