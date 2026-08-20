from pathlib import Path    
import re

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

def _extrair_cliente(texto: str) -> str:
    linhas = [linha.strip() for linha in texto.splitlines()]
    
    for index, linha in enumerate(linhas):
        if linha == "NOME DO CLIENTE:":
            # Verifica se a segunda linha existe
            if index + 2 < len(linhas):
                segunda_linha = linhas[index + 2]
                # Se a segunda linha começar com CNPJ, retorna a primeira
                if segunda_linha.upper().startswith("CNPJ"):
                    return linhas[index + 1]
                return segunda_linha
            # Se apenas a primeira linha após o marcador existir
            elif index + 1 < len(linhas):
                return linhas[index + 1]
                
    return ""

def _extrair_endereco(texto: str) -> str:
    linhas = [linha.strip() for linha in texto.splitlines()]
    endereco_linhas = []
    capturando = False
    
    for linha in linhas:
        if linha == "ENDEREÇO:":
            capturando = True
            continue
            
        if capturando:
            # Para a captura se encontrar o marcador de página
            if re.match(r"^========== PAGE \d+ ==========$", linha):
                break
            # Adiciona a linha se não estiver vazia
            if linha:
                endereco_linhas.append(linha)
                
    return " ".join(endereco_linhas)

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

def _extrair_classificacao(texto):
    if not texto or not isinstance(texto, str):
        return None

    linhas = texto.splitlines()

    padrao_pagina = re.compile(
        r"^\s*=+\s*PAGE\s+\d+\s*=+\s*$",
        re.IGNORECASE
    )

    for i, linha in enumerate(linhas):

        linha_limpa = linha.strip()

        # Caso 1:
        # CLASSIFICAÇÃO: B4a ILUMINAÇÃO PÚBLICA...
        match = re.match(
            r"^CLASSIFICAÇÃO\s*:\s*(.+)$",
            linha_limpa,
            re.IGNORECASE
        )

        if match:
            if i > 0 and padrao_pagina.match(linhas[i - 1].strip()):
                return match.group(1).strip()

        # Caso 2:
        # CLASSIFICAÇÃO
        if re.match(r"^CLASSIFICAÇÃO\s*$", linha_limpa, re.IGNORECASE):

            if i > 0 and padrao_pagina.match(linhas[i - 1].strip()):

                for j in range(i + 1, len(linhas)):
                    valor = linhas[j].strip()

                    if valor:
                        return valor

                return None

    return "UNK"

def _extrair_fornecimento(texto):
    """
    Extrai o tipo de fornecimento de linhas como:

    TIPO DE FORNECIMENTO: Conv. Monômia - Trifásico

    Retorna:
        str: Tipo de fornecimento.
        None: Caso não encontre.
    """

    padrao = re.compile(
        r'^\s*TIPO\s+DE\s+FORNECIMENTO\s*:\s*(.+?)\s*$',
        re.IGNORECASE
    )

    for linha in texto.splitlines():
        linha = linha.strip()

        resultado = padrao.match(linha)
        if resultado:
            return resultado.group(1).strip()

    return None

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
        "Consumo Medido": 0.0,
        "Classificação": "UNK",
        "Fornecimento": "UNK",
        "Cliente": "UNK",
        "Endereço": "UNK"
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
            
        elif "CLASSIFICAÇÃO" in chave.upper():
            fatura_tags["Classificação"] = valor

        elif "FORNECIMENTO" in chave.upper():
            fatura_tags["Fornecimento"] = valor
        
        elif "CLIENTE" in chave.upper():
            fatura_tags["Cliente"] = valor
            
        elif "ENDEREÇO" in chave.upper():
            fatura_tags["Endereço"] = valor

    return fatura_tags

# ============================================================== #
# EXECUÇÃO - NEOENERGIA
# ============================================================== #

def format_neoenergia(input, file_name):    

    vetor=[]

    with open(input, "r", encoding="utf-8") as f:
        texto = f.read()
     
    unidade             = _extrair_unidade(texto)
    referencia          = _extrair_mes_referencia(texto)
    consumo_faturado    = _extrair_consumo_faturado(texto)
    consumo_medido      = _extrair_consumo_medido(texto)
    classificacao       = _extrair_classificacao(texto)
    fornecimento        = _extrair_fornecimento(texto)    
    cliente             = _extrair_cliente(texto)
    endereco            = _extrair_endereco(texto)
    print(endereco)
 
    vetor.append(unidade)
    vetor.append(referencia)
    vetor.append(consumo_faturado)
    vetor.append(consumo_medido)
    vetor.append(classificacao)
    vetor.append(fornecimento)
    vetor.append(cliente)
    vetor.append(endereco)

    texto = "UNIDADE CONSUMIDORA: "     + unidade
    texto += "\nMÊS DE REFERÊNCIA: "    + referencia
    texto += "\nCONSUMO FATURADO: "     + consumo_faturado
    texto += "\nCONSUMO MEDIDO: "       + consumo_medido
    texto += "\nCLASSIFICAÇÃO: "        + classificacao
    texto += "\nFORNECIMENTO: "         + fornecimento  
    texto += "\nCLIENTE: "              + cliente
    texto += "\nENDEREÇO: "             + endereco
    
    fatura_tags = extrair_fatura_tagueada(texto)  

    output = str(input).replace("Poppler", "Texter")
    with open(output, "w", encoding="utf-8") as f:
        f.write(texto)
    
    return fatura_tags