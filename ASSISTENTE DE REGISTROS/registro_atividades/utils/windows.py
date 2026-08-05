"""Funções específicas do Windows."""

from __future__ import annotations

from pathlib import Path
import subprocess


def open_file_in_notepad(path: Path) -> None:
    """Abre arquivo no Bloco de Notas sem bloquear o processo principal."""
    subprocess.Popen(["notepad.exe", str(path)], shell=False)
