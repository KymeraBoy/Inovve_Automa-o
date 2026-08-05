"""Geração do arquivo diário de registro."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from registros.organizer import RecordPaths, build_record_paths, ensure_record_dirs
from registros.templates import build_daily_template


@dataclass(slots=True)
class DailyRecordResult:
    """Resultado da preparação do registro diário."""

    path: Path
    created: bool
    paths: RecordPaths


def ensure_daily_record(records_root: Path, reference_date: date | None = None) -> DailyRecordResult:
    """Cria o arquivo diário caso não exista e retorna metadados da operação."""
    reference_date = reference_date or date.today()
    paths = build_record_paths(records_root, reference_date)
    ensure_record_dirs(paths)

    created = False
    if not paths.day_file.exists():
        paths.day_file.write_text(build_daily_template(reference_date), encoding="utf-8")
        created = True

    return DailyRecordResult(path=paths.day_file, created=created, paths=paths)
