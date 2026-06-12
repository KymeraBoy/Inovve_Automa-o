import os
import re

from texter_utils import aba_info_geral


def _normalizar_linha_bloco(valor):
    return re.sub(r"\s+", " ", (valor or "").strip())


def _coletar_bloco_apos_rotulo(texto, rotulos, rotulos_parada, parar_em_documento=False):
    linhas = texto.splitlines()
    rotulos_normalizados = {_normalizar_linha_bloco(rotulo).upper() for rotulo in rotulos}
    rotulos_parada_normalizados = {_normalizar_linha_bloco(rotulo).upper() for rotulo in rotulos_parada}

    for indice, linha in enumerate(linhas):
        linha_normalizada = _normalizar_linha_bloco(linha).upper()
        if linha_normalizada not in rotulos_normalizados:
            continue

        bloco = []
        for proxima_linha in linhas[indice + 1:]:
            valor = _normalizar_linha_bloco(proxima_linha)
            if not valor:
                if bloco:
                    break
                continue

            valor_upper = valor.upper()
            if valor_upper in rotulos_parada_normalizados:
                break
            if parar_em_documento and (valor_upper.startswith("CNPJ") or valor_upper.startswith("CPF")):
                break

            bloco.append(valor)

        if bloco:
            return bloco

    return []

# ============================================================== #
# EXECUÇÃO - NEOENERGIA
# ============================================================== #

def _extrair_do_nome_arquivo(filename):
    if not filename:
        return "", "", ""

    base = os.path.basename(filename)
    stem = os.path.splitext(base)[0]
    partes = stem.split("-")

    municipio = partes[0] if len(partes) > 0 else ""
    referencia = partes[1] if len(partes) > 1 else ""
    unidade = partes[2] if len(partes) > 2 else ""

    municipio = municipio.replace("_", " ").strip()
    referencia = referencia.replace("_", "/").strip()
    unidade = re.sub(r"\D", "", unidade)

    return municipio, unidade, referencia


def _normalizar_referencia(valor):
    if not valor:
        return ""

    match = re.search(r"\b(\d{2})\s*/\s*(\d{2,4})\b", valor)
    if not match:
        return ""

    mes = match.group(1)
    ano = match.group(2)
    if len(ano) == 2:
        ano = f"20{ano}"
    return f"{mes}/{ano}"


def _extrair_referencia(texto):
    candidatos = [
        r"REF\s*:?\s*M[ÊE]S\s*/\s*ANO\s*\n\s*(\d{2}\s*/\s*\d{2,4})",
        r"M[ÊE]S\s*/\s*ANO\s*\n\s*(\d{2}\s*/\s*\d{2,4})",
    ]
    for padrao in candidatos:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            referencia = _normalizar_referencia(match.group(1))
            if referencia:
                return referencia
    return ""


def _extrair_unidade(texto):
    candidatos = [
        r"C[ÓO]DIGO\s+DA\s+INSTALA[ÇC][ÃA]O\s*\n\s*(\d+)",
        r"N[ºO.]\s*DA\s+INSTALA[ÇC][ÃA]O\s*\n\s*(\d+)",
        r"CONTA\s+CONTRATO\s*\n\s*(\d+)",
    ]
    for padrao in candidatos:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""


def _extrair_municipio(texto):
    match = re.search(
        r"(?:MUNICIPIO DE|PREFEITURA MUNICIPAL DE|PREF MUNICIPAL DE)\s+([A-ZÀ-ÚÇ ]{3,})",
        texto.upper(),
    )
    if match:
        municipio = re.sub(r"\s+", " ", match.group(1)).strip()
        return municipio
    return ""


def _extrair_classificacao(texto):
    candidatos = [
        # Layout novo: "CLASSIFICACAO: <valor>"
        r"CLASSIFICA[ÇC][ÃA]O\s*:\s*([^\n\r]+)",
        # Layout antigo: "CLASSIFICACAO" em uma linha e valor na seguinte
        r"CLASSIFICA[ÇC][ÃA]O\s*[\n\r]+\s*([^\n\r]+)",
    ]

    for padrao in candidatos:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            classificacao = re.sub(r"\s+", " ", match.group(1)).strip(" ,.-")
            if classificacao:
                return classificacao

    return ""


