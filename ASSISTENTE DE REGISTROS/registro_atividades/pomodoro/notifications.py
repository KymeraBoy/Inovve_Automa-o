"""Notificações de desktop para ciclos do Pomodoro."""

from __future__ import annotations


def send_notification(title: str, message: str) -> None:
    """Exibe notificação no Windows com fallback silencioso."""
    try:
        from plyer import notification

        notification.notify(
            title=title,
            message=message,
            app_name="Registro de Atividades",
            timeout=8,
        )
        return
    except Exception:
        pass

    try:
        from tkinter import Tk, messagebox

        root = Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except Exception:
        pass
