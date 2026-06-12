import re
import unicodedata


# ============================================================== #
# TABELA DE MESES (extenso → abreviação)
# ============================================================== #

_MESES_PT = {
    "janeiro": "JAN", "fevereiro": "FEV", "marco": "MAR", "março": "MAR",
    "abril": "ABR", "maio": "MAI", "junho": "JUN", "julho": "JUL",
    "agosto": "AGO", "setembro": "SET", "outubro": "OUT",
    "novembro": "NOV", "dezembro": "DEZ",
}

# Prefixos de endereço que não fazem parte do nome do município
_PREFIXOS_ENDERECO = {
    "POV", "POVOADO", "AREA", "RURAL", "ROD", "RUA", "AV", "AVENIDA",
    "LOC", "ASSENT", "ASSENTAMENTO", "SITIO", "FAZENDA", "ROTEIRO",
    "DOMICILIO", "BARRACAO", "ESCOLA", "PREFEITURA", "PM",
}


def _sem_acento(texto):
    """Remove acentos e retorna em maiúsculas."""
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).upper()


# ============================================================== #
# EXTRAÇÃO DE MUNICÍPIO
# ============================================================== #

def _extrair_municipio(texto, filename=None):
    """
    Busca linhas com padrão '(AG: XX)' presente em todos os layouts Energisa
    e extrai o nome do município que precede esse marcador.
    Fallback: primeiro segmento do filename.
    """
    pat_ag = re.compile(
        r"(.+?)\s*(?:(?:/|-)\s*[A-Z]{2}\s*)?\(AG:\s*\d+\)",
        re.IGNORECASE,
    )
    for linha in texto.splitlines():
        m = pat_ag.search(linha)
        if not m:
            continue
        candidato = m.group(1).strip()
        # Remove qualquer prefixo de endereço longo antes do nome da cidade
        partes = candidato.split()
        while partes and _sem_acento(partes[0]) in _PREFIXOS_ENDERECO:
            partes = partes[1:]
        # Trunca se sobrar muitas palavras (e.g. endereço completo colado)
        if len(partes) > 3:
            partes = partes[-3:]
        # Remove sufixo de UF isolado (ex: "SE", "PB")
        if len(partes) > 1 and re.fullmatch(r"[A-Z]{2}", partes[-1]):
            partes = partes[:-1]
        cidade = " ".join(partes).strip(" -/")
        if cidade:
            return cidade.title()

    # Fallback: primeiro segmento do filename
    if filename:
        nome_base = re.sub(r'(?:_Poppler)?\.txt$', '', filename, flags=re.IGNORECASE)
        primeiro = nome_base.split("_")[0]
        if primeiro:
            return primeiro.title()

    return "Municipio_Desconhecido"


# ============================================================== #
# EXTRAÇÃO DE UC
# ============================================================== #

def _extrair_uc_documento(texto, filename=None):
    """
    Prioridade:
    1. UC codificada no filename (padrão atual e legado)
    2. Padrão curto X/XXXXXX-X diretamente no texto Poppler (todos os layouts)
    3. Matrícula longa XXXXXX-YYYY-MM-D como último recurso
    """
    # 1. Filename: padrão atual ...-X_XXXXXX-X-LY_... e legado ..._X_XXXXXX-X_LY...
    if filename:
        padroes_nome = [
            r"-(\d{1,2})_(\d{5,8})-(\d)-L\d(?:_|\.|$)",
            r"_(\d{1,2})_(\d{5,8})-(\d)_L\d(?:_|\.|$)",
        ]
        for padrao in padroes_nome:
            m = re.search(padrao, filename, flags=re.IGNORECASE)
            if m:
                return f"{m.group(1)}/{m.group(2)}-{m.group(3)}"

    # 2. Texto: padrão de UC com bloco central longo (evita capturar CNPJ xx/0001-xx)
    pat_uc = re.search(r"\b\d{1,2}/\d{5,8}-\d\b", texto)
    if pat_uc:
        return pat_uc.group(0)

    # 3. Matrícula longa (fallback)
    pat_mat = re.search(r"\b\d{5,}-\d{4}-\d{1,2}-\d\b", texto)
    if pat_mat:
        return pat_mat.group(0)

    return "SEM_UC"


