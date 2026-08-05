"""Utilitários de data e hora."""

from __future__ import annotations

from datetime import datetime


def now_hhmm() -> str:
    """Retorna horário atual no formato HH:MM."""
    return datetime.now().strftime("%H:%M")


def now_human() -> str:
    """Retorna data/hora legível para exibição na interface."""
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")
