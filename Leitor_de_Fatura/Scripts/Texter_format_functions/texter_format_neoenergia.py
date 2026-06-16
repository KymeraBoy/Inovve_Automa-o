from pathlib import Path    
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


def _extrair_unidade(texto: str) -> str | None:
    """
    Procura no texto as linhas contendo:
    - 'CÓDIGO DA INSTALAÇÃO' ou 'Nº DA INSTALAÇÃO'

    Retorna o conteúdo da linha seguinte, com validações:
    - não vazio
    - apenas números
    - garante que o termo realmente existe no texto

    Args:
        texto (str): texto completo

    Returns:
        str | None: código encontrado ou None se inválido/não encontrado
    """

    if not texto or not isinstance(texto, str):
        return None

    linhas = texto.splitlines()

    termos = [
        "CÓDIGO DA INSTALAÇÃO",
        "Nº DA INSTALAÇÃO"
    ]

    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()

        if any(termo in linha_upper for termo in termos):
            # garante que existe próxima linha
            if i + 1 >= len(linhas):
                continue

            proxima_linha = linhas[i + 1].strip()

            # validações de segurança
            if not proxima_linha:
                continue

            if not re.fullmatch(r"\d+", proxima_linha):
                continue

            return proxima_linha

    return "UNK"

def _extrair_mes_referencia(texto: str) -> str | None:
    """
    Procura no texto os termos:
    - 'CONSUMO / kWh'
    - 'HISTÓRICO DO CONSUMO'

    Retorna o conteúdo da 3ª linha após a linha onde o termo é encontrado,
    com validações de segurança.

    Args:
        texto (str): texto completo

    Returns:
        str | None: valor encontrado ou None
    """

    if not texto or not isinstance(texto, str):
        return None

    linhas = texto.splitlines()

    termos = [
        "REF:MÊS/ANO",
        "MÊS/ANO"
    ]

    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()

        if any(termo in linha_upper for termo in termos):

            # precisa existir pelo menos 3 linhas depois
            if i + 3 >= len(linhas):
                continue

            valor = linhas[i + 1].strip()

            # validações básicas de segurança
            if not valor:
                continue

            # opcional: remover espaços duplicados
            valor = re.sub(r"\s+", " ", valor)

            return valor

    return "UNK"

def _extrair_consumo_faturado(texto: str) -> str | None:
    """
    Procura no texto os termos:
    - 'CONSUMO / kWh'
    - 'HISTÓRICO DO CONSUMO'

    Retorna o conteúdo da 3ª linha após a linha onde o termo é encontrado,
    com validações de segurança.

    Args:
        texto (str): texto completo

    Returns:
        str | None: valor encontrado ou None
    """

    if not texto or not isinstance(texto, str):
        return None

    linhas = texto.splitlines()

    termos = [
        "CONSUMO / KWH",
        "HISTÓRICO DO CONSUMO"
    ]

    for i, linha in enumerate(linhas):
        linha_upper = linha.upper()

        if any(termo in linha_upper for termo in termos):

            # precisa existir pelo menos 3 linhas depois
            if i + 3 >= len(linhas):
                continue

            valor = linhas[i + 4].strip()

            # validações básicas de segurança
            if not valor:
                continue

            # opcional: remover espaços duplicados
            valor = re.sub(r"\s+", " ", valor)

            return valor

    return "UNK"

def _extrair_consumo_medido(texto: str) -> str | None:
    """
    Procura uma linha onde a palavra 'CONSUMO' aparece sozinha
    e cuja linha anterior seja um divisor de página no formato:
    ========== PAGE X ==========

    Retorna o conteúdo da 2ª linha após essa referência.
    """

    if not texto or not isinstance(texto, str):
        return None

    linhas = texto.splitlines()

    padrao_pagina = re.compile(r"^=+\s*PAGE\s+\d+\s*=+$", re.IGNORECASE)

    for i, linha in enumerate(linhas):
        linha_limpa = linha.strip().upper()

        # A linha anterior deve ser um divisor de página
        if i == 0:
            continue

        linha_anterior = linhas[i - 1].strip()

        if (
            linha_limpa == "CONSUMO"
            and padrao_pagina.match(linha_anterior)
        ):
            # precisa existir pelo menos 2 linhas depois
            if i + 2 >= len(linhas):
                continue

            valor = linhas[i + 2].strip()

            if not valor:
                continue

            # normaliza espaços
            valor = re.sub(r"\s+", " ", valor)

            return valor

    return "UNK"


def extrair_fatura_tagueada(texto_fatura):
    """
    Transforma o texto bruto de uma fatura em um dicionário (vetor com tags)
    para facilitar a busca posterior.
    """
    linhas = [l.strip() for l in texto_fatura.splitlines() if l.strip()]
    
    # Este é o nosso vetor com tags (Dicionário)
    fatura_tags = {
        "Unidade Consumidora": None,
        "Mês de referência": None,
        "Consumo Faturado": 0.0,
        "Consumo Medido": 0.0
    }

    for linha in linhas:
        if ":" not in linha:
            continue
        
        # Divide a linha no primeiro ':' encontrado
        chave, valor = [part.strip() for part in linha.split(":", 1)]
        
        if "UNIDADE CONSUMIDORA" in chave.upper():
            fatura_tags["Unidade Consumidora"] = valor
       
        elif "MÊS DE REFERÊNCIA" in chave.upper():
            fatura_tags["Mês de referência"] = valor
            
        elif "CONSUMO FATURADO" in chave.upper():            
            # Remove letras/espaços e converte para número
            valor_limpo = re.sub(r'[^\d.,-]', '', valor).replace('.', '').replace(',', '.')
            fatura_tags["Consumo Faturado"] = float(valor_limpo) if valor_limpo else 0.0
                
        elif "CONSUMO MEDIDO" in chave.upper():
            valor_limpo = re.sub(r'[^\d.,-]', '', valor).replace('.', '').replace(',', '.')
            fatura_tags["Consumo Medido"] = float(valor_limpo) if valor_limpo else 0.0

    return fatura_tags


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


def format_neoenergia(input, file_name):    
    output = str(input).replace("Poppler", "Texter")

    vetor=[]

    with open(input, "r", encoding="utf-8") as f:
        texto = f.read()
     

    unidade = _extrair_unidade(texto)
    referencia = _extrair_mes_referencia(texto)
    consumo_faturado = _extrair_consumo_faturado(texto)
    consumo_medido = _extrair_consumo_medido(texto)
    
    vetor.append(unidade)
    vetor.append(referencia)
    vetor.append(consumo_faturado)
    vetor.append(consumo_medido)

    texto = "UNIDADE CONSUMIDORA: " + unidade
    texto += "\nMÊS DE REFERÊNCIA: " + referencia
    texto += "\nCONSUMO FATURADO: " + consumo_faturado
    texto += "\nCONSUMO MEDIDO: " + consumo_medido

    fatura_tags = extrair_fatura_tagueada(texto)


    




    with open(output, "w", encoding="utf-8") as f:
        f.write(texto)
    
    return fatura_tags