# ============================================================== #
# EXTRAÇÃO DE REFERÊNCIA (MÊS/ANO)
# ============================================================== #

def _extrair_referencia(texto, filename=None):
    """
    Prioridade:
    1. Abreviação padrão no texto: 'JAN/2020', 'SET/2021', etc.
    2. Mês por extenso no texto: 'Janeiro/2020', 'Setembro / 2023'
    3. Filename novo: MUNICIPIO_MES_ANO_UC_LX  →  MES_ANO
    4. Dedução pela matrícula longa: XXXXXX-YYYY-MM-D
    """
    _MESES_ABBR = r"JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ"

    # 1. Abreviação no texto
    m = re.search(rf"\b({_MESES_ABBR})\s*/\s*(\d{{4}})\b", texto, re.IGNORECASE)
    if m:
        return f"{m.group(1).upper()}/{m.group(2)}"

    # 2. Extenso no texto
    _EXTENSO = (
        r"janeiro|fevereiro|mar[çc]o|abril|maio|junho|julho"
        r"|agosto|setembro|outubro|novembro|dezembro"
    )
    m = re.search(rf"\b({_EXTENSO})\s*/\s*(\d{{4}})\b", texto, re.IGNORECASE)
    if m:
        chave = _sem_acento(m.group(1)).lower()
        chave = chave.replace("c", "ç") if "marco" not in chave else chave  # preserva "março"
        chave = _sem_acento(chave).lower()  # normaliza novamente após substituição
        abbr = _MESES_PT.get(chave) or _MESES_PT.get(chave.replace("ç", "c"))
        if abbr:
            return f"{abbr}/{m.group(2)}"

    # 3. Filename novo: _MES_ANO_
    if filename:
        m = re.search(r"_([A-Z]{3})_(\d{4})_", filename, flags=re.IGNORECASE)
        if m:
            return f"{m.group(1).upper()}/{m.group(2)}"

    # 4. Matrícula longa: XXXXXX-YYYY-MM-D
    _NUM_MES = {
        1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
        7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
    }
    m = re.search(r"\b\d{5,}-((?:19|20)\d{2})-(\d{1,2})-\d\b", texto)
    if m:
        abbr = _NUM_MES.get(int(m.group(2)))
        if abbr:
            return f"{abbr}/{m.group(1)}"

    return "SEM_REFERENCIA"


# ============================================================== #
# HELPERS AUXILIARES (mantidos para uso futuro)
# ============================================================== #

