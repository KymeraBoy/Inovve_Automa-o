# ============================================================= #
# BIBLIOTECAS
# ============================================================= #

import os
import re
import io
import fitz
import unicodedata
import subprocess
from PIL import Image
from pathlib import Path

# ============================================================= #
# CONFIGURAÇÕES
# ============================================================= #

cores = [
    (192, 64, 0),
    (160, 128, 64),
    (224, 224, 160),
    (224, 96, 96),]

month_name_mapping = {
    "janeiro": "JAN", "fevereiro": "FEV", "marco": "MAR", "março": "MAR",
    "abril": "ABR", "maio": "MAI", "junho": "JUN", "julho": "JUL",
    "agosto": "AGO", "setembro": "SET", "outubro": "OUT",
    "novembro": "NOV", "dezembro": "DEZ",
}

numero_para_mes = {
    1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
    7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
}

marcadores_de_referencia = [
    "MARCADOR DE MUNICÍPIO",
    "MARCADOR DE MÊS DE REFERÊNCIA",
    "MARCADOR DE UNIDADE CONSUMIDORA",
]

FATOR_SIMPLIFICACAO = 32
REDUCAO_IMAGEM = (100, 100)

UCS_FORCAR_LAYOUT_4 = {
    "5/315667-6",
    "5/4078395-3",
    "5/4150041-4",
    "5/4184196-6",
    "5/4456997-8",
    "5/4457126-3",
    "5/578204-0",
}

TERMOS_PIX_QR = (
    "pix",
    "qr code",
    "qrcode",
    "pague por pix",
    "pix copia e cola",
)

# ============================================================= #
# FUNÇÕES
# ============================================================= #

# FUNÇÕES QUE EU ADICIONEI

def abrir_pdf_e_extrair_texto(input_path):
    """
    Abre um arquivo PDF e extrai todo o texto.

    Args:
        input_path (str): Caminho para o arquivo PDF.

    Returns:
        tuple: (doc, texto_completo)
            - doc: objeto fitz.Document
            - texto_completo: string contendo todo o texto do PDF
    """
    doc = fitz.open(input_path)

    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text()

    return doc, texto_completo

def extrair_uc(caminho_arquivo):
    """
    Recebe o endereço de um arquivo de texto (como String ou objeto Path),
    lê o seu conteúdo utilizando pathlib e extrai o número da unidade consumidora.
    """
    # 1. Transforma a entrada em um objeto Path de forma segura
    arquivo_path = Path(caminho_arquivo)
    
    # Validação de existência do arquivo usando pathlib
    if not arquivo_path.exists():
        print(f"Erro: O arquivo no caminho '{arquivo_path}' não foi encontrado.")
        return None
        
    try:
        # 2. Path.read_text já abre, lê e fecha o arquivo automaticamente
        texto_documento = arquivo_path.read_text(encoding='utf-8')
            
        # 3. Isola a seção específica de Código do Cliente e Instalação
        match_secao = re.search(
            r"========== CODIGO DO CLIENTE E INSTALACAO ==========(.*?)(====|$)", 
            texto_documento, 
            re.DOTALL
        )
        
        if not match_secao:
            return None
            
        bloco_instalacao = match_secao.group(1)
        
        # 4. Busca pelo padrão clássico de instalação (ex: 5/7100783-5)
        match_codigo = re.search(r"\d+/([\d\-]+)", bloco_instalacao)
        
        if match_codigo:
            return match_codigo.group(1)
            
        # 5. Fallback: Se não achar com barra, pega a primeira linha limpa com números e hífen
        linhas = [linha.strip() for linha in bloco_instalacao.split('\n') if linha.strip()]
        for linha in linhas:
            if re.match(r"^[\d\-]+$", linha):
                return linha

        return None

    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        return None

