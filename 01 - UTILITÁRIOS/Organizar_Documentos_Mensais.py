# DESCRIÇÃO
# Este script organiza pastas recebidas em uma estrutura de diretórios baseada em municípios e tipos de documentos. Foi feito pensando em automatizar a organização dos documentos que chegam mensalmente vindos da concessionária.

from pathlib import Path
import shutil
import logging
import unicodedata
import re
from collections import Counter

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Ajuste estes caminhos conforme sua estrutura
PASTA_MUNICIPIOS = Path(r"C:\Users\Usuário 1\OneDrive\PASTA ENERGIA 1\PARCEIROS\Municípios Thamires e Ruda\Paraíba")
PASTA_RECEBIDOS = Path(r"C:\Users\Usuário 1\Downloads\SALVAR")

ARQUIVO_LOG = "organizacao.log"

# =============================================================================
# REGRAS DE CLASSIFICAÇÃO
# =============================================================================

TIPOS_DOCUMENTO = {
    "CÁLCULO DE ILUMINAÇÃO PÚBLICA": "QIP",
    "CALCULO DE ILUMINACAO PUBLICA": "QIP",
    "CIP": "CIP",
    "FATURAMENTO": "Faturas",
}

# =============================================================================
# LOG
# =============================================================================

logging.basicConfig(
    filename=ARQUIVO_LOG,
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def normalizar(texto: str) -> str:
    """
    Remove acentos e converte para maiúsculas.
    """
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto.upper().strip()


def montar_indice_municipios(base: Path) -> dict:
    """
    Cria um índice dos municípios existentes.
    Chave = nome normalizado.
    Valor = Path da pasta do município.
    """
    indice = {}

    for pasta in base.iterdir():
        if pasta.is_dir():
            indice[normalizar(pasta.name)] = pasta

    return indice


def identificar_tipo(nome_pasta: str):
    """
    Retorna a pasta de destino (QIP, CIP, Faturas...)
    """
    nome = normalizar(nome_pasta)

    for palavra, destino in TIPOS_DOCUMENTO.items():
        if normalizar(palavra) in nome:
            return destino

    return None


def identificar_municipio(nome_pasta: str):
    """
    Extrai o município após 'PM'.

    Exemplos:
    PM Malta
    PM Marizópolis
    """
    match = re.search(r"\bPM\s+(.+)$", nome_pasta, re.IGNORECASE)

    if not match:
        return None

    return match.group(1).strip()


# =============================================================================
# PROCESSAMENTO
# =============================================================================

def mover_pasta(origem: Path, destino: Path):
    """
    Move uma pasta usando shutil.move().
    """
    shutil.move(str(origem), str(destino))


def processar():
    indice_municipios = montar_indice_municipios(PASTA_MUNICIPIOS)

    estatisticas = Counter()

    for pasta_recebida in PASTA_RECEBIDOS.iterdir():

        if not pasta_recebida.is_dir():
            continue

        estatisticas["processadas"] += 1

        try:

            logging.info("------------------------------------------------")
            logging.info("Processando: %s", pasta_recebida.name)

            # -------------------------------------------------------------
            # Tipo
            # -------------------------------------------------------------

            destino_documento = identificar_tipo(pasta_recebida.name)

            if destino_documento is None:
                estatisticas["tipo_nao_identificado"] += 1
                logging.warning(
                    "Tipo de documento não identificado: %s",
                    pasta_recebida.name,
                )
                continue

            # -------------------------------------------------------------
            # Município
            # -------------------------------------------------------------

            municipio = identificar_municipio(pasta_recebida.name)

            if municipio is None:
                estatisticas["municipio_nao_encontrado"] += 1
                logging.warning(
                    "Município não identificado: %s",
                    pasta_recebida.name,
                )
                continue

            municipio_normalizado = normalizar(municipio)

            pasta_municipio = indice_municipios.get(municipio_normalizado)

            if pasta_municipio is None:
                estatisticas["municipio_nao_encontrado"] += 1
                logging.warning(
                    "Município inexistente: %s",
                    municipio,
                )
                continue

            # -------------------------------------------------------------
            # Destino final
            # -------------------------------------------------------------

            destino = (
                pasta_municipio
                / "Documentos"
                / destino_documento
            )

            if not destino.exists():

                estatisticas["erros"] += 1

                logging.error(
                    "Destino inexistente: %s",
                    destino,
                )

                continue

            destino_final = destino / pasta_recebida.name

            if destino_final.exists():

                estatisticas["erros"] += 1

                logging.error(
                    "Já existe pasta com o mesmo nome: %s",
                    destino_final,
                )

                continue

            mover_pasta(pasta_recebida, destino)

            estatisticas["movidas"] += 1

            logging.info(
                "Movida para %s",
                destino,
            )

        except Exception as e:

            estatisticas["erros"] += 1

            logging.exception(
                "Erro ao processar %s: %s",
                pasta_recebida.name,
                e,
            )

    return estatisticas


# =============================================================================
# MAIN
# =============================================================================

def imprimir_resumo(est):
    print()
    print("=" * 50)
    print("RESUMO")
    print("=" * 50)

    print(f"Pastas processadas........: {est['processadas']}")
    print(f"Movidas com sucesso.......: {est['movidas']}")
    print(f"Município não encontrado..: {est['municipio_nao_encontrado']}")
    print(f"Tipo não identificado.....: {est['tipo_nao_identificado']}")
    print(f"Erros.....................: {est['erros']}")

    print("\nLog salvo em:", Path(ARQUIVO_LOG).resolve())


if __name__ == "__main__":

    estatisticas = processar()

    imprimir_resumo(estatisticas)