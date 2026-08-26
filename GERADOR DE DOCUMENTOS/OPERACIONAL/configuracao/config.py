from __future__ import annotations

# Importa o dataclass, que permite criar classes usadas principalmente para armazenar dados de forma organizada.
from dataclasses import dataclass
# Importa Path, uma classe que facilita a criação e manipulação de caminhos de arquivos e pastas.
from pathlib import Path

# @dataclass transforma a classe AppConfig em uma classe própria para armazenar configurações/dados.
# frozen=True significa que, depois que um objeto AppConfig for criado, seus valores não poderão ser alterados.
@dataclass(frozen=True)
class AppConfig:
    """
    Centraliza os caminhos e configurações da aplicação operacional.

    Em vez de espalhar caminhos de pastas pelo projeto inteiro,
    podemos armazená-los todos nesta classe e acessá-los através
    de CONFIG.
    """

    base_dir:       Path
    municipios_dir: Path
    empresas_dir:   Path
    rec_dir:        Path
    req_dir:        Path
    ofi_dir:        Path
    saida_dir:      Path
    fila_arquivo:   Path

# __file__ representa o caminho deste próprio arquivo Python.
# Path(__file__) transforma esse caminho em um objeto Path.
# .resolve() transforma o caminho em um caminho absoluto, eliminando referências como "." e "..".
# .parents[2] sobe duas pastas a partir do diretório onde este arquivo está localizado.
# O resultado é armazenado em ROOT_DIR, que representa a pasta raiz do projeto.
ROOT_DIR = Path(__file__).resolve().parents[2]

# Cria o caminho para a pasta "OPERACIONAL".
OPERACIONAL_DIR = ROOT_DIR / "OPERACIONAL"

# Cria um objeto AppConfig contendo todos os caminhos utilizados pela aplicação.
# A variável CONFIG passa a ser o ponto central para acessar essas configurações em outras partes do projeto.
CONFIG = AppConfig(
    base_dir        =ROOT_DIR,
    municipios_dir  =ROOT_DIR / "MUNICIPIOS",
    empresas_dir    =ROOT_DIR / "EMPRESAS",
    rec_dir         =ROOT_DIR / "REC",
    req_dir         =ROOT_DIR / "REQ",
    ofi_dir         =ROOT_DIR / "OFI",
    saida_dir       =ROOT_DIR / "SAÍDA",
    fila_arquivo    =OPERACIONAL_DIR / "fila_documentos.json",
)