def _extrair_fornecimento(texto):
    candidatos = [
        r"CLASSIFICA[ÇC][ÃA]O\s*:\s*[^\n\r]+\s*[\n\r]+\s*([^\n\r,]+(?:[\- ][^\n\r,]+)?)",
        r"CLASSIFICA[ÇC][ÃA]O\s*[\n\r]+\s*[^\n\r]+\s*[\n\r]+\s*([^\n\r]+)",
    ]

    for padrao in candidatos:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            fornecimento = re.sub(r"\s+", " ", match.group(1)).strip(" ,.-")
            if fornecimento:
                return fornecimento

    return ""


def _extrair_cliente(texto):
    linhas_cliente = _coletar_bloco_apos_rotulo(
        texto,
        rotulos=["NOME DO CLIENTE:", "DADOS DO CLIENTE"],
        rotulos_parada=[
            "ENDEREÇO:",
            "ENDERECO:",
            "ENDEREÇO DA UNIDADE CONSUMIDORA",
            "ENDERECO DA UNIDADE CONSUMIDORA",
            "CLASSIFICAÇÃO",
            "CLASSIFICACAO",
            "REF:MÊS/ANO",
            "REF:MES/ANO",
            "MÊS/ANO",
            "MES/ANO",
            "CÓDIGO DA INSTALAÇÃO",
            "CODIGO DA INSTALACAO",
            "Nº DA INSTALAÇÃO",
            "N° DA INSTALAÇÃO",
            "N DA INSTALAÇÃO",
            "CONTA CONTRATO",
        ],
        parar_em_documento=True,
    )
    return " ".join(linhas_cliente)


def _extrair_endereco_entrega(texto):
    linhas_endereco = _coletar_bloco_apos_rotulo(
        texto,
        rotulos=["ENDEREÇO:", "ENDERECO:", "ENDEREÇO DA UNIDADE CONSUMIDORA", "ENDERECO DA UNIDADE CONSUMIDORA"],
        rotulos_parada=[
            "CLASSIFICAÇÃO",
            "CLASSIFICACAO",
            "REF:MÊS/ANO",
            "REF:MES/ANO",
            "MÊS/ANO",
            "MES/ANO",
            "CÓDIGO DA INSTALAÇÃO",
            "CODIGO DA INSTALACAO",
            "Nº DA INSTALAÇÃO",
            "N° DA INSTALAÇÃO",
            "N DA INSTALAÇÃO",
            "CONTA CONTRATO",
            "HISTÓRICO DO CONSUMO",
            "HISTORICO DO CONSUMO",
        ],
    )
    return " | ".join(linhas_endereco)


def format_neoenergia(texto, filename=None):
    municipio_nome, unidade_nome, referencia_nome = _extrair_do_nome_arquivo(filename)

    municipio = _extrair_municipio(texto) or municipio_nome or "UNK"
    unidade = _extrair_unidade(texto) or unidade_nome or "UNK"
    referencia = _extrair_referencia(texto) or _normalizar_referencia(referencia_nome) or "UNK"
    classificacao = _extrair_classificacao(texto) or "UNK"
    fornecimento = _extrair_fornecimento(texto) or "SEM_FORNECIMENTO"
    cliente = _extrair_cliente(texto) or "SEM_CLIENTE"
    endereco_entrega = _extrair_endereco_entrega(texto) or "SEM_ENDERECO"

    registro = [unidade, municipio, referencia, classificacao]
    if not any(linha[:4] == registro for linha in aba_info_geral):
        aba_info_geral.append(registro)

    return (
        f"MUNICIPIO\t{municipio}\n"
        f"UNIDADE CONSUMIDORA\t{unidade}\n"
        f"MES/ANO REFERENCIA\t{referencia}\n"
        f"CLASSIFICACAO\t{classificacao}\n"
        f"FORNECIMENTO\t{fornecimento}\n"
        f"CLIENTE\t{cliente}\n"
        f"ENDERECO DE ENTREGA\t{endereco_entrega}\n"
    )
