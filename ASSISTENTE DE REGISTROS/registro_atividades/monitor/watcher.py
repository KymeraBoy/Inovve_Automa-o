"""Watcher por polling leve para execução contínua em background."""

from __future__ import annotations

from threading import Event, Thread
from typing import Callable
import logging


class PollingWatcher:
    """Executa callback periódico com baixo consumo de CPU."""

    def __init__(
        self,
        interval_seconds: int,
        callback: Callable[[], None],
        logger: logging.Logger | None = None,
    ) -> None:
        self.interval_seconds = max(5, interval_seconds)
        self.callback = callback
        self.logger = logger or logging.getLogger("registro_atividades")
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        """Inicia thread de monitoramento, se ainda não estiver ativa."""
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._loop, name="PollingWatcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Sinaliza encerramento e aguarda fim da thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.callback()
            except Exception as exc:
                self.logger.exception("Erro no watcher: %s", exc)
            self._stop_event.wait(self.interval_seconds)
