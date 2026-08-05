"""Configuração central de logging da aplicação."""

from __future__ import annotations

import logging
from pathlib import Path

from constants import DEFAULT_LOG_FILE


def setup_logger(log_path: Path = DEFAULT_LOG_FILE) -> logging.Logger:
    """Inicializa logger em arquivo e console."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("registro_atividades")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