def _extrair_cliente_e_endereco(texto):
    linhas = texto.splitlines()
    _ruidos_inicio_bloco = (
        "DOMICILIO DE ENTREGA",
        "ENDERECO DA UNIDADE CONSUMIDORA",
        "ROTEIRO:",
        "MATRICULA:",
        "DOM. BANC.",
        "DOM. ENT.",
    )
    _ruidos_pos_ligacao = (
        "CNPJ",
        "CPF",
        "INSC",
        "CLASSIFICACAO",
        "CLASSE",
        "GRUPO",
        "LIGACAO",
        "TIPO DE FORNECIMENTO",
        "ROTEIRO:",
        "MATRICULA:",
        "REFERENCIA",
        "DATA DE APRESENTACAO",
        "UTILIZE O CODIGO",
        "PAGADOR",
        "SACADOR",
    )

    def _limpar_linha(valor):
        return valor.replace("\f", "").strip()

    def _normalizar(valor):
        return _sem_acento(valor).upper().rstrip(":")

    # Regra principal: em muitas faturas Energisa o cliente correto aparece
    # logo após a linha com indicação de ligação/tipo de fornecimento.
    idx_ligacao = None
    for i, linha in enumerate(linhas):
        base = _normalizar(_limpar_linha(linha))
        if re.search(r"\b(LIGACAO|TIPO DE FORNECIMENTO)\s*:", base):
            idx_ligacao = i
            break

    if idx_ligacao is not None:
        bloco_pos_ligacao = []
        for linha in linhas[idx_ligacao + 1:]:
            limpa = _limpar_linha(linha)
            if not limpa:
                continue
            base = _normalizar(limpa)
            if any(base.startswith(prefixo) for prefixo in _ruidos_pos_ligacao):
                break
            bloco_pos_ligacao.append(limpa)
            if len(bloco_pos_ligacao) >= 2:
                break

        if bloco_pos_ligacao:
            cliente = bloco_pos_ligacao[0]
            endereco = bloco_pos_ligacao[1] if len(bloco_pos_ligacao) >= 2 else ""
            return cliente, endereco

    _marcadores = (
        "Grupo/Subgp.", "Grupo/Subgp.:", "GRUPO/SUBGRP.",
        "Classificação:", "CLASSIFICAÇÃO:", "LIGAÇÃO:",
    )
    limite = len(linhas)
    for indice, linha in enumerate(linhas):
        if any(mk in linha for mk in _marcadores):
            limite = indice
            break
    bloco = []
    for linha in linhas[:limite]:
        linha_limpa = _limpar_linha(linha)
        if not linha_limpa:
            continue
        linha_norm = _normalizar(linha_limpa)
        if any(linha_norm.startswith(prefixo) for prefixo in _ruidos_inicio_bloco):
            continue
        bloco.append(linha_limpa)

    cliente = bloco[0] if len(bloco) >= 1 else ""
    endereco = bloco[1] if len(bloco) >= 2 else ""
    return cliente, endereco


def _extrair_numero_medidor(texto):
    padrao = (
        r"\b(?:N[ºo\.]?\s*do\s*Medidor|N[ºo\.]?\s*MEDIDOR|MEDIDOR|Medidor"
        r"|MATR[ÍI]CULA)\s*:\s*(.+)$"
    )
    for linha in texto.splitlines():
        match = re.search(padrao, linha, flags=re.IGNORECASE)
        if not match:
            continue
        valor_bruto = match.group(1).strip()
        if not valor_bruto:
            continue
        valor = re.split(
            r"\s+(?:Emiss[ãa]o|DOM\.?|REFER[ÊE]NCIA|Roteiro|Classe|Grupo|CNPJ|CPF|Insc\.?|Matr[íi]cula)\b",
            valor_bruto, maxsplit=1, flags=re.IGNORECASE,
        )[0].strip()
        valor = valor.split()[0].strip() if valor else ""
        if valor and re.search(r"\d", valor):
            return valor
    return ""


def _extrair_classificacao(texto):
    padroes = [
        r"Cls/Sbc:\s*(.+)$",
        r"CLASSE/SUBCLS\.:\s*(.+)$",
        r"Classifica[çc][ãa]o:\s*(.+)$",
    ]

    for linha in texto.splitlines():
        for padrao in padroes:
            m = re.search(padrao, linha, flags=re.IGNORECASE)
            if not m:
                continue
            valor = m.group(1).strip()
            if valor:
                return valor

    return ""


