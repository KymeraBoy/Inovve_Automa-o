"""Janela principal da aplicação de registro de atividades."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from queue import Empty, Queue
from pathlib import Path

from config import AppConfig, save_app_config
from monitor.file_monitor import ActivityFileMonitor, MonitorOutcome, build_monitor_callback
from monitor.watcher import PollingWatcher
from pomodoro.settings import PomodoroSettings, save_pomodoro_settings
from pomodoro.timer import PomodoroState, PomodoroTimer
from ui.dialogs import SettingsDialog
from ui.pomodoro_widget import PomodoroWidget
from utils.datetime_utils import now_human


class MainWindow:
    """Controlador da interface principal."""

    def __init__(
        self,
        app_config: AppConfig,
        pomodoro_settings: PomodoroSettings,
        registro_path: Path,
        monitor: ActivityFileMonitor,
    ) -> None:
        self.app_config = app_config
        self.pomodoro_settings = pomodoro_settings
        self.registro_path = registro_path
        self.monitor = monitor

        self.root = tk.Tk()
        self.root.title("Assistente de Registros")
        self.root.geometry("820x420")

        self.var_registro = tk.StringVar(value=f"Registro atual: {registro_path.name}")
        self.var_caminho = tk.StringVar(value=f"Caminho monitorado: {registro_path}")
        self.var_status = tk.StringVar(value="Status monitoramento: Ativo")
        self.var_last_check = tk.StringVar(value="Última verificação: -")
        self.var_last_action = tk.StringVar(value="Última ação: aguardando...")

        self.event_queue: Queue[tuple[str, object]] = Queue()

        self.pomodoro = PomodoroTimer(
            settings=pomodoro_settings,
            on_tick=self._on_pomodoro_tick,
            on_phase_change=self._on_pomodoro_phase_change,
        )

        callback = build_monitor_callback(monitor, self._on_monitor_outcome)
        self.watcher = PollingWatcher(app_config.monitor_interval_seconds, callback)

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        info = ttk.LabelFrame(container, text="Registro", padding=10)
        info.pack(fill="x")

        ttk.Label(info, textvariable=self.var_registro).pack(anchor="w")
        ttk.Label(info, textvariable=self.var_caminho).pack(anchor="w", pady=(2, 0))
        ttk.Label(info, textvariable=self.var_status).pack(anchor="w", pady=(2, 0))
        ttk.Label(info, textvariable=self.var_last_check).pack(anchor="w", pady=(2, 0))
        ttk.Label(info, textvariable=self.var_last_action).pack(anchor="w", pady=(2, 0))

        self.pomodoro_widget = PomodoroWidget(
            container,
            on_start=self.pomodoro.start,
            on_pause=self.pomodoro.pause,
            on_reset=self.pomodoro.reset,
            on_next=self.pomodoro.next_cycle,
            on_settings=self._open_settings,
        )
        self.pomodoro_widget.pack(fill="x", pady=(12, 0))

    def run(self) -> None:
        """Inicia monitoramento e loop da interface."""
        self.monitor.prime()
        self.watcher.start()
        self._pump_queue()
        self.root.mainloop()

    def _pump_queue(self) -> None:
        while True:
            try:
                kind, payload = self.event_queue.get_nowait()
            except Empty:
                break

            if kind == "monitor":
                outcome: MonitorOutcome = payload  # type: ignore[assignment]
                self.var_last_check.set(f"Última verificação: {now_human()}")
                self.var_last_action.set(f"Última ação: {outcome.message}")
            elif kind == "pomodoro":
                state: PomodoroState = payload  # type: ignore[assignment]
                mm = state.remaining_seconds // 60
                ss = state.remaining_seconds % 60
                self.pomodoro_widget.update_display(state.phase, f"{mm:02d}:{ss:02d}")

        self.root.after(250, self._pump_queue)

    def _on_monitor_outcome(self, outcome: MonitorOutcome) -> None:
        self.event_queue.put(("monitor", outcome))

    def _on_pomodoro_tick(self, state: PomodoroState) -> None:
        self.event_queue.put(("pomodoro", state))

    def _on_pomodoro_phase_change(self, state: PomodoroState) -> None:
        self.event_queue.put(("pomodoro", state))

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.root, self.app_config, self.pomodoro_settings)
        self.root.wait_window(dialog)
        if not dialog.result:
            return

        new_app_config, new_pomodoro_settings = dialog.result
        new_app_config.records_root = self.app_config.records_root
        new_app_config.open_notepad_on_start = self.app_config.open_notepad_on_start

        self.app_config = new_app_config
        self.pomodoro_settings = new_pomodoro_settings

        save_app_config(self.app_config)
        save_pomodoro_settings(self.pomodoro_settings)

        self.watcher.stop()
        self.watcher = PollingWatcher(
            self.app_config.monitor_interval_seconds,
            build_monitor_callback(self.monitor, self._on_monitor_outcome),
        )
        self.watcher.start()

        self.pomodoro.update_settings(self.pomodoro_settings)

    def _on_close(self) -> None:
        self.watcher.stop()
        self.pomodoro.stop()
        self.root.destroy()
