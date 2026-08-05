from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Centraliza caminhos e configuracoes da aplicacao operacional."""

    base_dir: Path
    municipios_dir: Path
    empresas_dir: Path
    rec_dir: Path
    req_dir: Path
    ofi_dir: Path
    saida_dir: Path
    fila_arquivo: Path


ROOT_DIR = Path(__file__).resolve().parents[2]
OPERACIONAL_DIR = ROOT_DIR / "OPERACIONAL"

CONFIG = AppConfig(
    base_dir=ROOT_DIR,
    municipios_dir=ROOT_DIR / "MUNICIPIOS",
    empresas_dir=ROOT_DIR / "EMPRESAS",
    rec_dir=ROOT_DIR / "REC",
    req_dir=ROOT_DIR / "REQ",
    ofi_dir=ROOT_DIR / "OFI",
    saida_dir=ROOT_DIR / "SAÍDA",
    fila_arquivo=OPERACIONAL_DIR / "fila_documentos.json",
)
