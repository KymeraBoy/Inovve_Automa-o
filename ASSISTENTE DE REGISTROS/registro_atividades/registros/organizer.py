"""Organização de pastas de registros por ano e mês."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(slots=True)
class RecordPaths:
    """Caminhos relevantes para o registro diário."""

    root: Path
    year_dir: Path
    month_dir: Path
    day_file: Path


def build_record_paths(root: Path, reference_date: date) -> RecordPaths:
    """Monta caminhos no formato root/AAAA/MM para o dia de referência."""
    year_dir = root / reference_date.strftime("%Y")
    month_dir = year_dir / reference_date.strftime("%m")
    day_file = month_dir / f"Registro-{reference_date.strftime('%Y-%m-%d')}.txt"
    return RecordPaths(root=root, year_dir=year_dir, month_dir=month_dir, day_file=day_file)


def ensure_record_dirs(paths: RecordPaths) -> None:
    """Garante existência das pastas necessárias."""
    paths.month_dir.mkdir(parents=True, exist_ok=True)
