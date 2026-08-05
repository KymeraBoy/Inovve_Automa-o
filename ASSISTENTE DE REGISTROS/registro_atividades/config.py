"""Carregamento e persistência de configurações da aplicação."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from constants import DEFAULT_CONFIG_FILE, ROOT_DIR


@dataclass(slots=True)
class AppConfig:
    """Configuração principal da aplicação."""

    records_root: str = "registros_diarios"
    monitor_interval_seconds: int = 60
    open_notepad_on_start: bool = True

    def records_root_path(self) -> Path:
        """Retorna o caminho absoluto da pasta base de registros."""
        path = Path(self.records_root)
        if not path.is_absolute():
            path = ROOT_DIR / path
        return path


DEFAULT_CONFIG = AppConfig()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_app_config(path: Path = DEFAULT_CONFIG_FILE) -> AppConfig:
    """Lê a configuração, criando arquivo padrão quando não existir."""
    if not path.exists():
        save_app_config(DEFAULT_CONFIG, path)
        return DEFAULT_CONFIG

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AppConfig(**data)
    except Exception:
        return DEFAULT_CONFIG


def save_app_config(config: AppConfig, path: Path = DEFAULT_CONFIG_FILE) -> None:
    """Salva a configuração principal em JSON UTF-8."""
    _ensure_parent(path)
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
