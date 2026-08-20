import re
import unicodedata


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

def texto_para_vetor(texto):
    # Regex captura o nome da TAG (antes do :) e o VALOR (depois do :)
    padrao = r"^([^:]+):\s*(.*)$"

    vetor_resultado = []

    for linha in texto.strip().split("\n"):
        match = re.match(padrao, linha.strip())
        if match:
            tag = match.group(1).strip()
            valor = match.group(2).strip()

            # Adiciona ao vetor no formato desejado
            vetor_resultado.append(
                {tag : valor}
            )

    return vetor_resultado

# ============================================================== #
# EXTRAÇÃO DE MUNICÍPIO
# ============================================================== #

def extrair_municipio(texto: str) -> str | None:
    if "DOMICÍLIO DE ENTREGA" not in texto:
        return "SEM DOMICÍLIO DE ENTREGA"

    # Captura a linha/texto que antecede o código (AG: 123)
    match = re.search(r"^([^\r\n]*?)\s*\(AG:\s*\d{1,3}\)", texto, re.MULTILINE)

    if not match:
        return None

    # Extrai o texto capturado no primeiro grupo
    municipio_str = match.group(1).strip()

    # Se a captura contiver múltiplas linhas ou caminhos, pega apenas o nome final
    if "\n" in municipio_str:
        municipio_str = municipio_str.split("\n")[-1].strip()

    # Remove o código de UF/Estado ao final (ex: '-PB', '/ PB', ' PB')
    municipio_str = re.sub(
        r"[\s\-/]+[A-Za-z]{2}$", "", municipio_str
    ).strip()

    return municipio_str if municipio_str else None

# ============================================================== #
# EXTRAÇÃO DE UC
# ============================================================== #

def extrair_uc(texto_norm):

    PADROES_UC = [
        r"\b\d/\d{5,7}-\d\b",   # Maior prioridade
        r"\d{3}\.\d{3}\.\d{3}-\d{2}",  # Segunda prioridade      
        r"\d{2}\.\d{3}-\d{2}",  # Terceira prioridade
    ]

    for padrao in PADROES_UC:
        uc_match = re.search(padrao, texto_norm)

        if uc_match:
            uc = uc_match.group(0)

            # Normaliza o segundo padrão removendo 
            # if padrao == r"\b\d/\d{5,7}-\d\b":
            #     uc = uc.replace("/", "").replace("-", "")
            if padrao == r"\d{2}\.\d{3}-\d{2}":
                uc = uc.replace(".", "").replace("-", "")

            return uc

    return "Não encontrado"

# ============================================================== #
# EXTRAÇÃO DE REFERÊNCIA (MÊS/ANO)
# ============================================================== #

def extrair_mes(texto_norm):

    PADROES_MES = [
        r"\b(Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro)\s*/\s*\d{4}\b",
        r"\b(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s*/?\s*\d{4}\b",
    ]

    MESES_ABREV = {
        "janeiro": "JAN",
        "fevereiro": "FEV",
        "março": "MAR",
        "abril": "ABR",
        "maio": "MAI",
        "junho": "JUN",
        "julho": "JUL",
        "agosto": "AGO",
        "setembro": "SET",
        "outubro": "OUT",
        "novembro": "NOV",
        "dezembro": "DEZ",
    }

    for padrao in PADROES_MES:
        mes_match = re.search(padrao, texto_norm, re.IGNORECASE)
        if mes_match:
            valor = mes_match.group(0)
            partes = re.search(r"([A-Za-zÀ-ÿ]+)\s*/?\s*(\d{4})",valor)
            if partes:
                mes = partes.group(1).lower()
                ano = partes.group(2)
                mes_abrev = MESES_ABREV.get(
                    mes,
                    mes[:3].upper()
                )
                return f"{mes_abrev}/{ano}"
    return None

# ============================================================== #
# HELPERS AUXILIARES (mantidos para uso futuro)
# ============================================================== #

def extrair_ligacao(texto):
    # Procura a palavra LIGAÇÃO: seguida pelo tipo (TRIFASICO, BIFASICO ou MONOFASICO)
    match = re.search(r"LIGAÇÃO:\s*([A-Za-z]+)", texto, re.IGNORECASE)
    return match.group(1) if match else None

def extrair_forncecimento(texto):
    # Procura por BAIXA TENSÃO, MÉDIA TENSÃO ou ALTA TENSÃO no documento
    match = re.search(
        r"\b(BAIXA|MÉDIA|MEDIA|ALTA)\s+TENSÃO\b", texto, re.IGNORECASE
    )
    return match.group(0) if match else None