def extrair_mes_ano(caminho_arquivo):
    """
    Recebe o endereço de um arquivo de texto (como String ou objeto Path),
    lê o seu conteúdo utilizando pathlib e extrai o mês/ano de referência 
    da fatura formatado como 'MES_ANO' (Ex: JUL_2025).
    """
    # 1. Transforma a entrada em um objeto Path de forma segura
    arquivo_path = Path(caminho_arquivo)
    
    # Validação de existência do arquivo usando pathlib
    if not arquivo_path.exists():
        print(f"Erro: O arquivo no caminho '{arquivo_path}' não foi encontrado.")
        return None
        
    try:
        # 2. Abre, lê e fecha o arquivo automaticamente em UTF-8
        texto_documento = arquivo_path.read_text(encoding='utf-8')
            
        # 3. Isola a seção de Mês/Ano, Vencimento e Valor
        match_secao = re.search(
            r"========== MES/ANO, VENCIMENTO E VALOR ==========(.*?)(====|$)", 
            texto_documento, 
            re.DOTALL
        )
        
        if not match_secao:
            return None
            
        bloco_referencia = match_secao.group(1)
        
        # 4. Procura pelo padrão "NomeDoMês / Ano" (ex: Julho / 2025)
        # O padrão aceita variações com ou sem espaços em volta da barra
        match_data = re.search(r"([A-Za-zçãõÚí]+)\s*/\s*(\d{4})", bloco_referencia)
        
        if match_data:
            # Extrai o mês e o ano limpos
            mes = match_data.group(1).strip()
            ano = match_data.group(2).strip()
            
            # Formata para obter as 3 primeiras letras em maiúsculo (Ex: Julho -> JUL)
            # Nota: Caso os meses venham completos ou já abreviados, o [:3] resolve
            mes_abreviado = mes[:3].upper()
            
            # Retorna no formato solicitado: MES_ANO (Ex: JUL_2025)
            return f"{mes_abreviado}_{ano}"

        return None

    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        return None

def extrair_municipio_l4(bloco_cliente):
    """Lógica dedicada exclusivamente ao Layout 4"""
    linhas = [linha.strip() for line in bloco_cliente.split('\n') if (linha := line.strip())]
    
    for i, linha in enumerate(linhas):
        if "CNPJ" in linha or "CPF" in linha or "Insc." in linha:
            if i > 0:
                municipio_bruto = linhas[i-1]
                municipio_limpo = re.sub(r"\s*\(AG:\s*\d+\)", "", municipio_bruto).strip()
                if re.match(r"^[A-ZÁ-Úa-zá-ú\s]+$", municipio_limpo):
                    return municipio_limpo
                    
    match_pm = re.search(r"PM\s+([A-ZÁ-Úa-zá-ú]+)", bloco_cliente)
    if match_pm:
        return match_pm.group(1)
        
    if linhas:
        municipio_limpo = re.sub(r"\s*\(AG:\s*\d+\)", "", linhas[-1]).strip()
        if re.match(r"^[A-ZÁ-Úa-zá-ú\s]+$", municipio_limpo):
            return municipio_limpo
            
    return None

def extrair_municipio_l5(bloco_cliente):
    """Lógica corrigida e dedicada exclusivamente ao Layout 5"""
    # Divide em linhas e remove espaços extras
    linhas = [linha.strip() for line in bloco_cliente.split('\n') if (linha := line.strip())]
    
    # Estratégia 1: Buscar o município no início (Domicílio de Entrega)
    # Evita pegar faturas que mencionam JOAO PESSOA no fim do bloco como endereço de consumo
    for linha in linhas:
        # Se achamos uma linha com AG no começo/meio do bloco (antes de mudar para Unidade Consumidora)
        if "ENDEREÇO DA UNIDADE CONSUMIDORA" in linha:
            break # Interrompe para não capturar o município do local de consumo físico externo
            
        match_agencia = re.search(r"^([A-ZÁ-Úa-zá-ú\s]+?)\s*\(AG:\s*\d+\)", linha)
        if match_agencia:
            municipio = match_agencia.group(1).strip()
            if municipio and "PREFEITURA" not in municipio and "CASA" not in municipio:
                return municipio
            elif municipio and "PREFEITURA MUNICIPAL DE" in municipio:
                return municipio.replace("PREFEITURA MUNICIPAL DE", "").strip()

    # Estratégia 2: Procurar por linha isolada acima de metadados estruturais (ex: GRUPO/SUBGRP)
    for i, linha in enumerate(linhas):
        if "GRUPO/SUBGRP" in linha or "MATRÍCULA" in linha:
            if i > 0:
                # O candidato é a linha imediatamente anterior
                candidato = linhas[i-1]
                # Se for apenas texto limpo (o nome da cidade sozinho, ex: POMBAL)
                if re.match(r"^[A-ZÁ-Ú\s]+$", candidato) and len(candidato) > 2:
                    # Garante que não capturamos termos estruturais comuns
                    if candidato not in ["JAGUARIBE", "CENTRO", "AREA RURAL"]:
                        return candidato

    # Estratégia 3: Fallback direto por varredura de palavra-chave explícita de controle
    if "POMBAL" in bloco_cliente:
        return "POMBAL"

    return None

