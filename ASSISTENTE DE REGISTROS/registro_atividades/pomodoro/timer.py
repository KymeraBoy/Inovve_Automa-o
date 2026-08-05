"""Motor de temporização Pomodoro."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Event, Thread
from time import monotonic
from typing import Callable
import json

from constants import DEFAULT_HISTORY_FILE
from pomodoro.notifications import send_notification
from pomodoro.settings import PomodoroSettings
from pomodoro.sounds import play_cycle_end_sound


@dataclass(slots=True)
class PomodoroState:
    """Estado atual do temporizador."""

    phase: str = "foco"
    is_running: bool = False
    remaining_seconds: int = 25 * 60
    completed_focus_cycles: int = 0


class PomodoroTimer:
    """Timer Pomodoro em thread, com callbacks de atualização."""

    def __init__(
        self,
        settings: PomodoroSettings,
        on_tick: Callable[[PomodoroState], None] | None = None,
        on_phase_change: Callable[[PomodoroState], None] | None = None,
        history_path: Path = DEFAULT_HISTORY_FILE,
    ) -> None:
        self.settings = settings
        self.on_tick = on_tick
        self.on_phase_change = on_phase_change
        self.history_path = history_path

        self.state = PomodoroState(remaining_seconds=settings.focus_minutes * 60)
        self._stop_event = Event()
        self._pause_event = Event()
        self._thread: Thread | None = None
        self._target_end = 0.0

    def start(self) -> None:
        if self.state.is_running:
            return

        self.state.is_running = True
        self._pause_event.clear()
        self._target_end = monotonic() + self.state.remaining_seconds

        if self._thread is None or not self._thread.is_alive():
            self._stop_event.clear()
            self._thread = Thread(target=self._run_loop, name="PomodoroTimer", daemon=True)
            self._thread.start()

    def pause(self) -> None:
        if not self.state.is_running:
            return
        self.state.is_running = False
        self._pause_event.set()

    def reset(self) -> None:
        self.pause()
        self.state.phase = "foco"
        self.state.remaining_seconds = self.settings.focus_minutes * 60
        self._emit_tick()

    def next_cycle(self) -> None:
        """Avança imediatamente para a próxima fase."""
        self._finish_current_phase(force_next=True)

    def update_settings(self, settings: PomodoroSettings) -> None:
        """Atualiza configuração e reinicia contador para foco."""
        self.settings = settings
        self.reset()

    def stop(self) -> None:
        self._stop_event.set()
        self.pause()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            if not self.state.is_running:
                self._stop_event.wait(0.2)
                continue

            remaining = int(round(self._target_end - monotonic()))
            if remaining <= 0:
                self.state.remaining_seconds = 0
                self._emit_tick()
                self._finish_current_phase(force_next=False)
                continue

            self.state.remaining_seconds = remaining
            self._emit_tick()
            self._stop_event.wait(1)

    def _finish_current_phase(self, force_next: bool) -> None:
        if self.state.phase == "foco":
            self.state.completed_focus_cycles += 1
            next_phase = self._break_phase_name()
            title = "Pomodoro"
            msg = "Tempo de foco concluído. Hora da pausa."
        else:
            next_phase = "foco"
            title = "Pomodoro"
            msg = "Pausa concluída. Volte ao foco."

        if not force_next:
            play_cycle_end_sound()
            send_notification(title, msg)
            self._append_history_entry(msg)

        self.state.phase = next_phase
        self.state.remaining_seconds = self._phase_seconds(next_phase)

        if self.state.is_running:
            self._target_end = monotonic() + self.state.remaining_seconds

        self._emit_tick()
        if self.on_phase_change:
            self.on_phase_change(self.state)

    def _break_phase_name(self) -> str:
        if self.state.completed_focus_cycles % max(1, self.settings.long_break_every) == 0:
            return "pausa longa"
        return "pausa curta"

    def _phase_seconds(self, phase: str) -> int:
        if phase == "foco":
            return self.settings.focus_minutes * 60
        if phase == "pausa curta":
            return self.settings.short_break_minutes * 60
        return self.settings.long_break_minutes * 60

    def _emit_tick(self) -> None:
        if self.on_tick:
            self.on_tick(self.state)

    def _append_history_entry(self, message: str) -> None:
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"events": []}

        if self.history_path.exists():
            try:
                payload = json.loads(self.history_path.read_text(encoding="utf-8"))
                if "events" not in payload or not isinstance(payload["events"], list):
                    payload = {"events": []}
            except Exception:
                payload = {"events": []}

        payload["events"].append(
            {
                "phase": self.state.phase,
                "message": message,
            }
        )
        self.history_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
