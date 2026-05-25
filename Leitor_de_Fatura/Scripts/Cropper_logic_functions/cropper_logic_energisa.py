# ============================================================= #
# BIBLIOTECAS
# ============================================================= #

import os
import re
import io
import fitz
import unicodedata
from PIL import Image

# ============================================================= #
# CONFIGURAÇÕES
# ============================================================= #

cores = [
    (192, 64, 0),
    (160, 128, 64),
    (224, 224, 160),
    (224, 96, 96),


]

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

# ============================================================= #
# FUNÇÕES
# ============================================================= #

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
    full_path = os.path.join(dir_path, cropped_name)   
    # Se o arquivo não existe, retorna o caminho original
    if not os.path.exists(full_path):
        return full_path
    # Separa o nome da extensão (ex: "imagem" e ".jpg")
    name, extension = os.path.splitext(cropped_name)    
    # Adiciona "-copia" e verifica repetidamente
    counter = 1
    new_name = f"{name}-copia{extension}"
    new_path = os.path.join(dir_path, new_name)    
    while os.path.exists(new_path):
        new_name = f"{name}-copia({counter}){extension}"
        new_path = os.path.join(dir_path, new_name)
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

def normalizar_texto_para_regra(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto

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

def identificar_layout_fatura(doc, template, texto_completo):
    pages = [doc.load_page(i) for i in range(len(doc))]
    texto_norm = normalizar_texto_para_regra(texto_completo)
    textos_paginas_norm = [normalizar_texto_para_regra(page.get_text()) for page in pages]

    if len(pages) == 2:
        scores = {"LAYOUT_4": 0, "LAYOUT_5": 0, "LAYOUT_6": 0, "LAYOUT_7": 0}
        texto_verso = textos_paginas_norm[1]

        # LAYOUT 4: forte presença de DANF3E / Documento Auxiliar
        if "danf3e" in texto_norm or "documento auxiliar" in texto_norm:
            scores["LAYOUT_4"] += 7
        if "auxiliar" in texto_norm:
            scores["LAYOUT_4"] += 3

        # LAYOUT 5: sinais característicos de bandeira/lançamentos
        if "endereco da unidade consumidora" in texto_norm:
            scores["LAYOUT_5"] += 8
        if "adic. b. vermelha" in texto_norm:
            scores["LAYOUT_5"] += 6
        if "bandeira vermelha" in texto_norm:
            scores["LAYOUT_5"] += 5
        if "faturamento pela media/minimo" in texto_norm:
            scores["LAYOUT_5"] += 4

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

# ============================================================= #
# EXECUÇÃO
# ============================================================= #

def cropper_logic_energisa(input_path, output_path, template):
    doc = fitz.open(input_path)
    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text()

    # 1) Identificacao do layout da fatura
    layout_key, recortes = identificar_layout_fatura(doc, template, texto_completo)
    if recortes is None:
        print(f"Não foi possível identificar o layout do documento {input_path}. Verifique manualmente.")
        doc.close()
        return output_path

    # 4) Aplicar os recortes apropriadamente
    new_doc = aplicar_recortes_apropriadamente(doc, recortes, layout_key, template)

    # 2) Extracao de informacoes do PDF
    info_extraida = extrair_informacoes_do_pdf(new_doc)

    # 3) Renomear o documento
    novo_nome = renomear_documento(input_path, layout_key, info_extraida)

    dir_path = os.path.dirname(output_path)
    cropped_name = novo_nome.replace(".pdf", "_Cropped.pdf")
    output_path = os.path.join(dir_path, cropped_name)
    # output_path = obter_caminho_unico(dir_path, cropped_name)

    if len(new_doc) > 0:
        new_doc.save(output_path)
    new_doc.close()
    doc.close()    

    dir_path = os.path.dirname(input_path)
    new_input_path = os.path.join(dir_path, novo_nome)
    new_input_path = obter_caminho_unico(dir_path, novo_nome)   
    os.rename(input_path, new_input_path)
    return output_path
