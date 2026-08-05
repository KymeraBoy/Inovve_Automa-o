"""Orquestra a criação da estrutura e o arquivamento do PDF."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Mapping, Sequence

from config import (
    COMPANY_ROOTS,
    FORMAL_DESTINATION_SUBFOLDER,
    PROCESS_SUBFOLDERS,
    REC_PARENT_FOLDER,
    REQ_PARENT_CANDIDATES,
    THESIS_PREFIX_TO_TYPE,
    USE_FILE_STEM_AS_PROCESS_FOLDER,
)
from finder import MunicipalityFinder
from parser import parse_document_name
from utils import DuplicateTargetError, FileMoveError, PermissionDeniedError


class ThesisOrganizer:
    """Executa o fluxo completo de arquivamento do documento selecionado."""

    def __init__(
        self,
        company_roots: Sequence[Path],
        thesis_prefix_to_type: Mapping[str, str],
        rec_parent_folder: str,
        req_parent_candidates: Sequence[str],
        process_subfolders: Mapping[str, Sequence[str]],
        formal_destination_subfolder: Mapping[str, str],
        use_stem_as_process_folder: bool,
    ) -> None:
        """Configura todas as regras da automação.

        Args:
            company_roots: Raízes das empresas para busca do município.
            thesis_prefix_to_type: Mapeamento de prefixos válidos para tipo.
            rec_parent_folder: Pasta de reclamações dentro do município.
            req_parent_candidates: Pastas alternativas de requerimentos.
            process_subfolders: Estrutura interna por tipo de tese.
            formal_destination_subfolder: Subpasta final onde o PDF deve ser movido.
            use_stem_as_process_folder: Se True, usa nome sem extensão para pasta do processo.
        """
        self.finder = MunicipalityFinder(company_roots)
        self.thesis_prefix_to_type = thesis_prefix_to_type
        self.rec_parent_folder = rec_parent_folder
        self.req_parent_candidates = tuple(req_parent_candidates)
        self.process_subfolders = process_subfolders
        self.formal_destination_subfolder = formal_destination_subfolder
        self.use_stem_as_process_folder = use_stem_as_process_folder

    @classmethod
    def from_default_config(cls) -> "ThesisOrganizer":
        """Cria o organizador com as constantes padrão de configuração."""
        return cls(
            company_roots=COMPANY_ROOTS,
            thesis_prefix_to_type=THESIS_PREFIX_TO_TYPE,
            rec_parent_folder=REC_PARENT_FOLDER,
            req_parent_candidates=REQ_PARENT_CANDIDATES,
            process_subfolders=PROCESS_SUBFOLDERS,
            formal_destination_subfolder=FORMAL_DESTINATION_SUBFOLDER,
            use_stem_as_process_folder=USE_FILE_STEM_AS_PROCESS_FOLDER,
        )

    def organize(self, pdf_path: Path) -> Path:
        """Executa a automação do início ao fim para um único PDF.

        Args:
            pdf_path: Caminho do arquivo PDF selecionado pelo usuário.

        Returns:
            Caminho final do arquivo movido.

        Raises:
            DuplicateTargetError: Quando pasta ou arquivo de destino já existe.
            PermissionDeniedError: Quando há erro de permissão.
            FileMoveError: Quando a movimentação falha por outro motivo.
        """
        parsed = parse_document_name(
            source_path=pdf_path,
            thesis_prefix_to_type=self.thesis_prefix_to_type,
            use_stem_as_process_folder=self.use_stem_as_process_folder,
        )

        municipality_folder = self.finder.find_municipality_folder(parsed.municipality)
        thesis_parent = self.finder.resolve_thesis_parent_folder(
            municipality_folder=municipality_folder,
            thesis_type=parsed.thesis_type,
            rec_parent_folder=self.rec_parent_folder,
            req_parent_candidates=self.req_parent_candidates,
        )

        process_folder = thesis_parent / parsed.process_folder_name
        if process_folder.exists():
            raise DuplicateTargetError(
                "A pasta do processo já existe e não pode ser sobrescrita: "
                f"'{process_folder}'."
            )

        subfolders = tuple(self.process_subfolders[parsed.thesis_type])
        self._create_process_structure(process_folder=process_folder, subfolders=subfolders)

        destination = process_folder / self.formal_destination_subfolder[parsed.thesis_type] / parsed.original_name
        if destination.exists():
            raise DuplicateTargetError(
                "Já existe um arquivo com o mesmo nome no destino final: "
                f"'{destination}'."
            )

        try:
            shutil.move(str(parsed.source_path), str(destination))
        except PermissionError as exc:
            raise PermissionDeniedError(
                "Sem permissão para mover o arquivo. Feche o PDF se estiver aberto e tente novamente."
            ) from exc
        except OSError as exc:
            raise FileMoveError(f"Erro ao mover arquivo para '{destination}': {exc}") from exc

        return destination

    @staticmethod
    def _create_process_structure(process_folder: Path, subfolders: Sequence[str]) -> None:
        """Cria pasta principal do processo e sua estrutura interna.

        Args:
            process_folder: Pasta principal a ser criada.
            subfolders: Subpastas obrigatórias.

        Raises:
            DuplicateTargetError: Se a pasta do processo já existir.
            PermissionDeniedError: Se faltar permissão para criação.
            FileMoveError: Para demais erros de sistema de arquivos.
        """
        try:
            process_folder.mkdir(parents=False, exist_ok=False)
        except FileExistsError as exc:
            raise DuplicateTargetError(
                f"A pasta do processo já existe: '{process_folder}'."
            ) from exc
        except PermissionError as exc:
            raise PermissionDeniedError(
                f"Sem permissão para criar a pasta do processo: '{process_folder}'."
            ) from exc
        except OSError as exc:
            raise FileMoveError(f"Erro ao criar a pasta do processo '{process_folder}': {exc}") from exc

        for folder_name in subfolders:
            subfolder_path = process_folder / folder_name
            try:
                subfolder_path.mkdir(parents=False, exist_ok=False)
            except PermissionError as exc:
                raise PermissionDeniedError(
                    f"Sem permissão para criar a subpasta '{subfolder_path}'."
                ) from exc
            except OSError as exc:
                raise FileMoveError(f"Erro ao criar subpasta '{subfolder_path}': {exc}") from exc
