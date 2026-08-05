"""Ponto de entrada do Assistente de Registros."""

from __future__ import annotations

from config import load_app_config
from monitor.file_monitor import ActivityFileMonitor
from pomodoro.settings import load_pomodoro_settings
from registros.compiler import compile_month_records
from registros.generator import ensure_daily_record
from ui.janela import MainWindow
from utils.logger import setup_logger
from utils.windows import open_file_in_notepad


def main() -> None:
    """Inicializa aplicação, registro diário e interface gráfica."""
    logger = setup_logger()

    app_config = load_app_config()
    pomodoro_settings = load_pomodoro_settings()

    daily = ensure_daily_record(app_config.records_root_path())
    if daily.created:
        consolidated = compile_month_records(daily.paths.month_dir)
        if consolidated:
            logger.info("Consolidado atualizado: %s", consolidated)

    if app_config.open_notepad_on_start:
        try:
            open_file_in_notepad(daily.path)
        except Exception as exc:
            logger.warning("Não foi possível abrir o Bloco de Notas: %s", exc)

    monitor = ActivityFileMonitor(daily.path, logger=logger)

    app = MainWindow(
        app_config=app_config,
        pomodoro_settings=pomodoro_settings,
        registro_path=daily.path,
        monitor=monitor,
    )
    app.run()


if __name__ == "__main__":
    main()