def extrair_municipio(caminho_arquivo):
    """
    Função principal que identifica o layout pelo nome do arquivo 
    e direciona para a lógica dedicada correspondente.
    """
    arquivo_path = Path(caminho_arquivo)
    
    if not arquivo_path.exists():
        print(f"Erro: O arquivo '{arquivo_path}' não foi encontrado.")
        return None
        
    nome_arquivo = arquivo_path.name.upper()
    
    try:
        texto_documento = arquivo_path.read_text(encoding='utf-8')
        
        # --- ROTEAMENTO POR LAYOUT ---
        if "L5" in nome_arquivo:
            match_secao = re.search(
                r"========== DOMICILIO DE ENTREGA E CLIENTE ==========(.*?)(====|$)", 
                texto_documento, 
                re.DOTALL
            )
            if match_secao:
                return extrair_municipio_l5(match_secao.group(1))
                
        elif "L4" in nome_arquivo:
            match_secao = re.search(
                r"========== CLIENTE ==========(.*?)(====|$)", 
                texto_documento, 
                re.DOTALL
            )
            if match_secao:
                return extrair_municipio_l4(match_secao.group(1))
                
        else:
            # Fallback caso o nome do arquivo venha sem a flag L4 ou L5
            if "========== DOMICILIO DE ENTREGA E CLIENTE ==========" in texto_documento:
                match_secao = re.search(r"========== DOMICILIO DE ENTREGA E CLIENTE ==========(.*?)(====|$)", texto_documento, re.DOTALL)
                return extrair_municipio_l5(match_secao.group(1))
            elif "========== CLIENTE ==========" in texto_documento:
                match_secao = re.search(r"========== CLIENTE ==========(.*?)(====|$)", texto_documento, re.DOTALL)
                return extrair_municipio_l4(match_secao.group(1))
            
        return None

    except Exception as e:
        print(f"Ocorreu um erro ao processar o arquivo {arquivo_path.name}: {e}")
        return None

# FUNÇÕES ANTIGAS