def extrair_classe(texto):
    # Captura tudo o que estiver na linha após 'CLASSE/SUBCLS.:'
    match = re.search(r"CLASSE/SUBCLS\.:\s*(.+)", texto, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extrair_endereco(texto):
    # Captura o texto que fica entre a linha do título e uma sequência de linhas vazias
    match = re.search(
        r"ENDEREÇO DA UNIDADE CONSUMIDORA\n+(.*?)(?=\n\s*\n|\Z)",
        texto,
        re.DOTALL,
    )
    if match:
        # Limpa espaços e une as linhas em uma única string
        linhas = [
            linha.strip()
            for linha in match.group(1).split("\n")
            if linha.strip()
        ]
        return ", ".join(linhas)
    return None

def extrair_domicilio(texto):
    # Captura o texto entre "DOMICÍLIO DE ENTREGA" e a próxima seção ("GRUPO/SUBGRP.:")
    match = re.search(
        r"DOMICÍLIO DE ENTREGA\n+(.*?)(?=\n\s*GRUPO/SUBGRP\.:)",
        texto,
        re.DOTALL,
    )
    if match:
        # Limpa espaços e une as linhas em uma única string
        linhas = [
            linha.strip()
            for linha in match.group(1).split("\n")
            if linha.strip()
        ]
        return ", ".join(linhas)
    return None

def extrair_cliente(texto):
    # Busca o conteúdo exatamente entre a linha da PAGE 001 e o DOMICÍLIO DE ENTREGA
    match = re.search(
        r"={10}\s*PAGE\s*\d+\s*={10}\s*\n+(.*?)(?=DOMICÍLIO DE ENTREGA)",
        texto,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()

    # Fallback: caso o marcador de página não exista, pega tudo do início até DOMICÍLIO DE ENTREGA
    match_fallback = re.search(
        r"^(.*?)(?=DOMICÍLIO DE ENTREGA)", texto, re.DOTALL
    )
    return match_fallback.group(1).strip() if match_fallback else None

def extrair_ultimo_kwh(texto):
    # Encontra o último número (inteiro ou decimal) que precede a unidade 'kWh'
    match = re.search(r"(\d+(?:,\d+)?)\s*kWh\s*$", texto, re.IGNORECASE)
    return match.group(1) if match else None

def extrair_valor_monetario(texto):
    # Procura a sigla R$ seguida do valor numérico (com vírgula nos centavos)
    match = re.search(r"R\$\s*\d+(?:[\.,]\d{2})?", texto)
    return match.group(0) if match else None

# EXECUÇÃO - ENERGISA
# ============================================================== #

def format_energisa(input_path, output_path):

    with open(input_path, "r", encoding="utf-8") as f:
        texto = f.read()

    municipio   = extrair_municipio(texto)
    uc          = extrair_uc(texto)
    mes         = extrair_mes(texto)
    ligacao     = extrair_ligacao(texto)
    classe      = extrair_classe(texto)
    fornecimento = extrair_forncecimento(texto)
    endereco    = extrair_endereco(texto)  
    domicilio   = extrair_domicilio(texto)
    cliente     = extrair_cliente(texto)
    consumo     = extrair_ultimo_kwh(texto)
    pagamento   = extrair_valor_monetario(texto)

    # cliente, endereco_entrega = _extrair_cliente_e_endereco(texto)
    # numero_medidor = _extrair_numero_medidor(texto)
    # leitura_anterior, leitura_atual = _extrair_datas_leitura(texto)
    # dias_medicao = _extrair_dias_medicao(texto)
    # valor_medido = _extrair_valor_medido(texto)
    # valor_faturado = _extrair_valor_faturado(texto, mes, valor_medido)
    # valor_fatura = _extrair_valor_fatura(texto)

    texto_saida = (
        f"MUNICÍPIO: {municipio}\n"
        f"UC: {uc}\n"
        f"REFERÊNCIA: {mes}\n"
        f"LIGAÇÃO: {ligacao or 'SEM_LIGACAO'}\n"
        f"CLASSIFICAÇÃO: {classe or 'SEM_CLASSIFICACAO'}\n"
        f"FORNECIMENTO: {fornecimento or 'SEM_FORNECIMENTO'}\n"
        f"ENDEREÇO: {endereco or 'SEM_ENDERECO'}\n"
        f"DOMICÍLIO: {domicilio or 'SEM_DOMICILIO'}\n"
        f"CLIENTE: {cliente or 'SEM_CLIENTE'}\n"
        f"CONSUMO: {consumo or 'SEM_CONSUMO'}\n"
        f"VALOR PAGAMENTO: {pagamento or 'SEM_VALOR_PAGAMENTO'}\n"
        # f"NÚMERO DO MEDIDOR: {numero_medidor or 'SEM_MEDIDOR'}\n"
        # f"DATA DE LEITURA ANTERIOR: {leitura_anterior}\n"
        # f"DATA DE LEITURA ATUAL: {leitura_atual}\n"
        # f"DIAS DE MEDIÇÃO: {dias_medicao}\n"
        # f"VALOR FATURADO: {valor_faturado}\n"
        # f"VALOR MEDIDO: {valor_medido}\n"
        # f"VALOR DA FATURA: {valor_fatura}\n"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(texto_saida)

    return texto_para_vetor(texto_saida)