def _extrair_fornecimento(texto):
    padroes = [
        r"LIGA[ÇC][ÃA]O:\s*([A-ZÇÃÕÁÉÍÓÚ\- ]+)",
        r"Tipo de Fornecimento:\s*([A-ZÇÃÕÁÉÍÓÚ\- ]+)",
    ]

    for linha in texto.splitlines():
        for padrao in padroes:
            m = re.search(padrao, linha, flags=re.IGNORECASE)
            if not m:
                continue
            valor = m.group(1).strip()
            if not valor:
                continue
            valor = re.split(r"\s{2,}|DOM\.|CNPJ|CPF|INSC", valor, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            if valor:
                return valor

    texto_sem_acento = _sem_acento(texto)
    if "TRIFAS" in texto_sem_acento:
        return "TRIFASICO"
    if "BIFAS" in texto_sem_acento:
        return "BIFASICO"
    if "MONOFAS" in texto_sem_acento:
        return "MONOFASICO"

    return ""


def _extrair_datas_leitura(texto):
    """
    Retorna (leitura_anterior, leitura_atual) no formato DD/MM/AAAA.
    Estratégia:
    1. Prioriza janelas com a palavra LEITURA e pelo menos 2 datas.
    2. Depois procura linhas com 3 datas (comum em Anterior/Atual/Próxima).
    3. Fallback: primeira linha com ao menos 2 datas.
    """
    linhas = texto.splitlines()
    padrao_data = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")

    def datas_em_janela(janela):
        datas = padrao_data.findall(janela)
        if len(datas) < 2:
            return None
        return datas[0], datas[1]

    # 1) Janela com "LEITURA"
    for i, linha in enumerate(linhas):
        linha_norm = _sem_acento(linha)
        if "LEITURA" not in linha_norm:
            continue

        janelas = [linha]
        if i + 1 < len(linhas):
            janelas.append(f"{linha} {linhas[i + 1]}")
        if i + 2 < len(linhas):
            janelas.append(f"{linha} {linhas[i + 1]} {linhas[i + 2]}")

        for janela in janelas:
            resultado = datas_em_janela(janela)
            if resultado:
                return resultado

    # 2) Linha com 3 ou mais datas (normalmente ciclo de leitura)
    for linha in linhas:
        datas = padrao_data.findall(linha)
        if len(datas) >= 3:
            return datas[0], datas[1]

    # 3) Fallback: primeira linha com pelo menos 2 datas
    for linha in linhas:
        resultado = datas_em_janela(linha)
        if resultado:
            return resultado

    return "SEM_LEITURA_ANTERIOR", "SEM_LEITURA_ATUAL"


def _extrair_dias_medicao(texto):
    """Extrai quantidade de dias de medição do ciclo (entre leituras)."""
    linhas = texto.splitlines()

    # Padrão comum: DATA_ANT DATA_ATUAL DIAS DATA_PROXIMA
    padrao_ciclo = re.compile(
        r"\b\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?\s+"
        r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?\s*(\d{1,3})\s+"
        r"\d{2}/\d{2}/\d{4}\b"
    )

    for linha in linhas:
        # Alguns layouts colam o número de dias após HH:MM:SS (ex: 00:00:0032)
        linha_ajustada = re.sub(r"(\d{2}:\d{2}:\d{2})(\d{1,3})\b", r"\1 \2", linha)
        m = padrao_ciclo.search(linha_ajustada)
        if m:
            return m.group(1)

    # Fallback: linhas com palavra "DIAS" e um número próximo
    for linha in linhas:
        if "DIAS" not in _sem_acento(linha):
            continue
        m = re.search(r"\b(\d{1,3})\b", linha)
        if m:
            return m.group(1)

    return "SEM_DIAS_MEDICAO"


def _extrair_valor_fatura(texto):
    """Extrai valor monetário total da fatura (R$)."""
    linhas = texto.splitlines()
    padrao_moeda = re.compile(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", re.IGNORECASE)

    # Prioriza linhas com indicação de total a pagar/fatura
    for linha in linhas:
        linha_norm = _sem_acento(linha)
        if not any(chave in linha_norm for chave in ("TOTAL A PAGAR", "N FATURA", "FATURA", "TOTAL:")):
            continue
        m = padrao_moeda.search(linha)
        if m:
            return m.group(0).replace(" ", "")

    # Fallback: primeiro valor monetário encontrado
    for linha in linhas:
        m = padrao_moeda.search(linha)
        if m:
            return m.group(0).replace(" ", "")

    return "SEM_VALOR_FATURA"


def _numero_br_para_float(valor):
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except Exception:
        return None


def _formatar_kwh(valor_float):
    if valor_float is None:
        return ""
    if abs(valor_float - round(valor_float)) < 1e-6:
        return f"{int(round(valor_float))} kWh"
    return f"{valor_float:.2f}".replace(".", ",") + " kWh"


def _extrair_medido_faturado_tabela(texto):
    """
    Extrai (medido, faturado) de linhas da tabela de consumo:
    Ex.: 'KWH ... 21,00 50,00' -> ('21 kWh', '50 kWh')
    """
    for linha in texto.splitlines():
        linha_norm = _sem_acento(linha)
        if not re.match(r"^\s*KWH\b", linha_norm):
            continue

        numeros = re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:,\d+)?", linha)
        if len(numeros) < 2:
            continue

        # Em geral os dois últimos campos da linha são Medido e Faturado.
        medido = _numero_br_para_float(numeros[-2])
        faturado = _numero_br_para_float(numeros[-1])
        if medido is None or faturado is None:
            continue
        return _formatar_kwh(medido), _formatar_kwh(faturado)

    return "", ""


def _extrair_diferenca_leituras(texto):
    """
    Valor medido = leitura atual - leitura anterior (quando leituras numéricas existem).
    """
    linhas = texto.splitlines()

    # 1) Formato com linhas separadas: "Anterior ... 540 kWh" e "Atual ... 592 kWh"
    leitura_anterior = None
    leitura_atual = None

    for linha in linhas:
        m = re.search(r"\bAnterior\b\s+\d{2}/\d{2}/\d{2,4}\s+([\d\.,]+)\s*k\s*wh\b", linha, flags=re.IGNORECASE)
        if m:
            leitura_anterior = _numero_br_para_float(m.group(1))

        m = re.search(r"\bAtual\b\s+\d{2}/\d{2}/\d{2,4}\s+([\d\.,]+)\s*k\s*wh\b", linha, flags=re.IGNORECASE)
        if m:
            leitura_atual = _numero_br_para_float(m.group(1))

    if leitura_atual is not None and leitura_anterior is not None:
        diff = leitura_atual - leitura_anterior
        if diff >= 0:
            return _formatar_kwh(diff)

    # 2) Formato tabular: linha iniciando em KWH com colunas Atual e Anterior
    for linha in linhas:
        linha_norm = _sem_acento(linha)
        if not re.match(r"^\s*KWH\b", linha_norm):
            continue

        numeros = re.findall(r"\d{1,3}(?:\.\d{3})*(?:,\d+)?|\d+(?:,\d+)?", linha)
        if len(numeros) < 2:
            continue

        atual = _numero_br_para_float(numeros[0])
        anterior = _numero_br_para_float(numeros[1])
        if atual is None or anterior is None:
            continue

        # Evita capturar linhas que não são de leitura (códigos pequenos, etc.)
        if atual > 100000 or anterior > 100000:
            continue
        if atual <= 1 and anterior <= 1:
            continue

        diff = atual - anterior
        if diff >= 0:
            return _formatar_kwh(diff)

    return "SEM_VALOR_MEDIDO"


def _extrair_valor_medido(texto):
    """Extrai valor medido, priorizando diferença entre leituras."""
    valor_por_diferenca = _extrair_diferenca_leituras(texto)
    if valor_por_diferenca != "SEM_VALOR_MEDIDO":
        return valor_por_diferenca

    return "SEM_VALOR_MEDIDO"


def _extrair_valor_faturado(texto, referencia, valor_medido):
    """
    Extrai valor faturado (kWh), priorizando:
    1) Coluna Faturado da tabela KWH.
    2) Linha do histórico com mês/ano da referência.
    3) Fallback no valor medido.
    """
    _, faturado_tabela = _extrair_medido_faturado_tabela(texto)
    if faturado_tabela:
        return faturado_tabela

    # Busca no histórico o valor do mesmo mês/ano da referência
    ref_match = re.match(r"^([A-Z]{3})/(\d{2,4})$", (referencia or "").upper())
    if ref_match:
        mes_ref = ref_match.group(1)
        ano_ref = ref_match.group(2)
        ano2 = ano_ref[-2:]
        padrao_linha_ref = re.compile(
            rf"\b{mes_ref}\s*/\s*(?:{ano_ref}|{ano2})\b\s+([0-9]{{1,5}}(?:,[0-9]{{1,2}})?)",
            re.IGNORECASE,
        )

        for linha in texto.splitlines():
            linha_norm = _sem_acento(linha)
            # Evita linha de cabeçalho, moeda e datas completas.
            if "REFERENCIA" in linha_norm or "MEDIA" in linha_norm or "R$" in linha_norm:
                continue
            if re.search(r"\b\d{2}/\d{2}/\d{2,4}\b", linha):
                continue

            m = padrao_linha_ref.search(linha)
            if not m:
                continue
            v = _numero_br_para_float(m.group(1))
            if v is not None:
                return _formatar_kwh(v)

    if valor_medido != "SEM_VALOR_MEDIDO":
        return valor_medido

    return "SEM_VALOR_FATURADO"


# ============================================================== #
# EXECUÇÃO - ENERGISA
# ============================================================== #

def format_energisa(texto, filename=None):
    """
    Lê o texto bruto extraído pelo Poppler e retorna um dict com as
    informações básicas da fatura: município, UC e mês/ano de referência.

    O campo 'texto' contém o conteúdo formatado que será gravado no
    arquivo .txt Texter.
    """
    municipio = _extrair_municipio(texto, filename)
    uc = _extrair_uc_documento(texto, filename)
    referencia = _extrair_referencia(texto, filename)
    classificacao = _extrair_classificacao(texto)
    tipo_fornecimento = _extrair_fornecimento(texto)
    cliente, endereco_entrega = _extrair_cliente_e_endereco(texto)
    numero_medidor = _extrair_numero_medidor(texto)
    leitura_anterior, leitura_atual = _extrair_datas_leitura(texto)
    dias_medicao = _extrair_dias_medicao(texto)
    valor_medido = _extrair_valor_medido(texto)
    valor_faturado = _extrair_valor_faturado(texto, referencia, valor_medido)
    valor_fatura = _extrair_valor_fatura(texto)

    texto_saida = (
        f"MUNICÍPIO: {municipio}\n"
        f"UC: {uc}\n"
        f"REFERÊNCIA: {referencia}\n"
        f"CLASSIFICAÇÃO: {classificacao or 'SEM_CLASSIFICACAO'}\n"
        f"FORNECIMENTO: {tipo_fornecimento or 'SEM_FORNECIMENTO'}\n"
        f"CLIENTE: {cliente or 'SEM_CLIENTE'}\n"
        f"ENDEREÇO DE ENTREGA: {endereco_entrega or 'SEM_ENDERECO'}\n"
        f"NÚMERO DO MEDIDOR: {numero_medidor or 'SEM_MEDIDOR'}\n"
        f"DATA DE LEITURA ANTERIOR: {leitura_anterior}\n"
        f"DATA DE LEITURA ATUAL: {leitura_atual}\n"
        f"DIAS DE MEDIÇÃO: {dias_medicao}\n"
        f"VALOR FATURADO: {valor_faturado}\n"
        f"VALOR MEDIDO: {valor_medido}\n"
        f"VALOR DA FATURA: {valor_fatura}\n"
    )

    return {
        "arquivo":          filename,
        "municipio":        municipio,
        "uc":               uc,
        "referencia":       referencia,
        "texto":            texto_saida,
        # campos mantidos para compatibilidade com o pipeline
        "info_geral":       [],
        "historico_consumo": [],
        "classificacao":    classificacao,
        "tipo_fornecimento": tipo_fornecimento,
        "cliente":          cliente,
        "endereco_entrega": endereco_entrega,
        "numero_medidor":   numero_medidor,
        "leitura_anterior": leitura_anterior,
        "leitura_atual":    leitura_atual,
        "dias_medicao":     dias_medicao,
        "valor_faturado":   valor_faturado,
        "valor_medido":     valor_medido,
        "valor_fatura":     valor_fatura,
    }