def normalizar_texto_para_regra(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto

def identificar_layout_fatura(doc, template, texto_completo):
    pages = [doc.load_page(i) for i in range(len(doc))]
    texto_norm = normalizar_texto_para_regra(texto_completo)
    textos_paginas_norm = [normalizar_texto_para_regra(page.get_text()) for page in pages]

    if len(pages) == 2:
        scores = {"LAYOUT_4": 0, "LAYOUT_5": 0, "LAYOUT_6": 0, "LAYOUT_7": 0}
        texto_verso = textos_paginas_norm[1]
        uc_fatura = extrair_uc_energisa(texto_norm)

        if uc_fatura in UCS_FORCAR_LAYOUT_4:
            return "LAYOUT_4", template["LAYOUT_4"]

        # LAYOUT 4: forte presença de DANF3E / Documento Auxiliar
        if "danf3e" in texto_norm or "documento auxiliar" in texto_norm:
            scores["LAYOUT_4"] += 7
        if "auxiliar" in texto_norm:
            scores["LAYOUT_4"] += 3
        if "nota fiscal" in texto_norm and "matricula:" in texto_norm and "dom. banc." in texto_norm:
            scores["LAYOUT_4"] += 4

        # LAYOUT 5: sinais característicos de bandeira/lançamentos
        if "endereco da unidade consumidora" in texto_norm:
            scores["LAYOUT_5"] += 8
        if "adic. b. vermelha" in texto_norm:
            scores["LAYOUT_5"] += 6
        if "bandeira vermelha" in texto_norm:
            scores["LAYOUT_5"] += 5
        if "faturamento pela media/minimo" in texto_norm:
            scores["LAYOUT_5"] += 4

        # Migração observada: alguns L4 mantêm semântica de cobrança sem QR/PIX textual.
        if parece_layout4_sem_pix_qr(texto_norm, uc_fatura):
            scores["LAYOUT_4"] += 12
            scores["LAYOUT_5"] -= 4

        # LAYOUT 6: cabeçalho mais antigo com domicílio/medidor/roteiro
        if "classe/subcls" in texto_norm:
            scores["LAYOUT_6"] += 1
        if "domicilio de entrega" in texto_norm:
            scores["LAYOUT_6"] += 1
        if "matricula:" in texto_norm and "roteiro:" in texto_norm:
            scores["LAYOUT_6"] += 1
        if "whatsapp" in texto_norm:
            scores["LAYOUT_6"] += 8

        # LAYOUT 7: costuma ter verso com pouco/nenhum texto extraível
        if len(texto_verso.strip()) < 20:
            scores["LAYOUT_7"] += 7
        if color_exists_in_page(pages[0], cores[3]):
            scores["LAYOUT_7"] += 4
        if "faturas em atraso" in texto_norm:
            scores["LAYOUT_7"] += 2

        # Critérios de desempate/fallback com sinais já usados no projeto
        if color_exists_in_page(pages[1], (0, 0, 0)):
            scores["LAYOUT_5"] += 1
        if "discriminacao" in texto_norm:
            scores["LAYOUT_6"] += 1

        layout_key = max(scores, key=scores.get)
        if scores[layout_key] > 0:
            return layout_key, template[layout_key]
        return None, None

    if len(pages) == 1:
        scores = {"LAYOUT_1": 0, "LAYOUT_2": 0, "LAYOUT_3": 0}

        if color_exists_in_page(pages[0], cores[0]):
            scores["LAYOUT_1"] += 7
        if color_exists_in_page(pages[0], cores[1]):
            scores["LAYOUT_3"] += 7
        if not color_exists_in_page(pages[0], cores[0]) and not color_exists_in_page(pages[0], cores[1]):
            scores["LAYOUT_2"] += 6

        if "valor do eusd" in texto_norm:
            scores["LAYOUT_1"] += 1
            scores["LAYOUT_2"] += 1
            scores["LAYOUT_3"] += 1

        if "data data" in texto_norm:
            scores["LAYOUT_1"] += 3
        if "cadastre sua fatura em debito automatico" in texto_norm:
            scores["LAYOUT_2"] += 2
            scores["LAYOUT_3"] += 1
        if "data de pagamento" in texto_norm:
            scores["LAYOUT_3"] += 2

        layout_key = max(scores, key=scores.get)
        if scores[layout_key] > 0:
            return layout_key, template[layout_key]
        return None, None

    # Mantém comportamento seguro: só identifica layouts conhecidos (1 ou 2 páginas)
    return None, None

def simplificar_cor(cor, fator=FATOR_SIMPLIFICACAO):
    return tuple((c // fator) * fator for c in cor)

def extrair_cores_da_pagina(page):
    cores_encontradas = set()

    desenhos = page.get_drawings()
    for desenho in desenhos:
        if "color" in desenho and desenho["color"]:
            cor = tuple(int(c * 255) for c in desenho["color"])
            cores_encontradas.add(simplificar_cor(cor))

        if "fill" in desenho and desenho["fill"]:
            cor = tuple(int(c * 255) for c in desenho["fill"])
            cores_encontradas.add(simplificar_cor(cor))

    blocos = page.get_text("dict")["blocks"]
    for bloco in blocos:
        if "lines" not in bloco:
            continue
        for linha in bloco["lines"]:
            for span in linha["spans"]:
                cor = span.get("color")
                if cor is None:
                    continue
                r = (cor >> 16) & 255
                g = (cor >> 8) & 255
                b = cor & 255
                cores_encontradas.add(simplificar_cor((r, g, b)))

    doc = page.parent
    imagens = page.get_images(full=True)
    for img in imagens:
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image = image.resize(REDUCAO_IMAGEM)

        for pixel in image.getdata():
            cores_encontradas.add(simplificar_cor(pixel))

    return cores_encontradas

def color_exists_in_page(page, cor_alvo_255):
    return simplificar_cor(cor_alvo_255) in extrair_cores_da_pagina(page)

def obter_caminho_unico(dir_path, cropped_name):
    '''Pega a pasta e o nome do arquivo, verifica se já existe um arquivo com o mesmo nome.
    Se existir, adiciona um sufixo "-copia" e um contador para criar um nome único,
    evitando sobrescrever arquivos existentes.'''

    base_path = Path(dir_path) / cropped_name
    # Se o arquivo não existe, retorna o caminho original
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    new_path = base_path.with_stem(f"{stem}-copia")
    while os.path.exists(new_path):
        new_path = base_path.with_stem(f"{stem}-copia({counter})")
        counter += 1        
    return new_path

def Index(texto, termo):
    linhas = texto.splitlines()
    indices = []
    for i, linha in enumerate(linhas):
        if termo in linha:
            indices.append(i)
    return indices

def extrair_municipio_robusto(texto):
    texto = texto.strip()
    padrao = r"^(.+?)(?=\s*[\-\s]\s*[A-Z]{2}\b|\s*\(|$)"
    match = re.search(padrao, texto, re.IGNORECASE)
    if match:
        resultado = match.group(1).strip()
        resultado = resultado.rstrip("-").strip()
        return resultado.title()
    return texto.strip().title()

def normalizar_segmento_nome(texto):
    texto = str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.upper()
    texto = re.sub(r"\s+", "_", texto)
    texto = texto.replace("/", "_")
    texto = re.sub(r"[^\w\-\.]", "-", texto)
    return texto

def extrair_municipio_para_nome(texto, linhas):
    texto_norm = normalizar_texto_para_regra(texto).upper()

    # Prioriza linhas iniciais do documento recortado com marcador de agência.
    candidatos = []
    for linha in linhas[:120]:
        linha_norm = normalizar_texto_para_regra(linha).upper()
        if "(AG:" in linha_norm:
            candidatos.append(linha_norm)

    if not candidatos:
        candidatos = [texto_norm]

    padroes = [
        r"([A-Z ]{3,})\s*(?:/|-|\s)\s*[A-Z]{2}\s*\(AG:\s*\d+\)",
        r"([A-Z ]{3,})\s*\(AG:\s*\d+\)",
    ]

    remover_prefixos = {
        "AREA", "RURAL", "POV", "POVOADO", "ASSENT", "ASSENTAMENTO",
        "RUA", "AV", "AVENIDA", "ROD", "RODOVIA", "SITIO", "FAZENDA",
    }

    for base in candidatos:
        for padrao in padroes:
            match = re.search(padrao, base)
            if not match:
                continue

            candidato = re.sub(r"\s+", " ", match.group(1)).strip(" -")
            candidato = re.sub(r"\b[A-Z]{2}\s*$", "", candidato).strip(" -")

            partes = candidato.split()
            while partes and partes[0] in remover_prefixos:
                partes = partes[1:]
            if not partes:
                continue

            # Em linhas com endereço, tende a preservar o trecho final (município)
            if len(partes) > 4:
                partes = partes[-4:]

            return extrair_municipio_robusto(" ".join(partes))

    return "Municipio_Desconhecido"

def extrair_referencia_para_nome(texto):
    texto_norm = normalizar_texto_para_regra(texto).upper()

    padrao_ref = re.search(r"\b(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s*/\s*(\d{2,4})\b", texto_norm)
    if padrao_ref:
        mes = padrao_ref.group(1)
        ano = padrao_ref.group(2)
        ano = f"20{ano}" if len(ano) == 2 else ano
        return f"{mes}/{ano}"

    padrao_matricula = re.search(r"\b\d{5,}-((?:19|20)\d{2})-(\d{1,2})-\d\b", texto_norm)
    if padrao_matricula:
        ano = padrao_matricula.group(1)
        mes_num = int(padrao_matricula.group(2))
        mes = numero_para_mes.get(mes_num)
        if mes:
            return f"{mes}/{ano}"

    return "SEM_REFERENCIA"

def extrair_unidade_para_nome(texto):
    texto_norm = normalizar_texto_para_regra(texto).upper()

    padrao_uc = re.search(r"\b\d+/\d+-\d+\b", texto_norm)
    if padrao_uc:
        return padrao_uc.group(0)

    padrao_matricula = re.search(r"\b\d{5,}-(?:19|20)\d{2}-\d{1,2}-\d\b", texto_norm)
    if padrao_matricula:
        return padrao_matricula.group(0)

    padrao_medidor = re.search(r"\bW?\d{8,}\b", texto_norm)
    if padrao_medidor:
        return padrao_medidor.group(0)

    padrao_medidor_alfanum = re.search(r"\b[A-Z]\d{8,}\b", texto_norm)
    if padrao_medidor_alfanum:
        return padrao_medidor_alfanum.group(0)

    return "SEM_UC"

def extrair_unidade_para_nome_layout4(texto):
    texto_norm = normalizar_texto_para_regra(texto).upper()

    # Novo identificador de UC observado nas faturas L4 (migração ANEEL), ex.: 5/872778-6
    padrao_uc_nova = re.search(r"\b5/\d{5,}-\d\b", texto_norm)
    if padrao_uc_nova:
        return padrao_uc_nova.group(0)

    return extrair_unidade_para_nome(texto)

def extrair_uc_energisa(texto_norm):

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

def extrair_municipio_energisa(texto: str) -> str | None:
    
    municipio_match = re.search(
        r"^([^\r\n]*?)\s*\(AG:\s*\d{1,3}\)",
        texto,
        re.MULTILINE
    )

    if "DOMICÍLIO DE ENTREGA" not in texto and municipio_match is None:
        return "SEM DOMICÍLIO DE ENTREGA"

    municipio_str = municipio_match.group(1).strip() if municipio_match else ""

    municipio_str = re.sub(
        r"\s*[-/]\s*[A-Za-z]{2}$",
        "",
        municipio_str
    )

    return municipio_str if municipio_str else None

def extrair_mes_energisa(texto_norm):

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
            partes = re.search(
                r"([A-Za-zÀ-ÿ]+)\s*/?\s*(\d{4})",
                valor
            )
            if partes:
                mes = partes.group(1).lower()
                ano = partes.group(2)
                mes_abrev = MESES_ABREV.get(
                    mes,
                    mes[:3].upper()
                )
                return f"{mes_abrev}/{ano}"
    return None

def parece_layout4_sem_pix_qr(texto_norm, uc_extraida):
    if not uc_extraida.startswith("5/"):
        return False

    tem_sinal_pix = any(termo in texto_norm for termo in TERMOS_PIX_QR)
    if tem_sinal_pix:
        return False

    if "matricula:" not in texto_norm or "dom. banc." not in texto_norm:
        return False

    # Evita conflito com layouts antigos que têm cabeçalho semelhante.
    if "classe/subcls" in texto_norm or "whatsapp" in texto_norm:
        return False

    return True

def aplicar_recortes_apropriadamente(doc, recortes, layout_key, template):
    new_doc = fitz.open()

    for i in range(len(doc)):
        recortes_pagina = recortes
        if i == 1:
            if layout_key == "LAYOUT_4":
                recortes_pagina = template["LAYOUT_4_VERSO"]
            elif layout_key == "LAYOUT_5":
                recortes_pagina = template["LAYOUT_5_VERSO"]
            elif layout_key == "LAYOUT_6":
                recortes_pagina = template["LAYOUT_6_VERSO"]
            elif layout_key == "LAYOUT_7":
                recortes_pagina = template["LAYOUT_7_VERSO"]

        for r in recortes_pagina:
            recorte = fitz.Rect(r[0], r[1], r[2], r[3])
            if recorte.width > 0 and recorte.height > 0:
                new_page = new_doc.new_page(width=recorte.width, height=recorte.height)
                new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)

    return new_doc

def extrair_informacoes_do_pdf(new_doc):
    texto = ""
    limite_cabecalho = min(3, len(new_doc))
    for i in range(0, limite_cabecalho):
        page = new_doc.load_page(i)
        texto += marcadores_de_referencia[i] + "\n" + page.get_text() + "\n"

    texto_completo = ""
    for i in range(len(new_doc)):
        page = new_doc.load_page(i)
        texto_completo += page.get_text() + "\n"

    texto = re.sub(r"\n\s*\n", "\n", texto)
    texto_completo = re.sub(r"\n\s*\n", "\n", texto_completo)
    padrao = re.compile(r"\b(" + "|".join(month_name_mapping.keys()) + r")\b", re.IGNORECASE)
    texto = padrao.sub(lambda x: month_name_mapping[x.group().lower()], texto)
    texto_completo = padrao.sub(lambda x: month_name_mapping[x.group().lower()], texto_completo)

    municipio = Index(texto, marcadores_de_referencia[0])
    data = Index(texto, marcadores_de_referencia[1])
    unidade = Index(texto, marcadores_de_referencia[2])
    linhas = texto.splitlines()
    l_5 = Index(texto, "ENDEREÇO DA UNIDADE CONSUMIDORA")

    return {
        "texto": texto,
        "texto_completo": texto_completo,
        "municipio": municipio,
        "data": data,
        "unidade": unidade,
        "linhas": linhas,
        "l_5": l_5,
    }

def renomear_documento(input_path, layout_key, info_extraida):
    del input_path
    texto = info_extraida["texto"]
    texto_completo = info_extraida.get("texto_completo", texto)
    linhas = info_extraida["linhas"]
    layout_num = layout_key.split("_")[-1] if layout_key and "_" in layout_key else "DESCONHECIDO"

    nome_municipio = extrair_municipio_para_nome(texto, linhas)
    mes_ano = extrair_referencia_para_nome(texto)
    if layout_key == "LAYOUT_4":
        unidade_consumidora = extrair_unidade_para_nome_layout4(texto_completo)
    else:
        unidade_consumidora = extrair_unidade_para_nome(texto_completo)

    municipio_fmt = normalizar_segmento_nome(nome_municipio)
    mes_ano_fmt = normalizar_segmento_nome(mes_ano)
    unidade_fmt = normalizar_segmento_nome(unidade_consumidora)

    novo_nome = f"{municipio_fmt}-{mes_ano_fmt}-{unidade_fmt}-L{layout_num}"

    return re.sub(r"[^\w\-_\. ]", "-", novo_nome) + ".pdf"

def extrair_texto_poppler_por_pagina(pdf_path, poppler_exe):
    pdf_path = Path(pdf_path)
    poppler_exe = Path(poppler_exe)

    doc = fitz.open(pdf_path)
    try:
        total_paginas = len(doc)
    finally:
        doc.close()

    textos_por_pagina = []

    for pagina_num in range(1, total_paginas + 1):
        processo = subprocess.run(
            [
                str(poppler_exe),
                "-f", str(pagina_num),
                "-l", str(pagina_num),
                "-layout",
                "-enc", "UTF-8",
                str(pdf_path),
                "-",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        if processo.returncode != 0:
            raise RuntimeError(
                f"Erro ao extrair texto da página {pagina_num} com Poppler: {processo.stderr}"
            )

        textos_por_pagina.append(processo.stdout or "")

    return textos_por_pagina

# ============================================================= #
# EXECUÇÃO
# ============================================================= #

def cropper_logic_energisa(input_path, pasta_cropper, pasta_poppler, template, Poppler):

    doc, texto_completo = abrir_pdf_e_extrair_texto(input_path)

    uc = extrair_uc_energisa(texto_completo)
    municipio = extrair_municipio_energisa(texto_completo)
    mes = extrair_mes_energisa(texto_completo)

    # Montagem do nome do documento    
    valores = [municipio, mes, uc]
    partes = []
    for valor in valores:
        valor = "".join(
            c if c.isalnum() else "_"
            for c in valor)
        valor = re.sub(r"_+", "_", valor)
        valor = valor.strip("_")
        partes.append(valor)
    nome = "-".join(partes)


    doc.close()
    novo_nome = input_path.with_name(f"{nome}.pdf")
    contador = 1
    while novo_nome.exists():
        novo_nome = input_path.with_name(f"{nome}_{contador}.pdf")
        contador += 1
    input_path.rename(novo_nome)

    # print(nome)

    # if municipio is "SEM DOMICÍLIO DE ENTREGA" :
    #     print(input_path)
    


    # # 1) Identificacao do layout da fatura
    # layout_key, recortes = identificar_layout_fatura(doc, template, texto_completo)
    # if recortes is None:
    #     print(f"Não foi possível identificar o layout do documento {input_path}. Verifique manualmente.")
    #     doc.close()
    #     return 
         
    # # 2) Aplicar os recortes apropriadamente
    # new_doc = aplicar_recortes_apropriadamente(doc, recortes, layout_key, template)

    # # 3) Extracao de informacoes do PDF
    # info_extraida = extrair_informacoes_do_pdf(new_doc)

    # # 4) Renomear o documento
    # novo_nome = renomear_documento(input_path, layout_key, info_extraida)
    
    # cropped_name = novo_nome.replace(".pdf", "_Cropped.pdf")
    # poppler_name = novo_nome.replace(".pdf", "_Poppler.txt")    
    
    # mapa_de_titulos = {
    #     "LAYOUT_4": ["DOMICILIO DE ENTREGA",
    #             "CLASSIFICACAO E FORNECIMENTO",
    #             "CLIENTE",
    #             "MES/ANO, VENCIMENTO E VALOR",
    #             "INFORMACOES",
    #             "ITENS DA FATURA",
    #             "DADOS DE MEDICAO",
    #             "DADOS FISCAIS",
    #             "APRESENTACAO",
    #             "DATAS DE LEITURA",
    #             "CODIGO DO CLIENTE E INSTALACAO",
    #             "IMPOSTOS",
    #             "HISTORICO DE CONSUMO",
    #             "RESERVADO AO FISCO",
    #         ],
    #     "LAYOUT_5": [   "DOMICILIO DE ENTREGA E CLIENTE",
    #                     "UNIDADE CONSUMIDORA",
    #                     "VALOR, REFERENCIA E CNPJ",
    #                     "VENCIMENTO, CONSUMO E RESERVADO AO FISCO",
    #                     "SITUACAO DE DEBITOS",
    #                     "DATAS DE EMISSAO/APRESENTACAO/PROXIMA LEITURA",
    #                     "DESCRITIVO",
    #                     "INFORMACOES FISCAIS",
    #                 ],
    # }    
       
    # vetor_titulos = mapa_de_titulos.get(layout_key, [])

    # cropped_pdf_path = pasta_cropper / cropped_name

    # if len(new_doc) > 0:
    #     new_doc.save(cropped_pdf_path)
    #     textos_por_pagina = extrair_texto_poppler_por_pagina(cropped_pdf_path, Poppler)
    # else:
    #     textos_por_pagina = []

    # # 4. Execução do laço gravando no arquivo
    # with open(obter_caminho_unico(pasta_poppler,poppler_name), "w", encoding="utf-8") as f:
    #     for idx, texto in enumerate(textos_por_pagina):

    #         # Verifica se o índice atual existe no vetor de títulos escolhido.
    #         # Se existir, usa o título. Se não (ex: o PDF tem mais páginas que títulos), usa um padrão.
    #         if idx < len(vetor_titulos):
    #             titulo_atual = vetor_titulos[idx]
    #         else:
    #             titulo_atual = f"PÁGINA {idx + 1}"  # Fallback caso faltem títulos

    #         # Escreve no arquivo usando o título dinâmico
    #         f.write(f"========== {titulo_atual} ==========\n")
    #         f.write(texto.strip())
    #         f.write("\n\n")      

    
    # if layout_key == "LAYOUT_4":   
    #     municipio           = extrair_municipio(pasta_poppler / poppler_name)
    #     mes_ano             = extrair_mes_ano(pasta_poppler / poppler_name)
    #     unidade_consumidora = extrair_uc(pasta_poppler / poppler_name)  
    #     novo_nome = f"{municipio}-{mes_ano}-{unidade_consumidora}-L4.txt"
    #     arquivo_original = pasta_poppler / poppler_name
    #     novo_caminho = arquivo_original.with_name(novo_nome)    
    #     arquivo_original.rename(novo_caminho)
    #     novo_nome = f"{municipio}-{mes_ano}-{unidade_consumidora}-L4.pdf"
        


    # new_doc.close()
    # doc.close()  

    

    # dir_path_input = Path(input_path).parent
    # new_input_path = obter_caminho_unico(dir_path_input, novo_nome)   
    # Path(input_path).rename(new_input_path)
    return 
