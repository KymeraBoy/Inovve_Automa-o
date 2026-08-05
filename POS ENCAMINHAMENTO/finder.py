"""Busca de município e resolução da pasta base para arquivamento."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from config import DocumentType
from utils import (
    AmbiguousMunicipalityError,
    FolderStructureError,
    MunicipalityNotFoundError,
    format_path_list,
    normalize_token,
)


class MunicipalityFinder:
    """Localiza municípios dentro de múltiplas estruturas de empresa."""

    def __init__(self, company_roots: Sequence[Path]) -> None:
        """Inicializa o buscador.

        Args:
            company_roots: Raízes das empresas onde os municípios serão procurados.
        """
        self.company_roots = tuple(company_roots)

    def find_municipality_folder(self, municipality_name: str) -> Path:
        """Procura a pasta de município em todas as empresas configuradas.

        Args:
            municipality_name: Município extraído do nome do PDF.

        Returns:
            Caminho da pasta do município.

        Raises:
            FolderStructureError: Se nenhuma raiz de empresa configurada existir.
            MunicipalityNotFoundError: Se o município não for encontrado.
            AmbiguousMunicipalityError: Se houver mais de uma pasta candidata.
        """
        existing_roots = [root for root in self.company_roots if root.exists() and root.is_dir()]
        if not existing_roots:
            configured_roots = format_path_list(list(self.company_roots))
            raise FolderStructureError(
                "Nenhuma pasta raiz de empresa foi encontrada. Ajuste COMPANY_ROOTS em config.py.\n"
                f"Caminhos configurados:\n{configured_roots}"
            )

        expected = normalize_token(municipality_name)
        matches: list[Path] = []

        for root in existing_roots:
            for city_dir in self._iter_municipality_dirs(root):
                if normalize_token(city_dir.name) == expected:
                    matches.append(city_dir)

        if not matches:
            roots_text = format_path_list(existing_roots)
            raise MunicipalityNotFoundError(
                "Município não encontrado nas estruturas configuradas: "
                f"'{municipality_name}'.\nRaízes pesquisadas:\n{roots_text}"
            )

        if len(matches) > 1:
            matches_text = format_path_list(matches)
            raise AmbiguousMunicipalityError(
                "Município encontrado em mais de um local. "
                "Refine a estrutura para evitar ambiguidades:\n"
                f"{matches_text}"
            )

        return matches[0]

    def resolve_thesis_parent_folder(
        self,
        municipality_folder: Path,
        thesis_type: DocumentType,
        rec_parent_folder: str,
        req_parent_candidates: Sequence[str],
    ) -> Path:
        """Determina a subpasta correta de destino por tipo de tese.

        Args:
            municipality_folder: Pasta do município localizado.
            thesis_type: Tipo da tese normalizado (REC ou REQ).
            rec_parent_folder: Pasta obrigatória para reclamações.
            req_parent_candidates: Pastas possíveis para requerimentos.

        Returns:
            Pasta-base onde será criada a pasta do processo.

        Raises:
            FolderStructureError: Se a pasta esperada não existir.
        """
        if thesis_type == "REC":
            rec_folder = municipality_folder / rec_parent_folder
            if rec_folder.exists() and rec_folder.is_dir():
                return rec_folder

            raise FolderStructureError(
                "Pasta obrigatória para Reclamações não encontrada em "
                f"'{municipality_folder}'. Esperado: '{rec_parent_folder}'."
            )

        for candidate in req_parent_candidates:
            candidate_path = municipality_folder / candidate
            if candidate_path.exists() and candidate_path.is_dir():
                return candidate_path

        candidates_text = ", ".join(req_parent_candidates)
        raise FolderStructureError(
            "Nenhuma pasta válida para Requerimento foi encontrada em "
            f"'{municipality_folder}'. Opções aceitas: {candidates_text}."
        )

    @staticmethod
    def _iter_municipality_dirs(root: Path) -> Iterable[Path]:
        """Itera municípios no formato esperado Empresa/Estado/Município.

        Args:
            root: Pasta raiz da empresa.

        Yields:
            Pastas de município encontradas sob cada estado.
        """
        for state_dir in root.iterdir():
            if not state_dir.is_dir():
                continue

            for municipality_dir in state_dir.iterdir():
                if municipality_dir.is_dir():
                    yield municipality_dir
