"""Persistência de configurações do Pomodoro."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from constants import DEFAULT_POMODORO_FILE


@dataclass(slots=True)
class PomodoroSettings:
    """Tempos de ciclo do Pomodoro em minutos."""

    focus_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    long_break_every: int = 4


def load_pomodoro_settings(path: Path = DEFAULT_POMODORO_FILE) -> PomodoroSettings:
    """Carrega ajustes do Pomodoro; cria padrão se necessário."""
    if not path.exists():
        save_pomodoro_settings(PomodoroSettings(), path)
        return PomodoroSettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return PomodoroSettings(**data)
    except Exception:
        return PomodoroSettings()


def save_pomodoro_settings(settings: PomodoroSettings, path: Path = DEFAULT_POMODORO_FILE) -> None:
    """Salva ajustes do Pomodoro em UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
