"""Ausnahmen der Bibliothek."""


class HISinOneError(RuntimeError):
    """Fehler beim Login oder Abruf des Notenspiegels."""


class HISinOneAuthError(HISinOneError):
    """Zugangsdaten falsch/abgelaufen. Wird NICHT wiederholt (Retry sinnlos)."""
