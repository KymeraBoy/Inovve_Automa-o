"""Configurações centrais da automação de arquivamento de teses.

Ajuste os caminhos em COMPANY_ROOTS para refletir as duas estruturas reais
existentes no seu computador.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final, Literal

DocumentType = Literal["REC", "REQ"]

# Caminhos fixos das duas estruturas principais (empresas).
# Edite para os caminhos reais no seu computador.
COMPANY_ROOTS: Final[tuple[Path, ...]] = (
    Path(r"C:\Users\Usuário 1\OneDrive\PASTA ENERGIA 1\PARCEIROS\Municípios Thamires e Ruda"),
    Path(r"C:\Users\Usuário 1\OneDrive\PASTA ENERGIA 1\Municípios HLA - Outros Estados"),
)

# Prefixos aceitos no nome do arquivo e o tipo normalizado de tese.
THESIS_PREFIX_TO_TYPE: Final[dict[str, DocumentType]] = {
    "REC": "REC",
    "REQ": "REQ",
    "PET": "REQ",
    "RQS": "REQ",
    "REQUISICAO": "REQ",
    "REQUISIÇÃO": "REQ",
}

# Pasta esperada para reclamações dentro de cada município.
REC_PARENT_FOLDER: Final[str] = "RECLAMAÇÕES"

# Para requerimentos, a automação escolhe a primeira pasta existente nesta ordem.
REQ_PARENT_CANDIDATES: Final[tuple[str, ...]] = (
    "REQUERIMENTOS",
    "PETIÇÕES",
    "REQUISIÇÕES",
)

# Estrutura interna para cada novo processo.
PROCESS_SUBFOLDERS: Final[dict[DocumentType, tuple[str, ...]]] = {
    "REC": (
        "ANEEL",
        "PAGAMENTO",
        "DOCUMENTOS RECEBIDOS",
        "RECLAMAÇÃO FORMAL",
        "E-MAILS",
    ),
    "REQ": (
        "ANEEL",
        "DOCUMENTOS RECEBIDOS",
        "REQUERIMENTO FORMAL",
        "E-MAILS",
    ),
}

# Pasta de destino do PDF em cada tipo de tese.
FORMAL_DESTINATION_SUBFOLDER: Final[dict[DocumentType, str]] = {
    "REC": "RECLAMAÇÃO FORMAL",
    "REQ": "REQUERIMENTO FORMAL",
}

# Nome da pasta do processo: por padrão sem a extensão ".pdf".
USE_FILE_STEM_AS_PROCESS_FOLDER: Final[bool] = True

# Janela de seleção de arquivo.
FILE_DIALOG_TITLE: Final[str] = "Selecione o PDF da tese"
FILE_DIALOG_FILTERS: Final[list[tuple[str, str]]] = [
    ("Arquivos PDF", "*.pdf"),
    ("Todos os arquivos", "*.*"),
]
