# ============================================================= #
# BIBLIOTECAS
# ============================================================= #

import os
import re
import fitz
from pathlib import Path

# ============================================================= #
# CONFIGURAÇÕES
# ============================================================= #

cores = [
    (91, 179, 181),
    (0, 157, 204),
    (1, 156, 178),
    (94, 197, 228),
    (0, 0, 0),
]

month_name_mapping = {
    "janeiro": "JAN", "fevereiro": "FEV", "marco": "MAR", "março": "MAR",
    "abril": "ABR", "maio": "MAI", "junho": "JUN", "julho": "JUL",
    "agosto": "AGO", "setembro": "SET", "outubro": "OUT",
    "novembro": "NOV", "dezembro": "DEZ",
}

marcadores_de_referencia = [
    "MARCADOR DE MUNICÍPIO",
    "MARCADOR DE MÊS DE REFERÊNCIA",
    "MARCADOR DE UNIDADE CONSUMIDORA",
]

# ============================================================= #
# FUNÇÕES
# ============================================================= #

def color_exists_in_page(page, cor_alvo_255):
    pix = page.get_pixmap()
    import numpy as np
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    return np.any(np.all(img_array[:, :, :3] == cor_alvo_255, axis=-1))

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

# ============================================================= #
# EXECUÇÃO
# ============================================================= #

def cropper_logic_energisa(input_path, output_path, template):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    texto = doc.load_page(0).get_text()

    recortes = ""
    pages = [doc.load_page(i) for i in range(len(doc))]

    if len(pages) == 2:
        if color_exists_in_page(pages[0], cores[3]):
            recortes = template["LAYOUT_4"]
        elif "discriminação" in texto.lower():
            recortes = template["LAYOUT_6"]
        elif color_exists_in_page(pages[1], cores[4]):
            recortes = template["LAYOUT_5"]
        else:
            recortes = template["LAYOUT_7"]

    if len(pages) == 1:
        if color_exists_in_page(pages[0], cores[0]):
            recortes = template["LAYOUT_1"]
        if color_exists_in_page(pages[0], cores[1]):
            recortes = template["LAYOUT_2"]
        if color_exists_in_page(pages[0], cores[2]):
            recortes = template["LAYOUT_3"]

    if recortes == "":
        print(f"Não foi possível identificar o layout do documento {input_path}. Verifique manualmente.")

    for i in range(len(doc)):
        recortes_pagina = recortes

        if i == 1:
            if recortes is template["LAYOUT_4"]:
                recortes_pagina = template["LAYOUT_4_VERSO"]
            elif recortes is template["LAYOUT_5"]:
                recortes_pagina = template["LAYOUT_5_VERSO"]
            elif recortes is template["LAYOUT_6"]:
                recortes_pagina = template["LAYOUT_6_VERSO"]
            elif recortes is template["LAYOUT_7"]:
                recortes_pagina = template["LAYOUT_7_VERSO"]

        for r in recortes_pagina:
            recorte = fitz.Rect(r[0], r[1], r[2], r[3])
            if recorte.width > 0 and recorte.height > 0:
                new_page = new_doc.new_page(width=recorte.width, height=recorte.height)
                new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)

    novo_nome = ""
    texto = ""

    for i in range(0, 3):
        page = new_doc.load_page(i)
        texto += marcadores_de_referencia[i] + "\n" + page.get_text() + "\n"
    texto = re.sub(r"\n\s*\n", "\n", texto)
    padrao = re.compile(r"\b(" + "|".join(month_name_mapping.keys()) + r")\b", re.IGNORECASE)
    texto = padrao.sub(lambda x: month_name_mapping[x.group().lower()], texto)

    municipio = Index(texto, marcadores_de_referencia[0])
    data = Index(texto, marcadores_de_referencia[1])
    unidade = Index(texto, marcadores_de_referencia[2])
    linhas = texto.splitlines()
    l_5 = Index(texto, "ENDEREÇO DA UNIDADE CONSUMIDORA")

    if   recortes == template["LAYOUT_1"]:
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[municipio[0] + 2])) + "_" + linhas[data[0] + 1] + "_" + linhas[unidade[0] + 1] + "_L1"
    elif recortes == template["LAYOUT_2"]:
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[municipio[0] + 3])) + "_" + linhas[data[0] + 1] + "_" + linhas[unidade[0] + 1] + "_L2"
    elif recortes == template["LAYOUT_3"]:
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[municipio[0] + 3])) + "_" + linhas[data[0] + 1] + "_" + linhas[unidade[0] + 1] + "_L3"
    elif recortes == template["LAYOUT_4"]:
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[data[0] - 2])) + "_" + linhas[data[0] + 1].replace(" ", "") + "_" + linhas[unidade[0] + 1] + "_L4"
    elif recortes == template["LAYOUT_5"]:
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[l_5[0] + 2])) + "_" + linhas[data[0] + 1] + "_" + linhas[unidade[0] + 1] + "_L5"
    elif recortes == template["LAYOUT_6"]:
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[data[0] - 1])) + "_" + linhas[data[0] + 1] + "_" + linhas[unidade[0] + 1] + "_L6"
    elif recortes == template["LAYOUT_7"]:
        print(linhas)
        novo_nome += extrair_municipio_robusto(re.sub(r"\s*/\s*", " ", linhas[municipio[0] + 2])) + "_" + linhas[data[0] + 1] + "_" + linhas[unidade[0] + 1] + "_L7"
    else:
        novo_nome = os.path.basename(input_path).replace(".pdf", "_LAYOUT_DESCONHECIDO.pdf")

    novo_nome = re.sub(r"[^\w\-_\. ]", "-", novo_nome) + ".pdf"

    if len(new_doc) > 0:
        new_doc.save(output_path)
    new_doc.close()
    doc.close()

    dir_path = os.path.dirname(output_path)
    cropped_name = novo_nome.replace(".pdf", "_Cropped.pdf")
    output_path = os.path.join(dir_path, cropped_name)
    output_path = obter_caminho_unico(dir_path, cropped_name)

    dir_path = os.path.dirname(input_path)
    new_input_path = os.path.join(dir_path, novo_nome)
    new_input_path = obter_caminho_unico(dir_path, novo_nome)
    os.rename(input_path, new_input_path)
    return output_path
