"""Widget visual do Pomodoro na janela principal."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class PomodoroWidget(ttk.LabelFrame):
    """Bloco de interface para controle do temporizador Pomodoro."""

    def __init__(self, master, on_start, on_pause, on_reset, on_next, on_settings):
        super().__init__(master, text="Pomodoro", padding=10)

        self.var_phase = tk.StringVar(value="Fase: foco")
        self.var_remaining = tk.StringVar(value="Tempo restante: 25:00")

        ttk.Label(self, textvariable=self.var_phase).grid(row=0, column=0, columnspan=5, sticky="w")
        ttk.Label(self, textvariable=self.var_remaining, font=("Segoe UI", 16, "bold")).grid(
            row=1, column=0, columnspan=5, sticky="w", pady=(4, 10)
        )

        ttk.Button(self, text="Iniciar", command=on_start).grid(row=2, column=0, padx=4)
        ttk.Button(self, text="Pausar", command=on_pause).grid(row=2, column=1, padx=4)
        ttk.Button(self, text="Reiniciar", command=on_reset).grid(row=2, column=2, padx=4)
        ttk.Button(self, text="Próximo ciclo", command=on_next).grid(row=2, column=3, padx=4)
        ttk.Button(self, text="Configurações", command=on_settings).grid(row=2, column=4, padx=4)

    def update_display(self, phase: str, mmss: str) -> None:
        """Atualiza fase e tempo do Pomodoro no widget."""
        self.var_phase.set(f"Fase: {phase}")
        self.var_remaining.set(f"Tempo restante: {mmss}")
