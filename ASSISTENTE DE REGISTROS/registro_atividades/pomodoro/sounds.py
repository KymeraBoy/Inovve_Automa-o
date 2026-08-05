"""Sons do Pomodoro."""

from __future__ import annotations


def play_cycle_end_sound() -> None:
    """Emite som simples ao concluir ciclo."""
    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        # Mantém silêncio quando áudio não estiver disponível.
        pass
