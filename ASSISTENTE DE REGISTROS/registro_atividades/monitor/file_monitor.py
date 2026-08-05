"""Monitor de arquivo diário com detecção inteligente de mudanças."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import logging

from monitor.parser import get_new_activity_buffer, parse_sections
from monitor.writer import process_document_content
from utils.datetime_utils import now_hhmm
from utils.file_utils import read_text_snapshot, sha256_text, write_text_if_changed


@dataclass(slots=True)
class MonitorOutcome:
    """Resultado de uma rodada de verificação."""

    processed: bool
    message: str


class ActivityFileMonitor:
    """Monitora arquivo e processa apenas o buffer de NOVA ATIVIDADE."""

    def __init__(self, file_path: Path, logger: logging.Logger | None = None) -> None:
        self.file_path = file_path
        self.logger = logger or logging.getLogger("registro_atividades")
        self._last_mtime_ns: int | None = None
        self._last_new_activity_hash: str = ""

    def _compute_buffer_hash(self, content: str) -> str:
        parsed = parse_sections(content)
        pending = get_new_activity_buffer(parsed)
        return sha256_text(pending)

    def prime(self) -> None:
        """Inicializa estado interno sem processar conteúdo."""
        if not self.file_path.exists():
            return

        stat = self.file_path.stat()
        snapshot = read_text_snapshot(self.file_path)
        self._last_mtime_ns = stat.st_mtime_ns
        try:
            self._last_new_activity_hash = self._compute_buffer_hash(snapshot.content)
        except Exception as exc:
            self.logger.warning("Falha ao inicializar hash da NOVA ATIVIDADE: %s", exc)

    def check_once(self) -> MonitorOutcome:
        """Executa uma varredura única e processa nova atividade quando existir."""
        if not self.file_path.exists():
            return MonitorOutcome(False, "Arquivo não encontrado.")

        stat = self.file_path.stat()
        mtime = stat.st_mtime_ns
        if self._last_mtime_ns is not None and mtime == self._last_mtime_ns:
            return MonitorOutcome(False, "Sem alteração de arquivo.")

        snapshot = read_text_snapshot(self.file_path)
        self._last_mtime_ns = mtime

        try:
            new_hash = self._compute_buffer_hash(snapshot.content)
        except Exception as exc:
            self.logger.error("Estrutura do arquivo inválida: %s", exc)
            return MonitorOutcome(False, f"Estrutura inválida: {exc}")

        if new_hash == self._last_new_activity_hash:
            return MonitorOutcome(False, "Alteração irrelevante para NOVA ATIVIDADE.")

        result = process_document_content(snapshot.content, now_hhmm())
        if not result.changed:
            self._last_new_activity_hash = new_hash
            return MonitorOutcome(False, "NOVA ATIVIDADE vazia.")

        changed = write_text_if_changed(
            self.file_path,
            result.new_content,
            newline=snapshot.newline,
        )
        if changed:
            final_snapshot = read_text_snapshot(self.file_path)
            self._last_new_activity_hash = self._compute_buffer_hash(final_snapshot.content)
            self._last_mtime_ns = self.file_path.stat().st_mtime_ns
            self.logger.info("Nova atividade registrada: %s", result.captured_activity.splitlines()[0][:80])
            return MonitorOutcome(True, "Nova atividade processada com sucesso.")

        self._last_new_activity_hash = new_hash
        return MonitorOutcome(False, "Nenhuma escrita necessária.")


def build_monitor_callback(
    monitor: ActivityFileMonitor,
    on_status: Callable[[MonitorOutcome], None],
) -> Callable[[], None]:
    """Empacota monitor/check em callback simples para watcher."""

    def _runner() -> None:
        outcome = monitor.check_once()
        on_status(outcome)

    return _runner
