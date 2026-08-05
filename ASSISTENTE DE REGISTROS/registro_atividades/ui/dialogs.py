"""Diálogos da interface para edição de configurações."""

from __future__ import annotations

from tkinter import Toplevel, ttk, messagebox

from config import AppConfig
from pomodoro.settings import PomodoroSettings


class SettingsDialog(Toplevel):
    """Janela modal para ajustes de monitoramento e Pomodoro."""

    def __init__(
        self,
        master,
        app_config: AppConfig,
        pomodoro_settings: PomodoroSettings,
    ) -> None:
        super().__init__(master)
        self.title("Configurações")
        self.resizable(False, False)
        self.result: tuple[AppConfig, PomodoroSettings] | None = None

        self.var_interval = ttk.Entry(self)
        self.var_interval.insert(0, str(app_config.monitor_interval_seconds))

        self.var_focus = ttk.Entry(self)
        self.var_focus.insert(0, str(pomodoro_settings.focus_minutes))

        self.var_short = ttk.Entry(self)
        self.var_short.insert(0, str(pomodoro_settings.short_break_minutes))

        self.var_long = ttk.Entry(self)
        self.var_long.insert(0, str(pomodoro_settings.long_break_minutes))

        self.var_long_every = ttk.Entry(self)
        self.var_long_every.insert(0, str(pomodoro_settings.long_break_every))

        form = ttk.Frame(self, padding=12)
        form.pack(fill="both", expand=True)

        fields = [
            ("Intervalo monitor (s)", self.var_interval),
            ("Foco (min)", self.var_focus),
            ("Pausa curta (min)", self.var_short),
            ("Pausa longa (min)", self.var_long),
            ("Pausa longa a cada", self.var_long_every),
        ]

        for row, (label, widget) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=4, padx=(0, 8))
            widget.grid(row=row, column=1, sticky="ew", pady=4)

        btns = ttk.Frame(form)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=(12, 0), sticky="e")

        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Salvar", command=self._save).pack(side="right")

        form.columnconfigure(1, weight=1)

        self.transient(master)
        self.grab_set()

    def _save(self) -> None:
        try:
            interval = max(5, int(self.var_interval.get().strip()))
            focus = max(1, int(self.var_focus.get().strip()))
            short_break = max(1, int(self.var_short.get().strip()))
            long_break = max(1, int(self.var_long.get().strip()))
            long_every = max(1, int(self.var_long_every.get().strip()))
        except ValueError:
            messagebox.showerror("Erro", "Informe apenas números inteiros válidos.")
            return

        app_cfg = AppConfig(
            records_root="registros_diarios",
            monitor_interval_seconds=interval,
            open_notepad_on_start=True,
        )
        pomodoro_cfg = PomodoroSettings(
            focus_minutes=focus,
            short_break_minutes=short_break,
            long_break_minutes=long_break,
            long_break_every=long_every,
        )

        self.result = (app_cfg, pomodoro_cfg)
        self.destroy()
