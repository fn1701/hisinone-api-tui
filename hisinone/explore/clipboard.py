"""In die Zwischenablage kopieren (wl-copy/xclip/xsel, sonst OSC 52)."""

import base64
import shutil
import subprocess
import sys

CLIPBOARD_TOOLS = (["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-bi"])


def copy_external(text: str) -> str | None:
    """Kopiert per externem Tool; liefert den Tool-Namen oder None."""
    for command in CLIPBOARD_TOOLS:
        if shutil.which(command[0]) and _run(command, text):
            return command[0]
    return None


def _run(command: list[str], text: str) -> bool:
    try:
        subprocess.run(command, input=text.encode(), check=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def copy_to_clipboard(text: str) -> str:
    """Kopiert in die Zwischenablage; ohne Tool per OSC 52 über das Terminal
    (tmux: set -g set-clipboard on). Liefert, womit kopiert wurde."""
    tool = copy_external(text)
    if tool:
        return tool
    sys.stdout.write(f"\033]52;c;{base64.b64encode(text.encode()).decode()}\a")
    sys.stdout.flush()
    return "OSC 52"
