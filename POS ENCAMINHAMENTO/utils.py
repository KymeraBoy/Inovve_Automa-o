"""Utilitários e exceções da automação de arquivamento."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


class OrganizationError(Exception):
    """Exceção base para erros amigáveis da automação."""


class InvalidPdfNameError(OrganizationError):
    """Nome do PDF não segue o padrão esperado."""


class MunicipalityNotFoundError(OrganizationError):
    """Município não encontrado em nenhuma empresa configurada."""


class AmbiguousMunicipalityError(OrganizationError):
    """Mesmo município encontrado em mais de um local possível."""


class FolderStructureError(OrganizationError):
    """Estrutura de pastas obrigatória está ausente."""


class DuplicateTargetError(OrganizationError):
    """Pasta ou arquivo de destino já existe."""


class FileMoveError(OrganizationError):
    """Falha ao mover o arquivo para o destino final."""


class PermissionDeniedError(OrganizationError):
    """Falha por falta de permissão de acesso ao sistema de arquivos."""


def normalize_token(value: str) -> str:
    """Normaliza texto para comparação tolerante a acentos/separadores.

    Args:
        value: Texto original.

    Returns:
        Texto em caixa alta, sem acentos e sem separadores comuns.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    compact = re.sub(r"[\s_\-]+", "", without_accents)
    return compact.upper()


def format_path_list(paths: list[Path]) -> str:
    """Formata caminhos em múltiplas linhas para mensagens amigáveis.

    Args:
        paths: Lista de caminhos.

    Returns:
        Texto com um item por linha, prefixado com "-".
    """
    return "\n".join(f"- {path}" for path in paths)
