"""Parser do nome de arquivo para extrair metadados da tese."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from config import DocumentType
from utils import InvalidPdfNameError, normalize_token


_FILENAME_PATTERN = re.compile(
    r"^(?P<prefix>[^-]+)-(?P<code>[^-]+)-(?P<municipality>[^-]+)-.+$",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedDocument:
    """Dados extraídos a partir do nome padronizado do PDF."""

    source_path: Path
    original_name: str
    process_folder_name: str
    thesis_type: DocumentType
    code: str
    municipality: str


def parse_document_name(
    source_path: Path,
    thesis_prefix_to_type: Mapping[str, DocumentType],
    use_stem_as_process_folder: bool = True,
) -> ParsedDocument:
    """Interpreta o nome do arquivo e devolve metadados estruturados.

    Espera-se o padrão: TIPO-CODIGO-MUNICIPIO-... .pdf

    Args:
        source_path: Caminho do PDF selecionado.
        thesis_prefix_to_type: Mapeamento de prefixos válidos para tipo da tese.
        use_stem_as_process_folder: Define se a pasta do processo usa o nome sem extensão.

    Returns:
        Metadados extraídos do arquivo.

    Raises:
        InvalidPdfNameError: Quando o arquivo não for PDF, não seguir o padrão ou
            usar um prefixo não reconhecido.
    """
    if source_path.suffix.lower() != ".pdf":
        raise InvalidPdfNameError("O arquivo selecionado não é um PDF.")

    stem = source_path.stem
    match = _FILENAME_PATTERN.match(stem)
    if not match:
        raise InvalidPdfNameError(
            "Nome inválido. Use o padrão TIPO-CODIGO-MUNICIPIO-... (ex.: REC-001_2026-CIDADE-...)."
        )

    raw_prefix = match.group("prefix").strip()
    normalized_prefix = normalize_token(raw_prefix)
    thesis_type = thesis_prefix_to_type.get(normalized_prefix)
    if thesis_type is None:
        accepted = ", ".join(sorted(thesis_prefix_to_type.keys()))
        raise InvalidPdfNameError(
            f"Tipo de tese não reconhecido no nome do arquivo: '{raw_prefix}'. Prefixos aceitos: {accepted}."
        )

    code = match.group("code").strip()
    municipality = match.group("municipality").strip()
    process_folder_name = stem if use_stem_as_process_folder else source_path.name

    return ParsedDocument(
        source_path=source_path,
        original_name=source_path.name,
        process_folder_name=process_folder_name,
        thesis_type=thesis_type,
        code=code,
        municipality=municipality,
    )
