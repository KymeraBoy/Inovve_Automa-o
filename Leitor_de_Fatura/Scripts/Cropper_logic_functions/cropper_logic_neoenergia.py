import os
import re
import fitz
from pathlib import Path
import shutil 
import subprocess
from pypdf import PdfReader

def limpar_pasta(caminho_pasta: str | Path) -> None:
    """
    Remove todo o conteúdo de uma pasta, mas mantém a própria pasta.

    Args:
        caminho_pasta: Caminho da pasta a ser limpa.
    """
    pasta = Path(caminho_pasta)

    if not pasta.exists():
        raise FileNotFoundError(f"A pasta '{pasta}' não existe.")

    if not pasta.is_dir():
        raise NotADirectoryError(f"'{pasta}' não é uma pasta.")

    for item in pasta.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


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
    while new_path.exists():
        new_path = base_path.with_stem(f"{stem}-copia({counter})")
        counter += 1        
    return new_path

def pdf_para_txt_com_paginas(pdf_path: str | Path,
                             pdftotext_path: str | Path,
                             output_txt_path: str | Path):
    """
    Converte PDF em TXT usando Poppler (pdftotext),
    separando o conteúdo por página.

    Args:
        pdf_path: caminho do PDF
        pdftotext_path: caminho do executável pdftotext
        output_txt_path: caminho do arquivo TXT de saída
    """

    pdf_path = Path(pdf_path)
    pdftotext_path = Path(pdftotext_path)
    output_txt_path = Path(output_txt_path)

    # pdfinfo normalmente fica na mesma pasta do pdftotext
    pdfinfo_path = pdftotext_path.parent / "pdfinfo"

    # 1. Obter número de páginas
    result = subprocess.run(
        [str(pdfinfo_path), str(pdf_path)],
        capture_output=True,
        text=True
    )

    num_pages = None
    for line in result.stdout.splitlines():
        if "Pages:" in line:
            num_pages = int(line.split(":")[1].strip())
            break

    if num_pages is None:
        raise RuntimeError("Não foi possível determinar o número de páginas do PDF.")

    # garante diretório de saída
    output_txt_path.parent.mkdir(parents=True, exist_ok=True)

    # 2. Escrever arquivo de saída
    with output_txt_path.open("w", encoding="utf-8") as out_file:

        for page in range(1, num_pages + 1):
            out_file.write(f"========== PAGE {page} ==========\n\n")

            process = subprocess.run(
                [
                    str(pdftotext_path),
                    "-f", str(page),
                    "-l", str(page),
                    "-layout",
                    str(pdf_path),
                    "-"
                ],
                capture_output=True,
                text=True
            )

            if process.returncode != 0:
                raise RuntimeError(
                    f"Erro ao processar página {page}: {process.stderr}"
                )

            out_file.write(process.stdout or "")
            out_file.write("\n\n")

# ============================================================== #
# Funções
# ============================================================== #

def _normalizar_texto(texto):
    substituicoes = str.maketrans({
        "Á": "A", "À": "A", "Â": "A", "Ã": "A", "Ä": "A",
        "É": "E", "È": "E", "Ê": "E", "Ë": "E",
        "Í": "I", "Ì": "I", "Î": "I", "Ï": "I",
        "Ó": "O", "Ò": "O", "Ô": "O", "Õ": "O", "Ö": "O",
        "Ú": "U", "Ù": "U", "Û": "U", "Ü": "U",
        "Ç": "C",
        "á": "a", "à": "a", "â": "a", "ã": "a", "ä": "a",
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "í": "i", "ì": "i", "î": "i", "ï": "i",
        "ó": "o", "ò": "o", "ô": "o", "õ": "o", "ö": "o",
        "ú": "u", "ù": "u", "û": "u", "ü": "u",
        "ç": "c",
    })
    texto = texto.translate(substituicoes).upper()
    return re.sub(r"\s+", " ", texto).strip()


def _linha_valida(texto, posicao=0):
    linhas_validas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    if len(linhas_validas) > posicao:
        return linhas_validas[posicao]
    return linhas_validas[0] if linhas_validas else ""


def _montar_nome_agrupada(textos_agrupada):
    cliente_linhas = [linha.strip() for linha in textos_agrupada[0].splitlines() if linha.strip()]
    cliente = cliente_linhas[1] if len(cliente_linhas) > 1 else (cliente_linhas[0] if cliente_linhas else "AGRUPADA")
    cliente = re.sub(r"^(PREFEITURA MUNICIPAL DE|PREF MUNICIPAL DE|MUNICIPIO DE)\s+", "", cliente, flags=re.IGNORECASE)

    referencia = _linha_valida(textos_agrupada[1], 1)
    codigo = _linha_valida(textos_agrupada[2], 2)

    partes = [parte for parte in [cliente, referencia, codigo] if parte]
    if not partes:
        partes = ["AGRUPADA"]

    novo_nome = "-".join(partes)
    novo_nome = re.sub(r"[^\w\-_\. ]", "_", novo_nome).strip(" -_.")
    novo_nome = novo_nome + "-COLETIVA"
    return f"{novo_nome or 'AGRUPADA'}.pdf"

def _normalizar_segmento_nome(texto):
    texto = _normalizar_texto(texto)
    texto = texto.replace("/", "_").replace("\\", "_")
    texto = re.sub(r"\s+", "_", texto)
    return re.sub(r"[^\w\-\.]+", "_", texto).strip(" _.-") or "SEM_DADO"


def _extrair_textos_recortes(page, recortes):
    textos = []
    for r in recortes:
        area = fitz.Rect(r[0], r[1], r[2], r[3])
        textos.append(page.get_text(clip=area).strip())
    return textos


def _identificar_layout_individual(page, template):
    candidatos = {
        "INDIVIDUAL_NEW": template["INDIVIDUAL_NEW"],
        "INDIVIDUAL_OLD": template["INDIVIDUAL_OLD"],
    }
    melhor_layout = "INDIVIDUAL_NEW"
    melhor_score = float("-inf")
    melhor_textos = []

    for layout_key, recortes in candidatos.items():
        textos = _extrair_textos_recortes(page, recortes[:4])
        base = _normalizar_texto("\n".join(textos))
        score = 0

        if layout_key == "INDIVIDUAL_NEW":
            if "NOME DO CLIENTE" in base:
                score += 4
            if "CODIGO DA INSTALACAO" in base:
                score += 4
            if "REF:MES/ANO" in base or "REF MES/ANO" in base:
                score += 2
            if "TIPO DE FORNECIMENTO" in base:
                score += 1
        else:
            if "DADOS DO CLIENTE" in base:
                score += 3
            if "N DA INSTALACAO" in base or "NO DA INSTALACAO" in base:
                score += 4
            if "CONTA CONTRATO" in base:
                score += 2
            if "ENDERECO DA UNIDADE CONSUMIDORA" in base:
                score += 2
            if "CLASSIFICACAO" in base:
                score += 1

        if score > melhor_score:
            melhor_layout = layout_key
            melhor_score = score
            melhor_textos = textos

    return melhor_layout, melhor_textos, melhor_score


def _classificar_pagina_neoenergia(page, template):
    texto_pagina = page.get_text("text")
    texto_norm = _normalizar_texto(texto_pagina)

    pontuacoes = {
        "COLETIVA": 0,
        "INDIVIDUAL_NEW": 0,
        "INDIVIDUAL_OLD": 0,
        "VERSO_NEW": 0,
        "VERSO_OLD": 0,
    }

    if "DOCUMENTO PARA PAGAMENTO DA CONTA COLETIVA" in texto_norm:
        pontuacoes["COLETIVA"] += 8
    if "INFORMACOES SOBRE A CONTA COLETIVA" in texto_norm:
        pontuacoes["COLETIVA"] += 4
    if "CONTA CONTRATO COLETIVA" in texto_norm:
        pontuacoes["COLETIVA"] += 4

    if "NOME DO CLIENTE" in texto_norm:
        pontuacoes["INDIVIDUAL_NEW"] += 5
    if "CODIGO DA INSTALACAO" in texto_norm:
        pontuacoes["INDIVIDUAL_NEW"] += 5
    if "REF:MES/ANO" in texto_norm or "REF MES/ANO" in texto_norm:
        pontuacoes["INDIVIDUAL_NEW"] += 3
    if "TOTAL A PAGAR R$" in texto_norm:
        pontuacoes["INDIVIDUAL_NEW"] += 2

    if "DADOS DO CLIENTE" in texto_norm:
        pontuacoes["INDIVIDUAL_OLD"] += 3
    if "N DA INSTALACAO" in texto_norm or "NO DA INSTALACAO" in texto_norm or "INSTALACAO" in texto_norm:
        pontuacoes["INDIVIDUAL_OLD"] += 4
    if "ENDERECO DA UNIDADE CONSUMIDORA" in texto_norm:
        pontuacoes["INDIVIDUAL_OLD"] += 4
    if "CONTA CONTRATO" in texto_norm and "COLETIVA" not in texto_norm:
        pontuacoes["INDIVIDUAL_OLD"] += 2
    if "CLASSIFICACAO" in texto_norm:
        pontuacoes["INDIVIDUAL_OLD"] += 1

    if "ACESSE NEOENERGIACOELBA.COM.BR E CONFIRA NOSSO AVISO DE PRIVACIDADE" in texto_norm:
        pontuacoes["VERSO_NEW"] += 8
    if "FALE COM A GENTE" in texto_norm:
        pontuacoes["VERSO_NEW"] += 3
    if "NOSSOS CANAIS DE ATENDIMENTO" in texto_norm:
        pontuacoes["VERSO_NEW"] += 3
    if "INFORMACOES IMPORTANTES" in texto_norm:
        pontuacoes["VERSO_NEW"] += 2

    if "AVISO IMPORTANTE" in texto_norm:
        pontuacoes["VERSO_OLD"] += 5
    if "UTILIZAR A OPCAO \"TITULO\"" in texto_norm:
        pontuacoes["VERSO_OLD"] += 5
    if "ESTE DOCUMENTO POSSIBILITA O PAGAMENTO EM QUALQUER BANCO" in texto_norm:
        pontuacoes["VERSO_OLD"] += 4
    if "COMPROVANTE DO CLIENTE" in texto_norm:
        pontuacoes["VERSO_OLD"] += 2

    layout_individual, textos_individuais, score_individual = _identificar_layout_individual(page, template)
    pontuacoes[layout_individual] += max(score_individual, 0)

    tipo, score = max(pontuacoes.items(), key=lambda item: item[1])
    if score <= 0:
        return "UNKNOWN", texto_pagina, [], 0

    if tipo.startswith("INDIVIDUAL"):
        return tipo, texto_pagina, textos_individuais, score

    return tipo, texto_pagina, [], score


def _extrair_municipio_referencia_do_nome(input_path):
    nome = os.path.basename(input_path)
    match = re.match(r"([^\-]+)-([0-9]{2}_[0-9]{2})-", nome)
    if match:
        return match.group(1), match.group(2)
    base = os.path.splitext(nome)[0]
    partes = base.split("-")
    municipio = partes[0] if partes else "MUNICIPIO"
    referencia = partes[1] if len(partes) > 1 else "SEM_REF"
    return municipio, referencia


def _extrair_municipio_por_prefixo(texto):
    texto_norm = _normalizar_texto(texto)
    match_nome = re.search(
        r"\b(?:MUNICIPIO DE|PREFEITURA MUNICIPAL DE|PREF MUNICIPAL DE)\s+([A-Z ]{3,})",
        texto_norm,
    )
    if match_nome:
        municipio_raw = re.sub(r"\s+", " ", match_nome.group(1)).strip()
        palavras = municipio_raw.split()
        termos_corte = {
            "ESTADIO", "ILUMINACAO", "PRACA", "ESCOLA", "PM", "PREDIOS",
            "PREDIO", "RUA", "AV", "AVENIDA", "PC", "POVOADO", "BARRACAO",
            "MERCADO", "SECRETARIA", "UNIDADE", "PUBLICOS", "PUBLICO",
            "CNPJ", "CPF", "ENDERECO", "CLIENTE", "CONSUMIDORA",
        }
        municipio_palavras = []
        for palavra in palavras:
            if palavra in termos_corte and municipio_palavras:
                break
            municipio_palavras.append(palavra)

        municipio = " ".join(municipio_palavras).strip()
        if municipio and len(municipio) >= 3:
            return municipio

    return ""


def _extrair_municipio_do_cliente(layout_individual, textos_ind):
    candidatos = []
    if layout_individual == "INDIVIDUAL_NEW" and len(textos_ind) > 0:
        candidatos.append(textos_ind[0])
    elif layout_individual == "INDIVIDUAL_OLD" and len(textos_ind) > 1:
        candidatos.append(textos_ind[1])

    for candidato in candidatos:
        municipio = _extrair_municipio_por_prefixo(candidato)
        if municipio:
            return municipio

    return ""


def _extrair_municipio_individual(texto_pagina, input_path, layout_individual, textos_ind):
    municipio_cliente = _extrair_municipio_do_cliente(layout_individual, textos_ind)
    if municipio_cliente:
        return municipio_cliente

    texto_norm = _normalizar_texto(texto_pagina)

    # Prioriza padrão com CEP, que costuma trazer apenas "MUNICIPIO UF".
    match_cep = re.search(r"\b\d{5}-\d{3}\s+([A-Z ]{3,}?)(?=\s+[A-Z]{2}\b)", texto_norm)
    if match_cep:
        municipio = re.sub(r"\s+", " ", match_cep.group(1)).strip()
        if municipio:
            return municipio

    municipio_pagina = _extrair_municipio_por_prefixo(texto_pagina)
    if municipio_pagina:
        return municipio_pagina

    match_barra = re.search(r"/([A-Z ]{3,})\b", texto_norm)
    if match_barra:
        municipio = re.sub(r"\s+", " ", match_barra.group(1)).strip()
        if municipio:
            return municipio

    municipio_fallback, _ = _extrair_municipio_referencia_do_nome(input_path)
    return municipio_fallback


def _extrair_referencia_do_nome(input_path):
    _, referencia = _extrair_municipio_referencia_do_nome(input_path)
    return referencia


def _normalizar_referencia_para_nome(texto):
    texto_norm = _normalizar_texto(texto)

    match_numerico = re.search(r"\b(\d{2})\s*/\s*(\d{2,4})\b", texto_norm)
    if match_numerico:
        mes = match_numerico.group(1)
        ano = match_numerico.group(2)
        if len(ano) == 4:
            ano = ano[-2:]
        return f"{mes}_{ano}"

    meses = {
        "JAN": "01",
        "FEV": "02",
        "MAR": "03",
        "ABR": "04",
        "MAI": "05",
        "JUN": "06",
        "JUL": "07",
        "AGO": "08",
        "SET": "09",
        "OUT": "10",
        "NOV": "11",
        "DEZ": "12",
    }
    match_textual = re.search(r"\b(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\s*/?\s*(\d{2,4})\b", texto_norm)
    if match_textual:
        mes = meses[match_textual.group(1)]
        ano = match_textual.group(2)
        if len(ano) == 4:
            ano = ano[-2:]
        return f"{mes}_{ano}"

    return ""


def _extrair_referencia_individual(layout_individual, textos_ind, input_path):
    candidatos = []
    if layout_individual == "INDIVIDUAL_NEW":
        if len(textos_ind) > 1:
            candidatos.append(textos_ind[1])
        if len(textos_ind) > 4:
            candidatos.append(textos_ind[4])
    elif layout_individual == "INDIVIDUAL_OLD":
        if len(textos_ind) > 7:
            candidatos.append(textos_ind[7])
        if len(textos_ind) > 4:
            candidatos.append(textos_ind[4])
        if len(textos_ind) > 6:
            candidatos.append(textos_ind[6])

    for candidato in candidatos:
        referencia = _normalizar_referencia_para_nome(candidato)
        if referencia:
            return referencia

    return _extrair_referencia_do_nome(input_path)


def _extrair_unidade_individual(texto_pagina):
    texto_norm = _normalizar_texto(texto_pagina)
    padroes = [
        r"CODIGO DA INSTALACAO\s*(\d+)",
        r"INSTALACAO\D+(\d+)",
        r"N\W*DA INSTALACAO\s*(\d+)",
        r"NO\W*DA INSTALACAO\s*(\d+)",
        r"N\.\W*DA INSTALACAO\s*(\d+)",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto_norm)
        if match:
            return match.group(1)

    numeros = re.findall(r"\b\d{5,}\b", texto_norm)
    return numeros[0] if numeros else "SEM_UNIDADE"


def _extrair_unidade_por_layout(layout_individual, textos_ind, texto_pagina):
    candidatos = []
    if layout_individual == "INDIVIDUAL_NEW":
        if len(textos_ind) > 2:
            candidatos.append(textos_ind[2])
    elif layout_individual == "INDIVIDUAL_OLD":
        if len(textos_ind) > 0:
            candidatos.append(textos_ind[0])

    candidatos.append(texto_pagina)

    for candidato in candidatos:
        unidade = _extrair_unidade_individual(candidato)
        if unidade != "SEM_UNIDADE":
            return unidade

    return "SEM_UNIDADE"


def _montar_nome_individual(input_path, texto_pagina, layout_individual, textos_ind):
    municipio = _extrair_municipio_individual(texto_pagina, input_path, layout_individual, textos_ind)
    referencia = _extrair_referencia_individual(layout_individual, textos_ind, input_path)
    unidade = _extrair_unidade_por_layout(layout_individual, textos_ind, texto_pagina)
    layout_sufixo = layout_individual.replace("INDIVIDUAL_", "")

    partes = [
        _normalizar_segmento_nome(municipio),
        _normalizar_segmento_nome(referencia),
        _normalizar_segmento_nome(unidade),
        _normalizar_segmento_nome(layout_sufixo),
    ]
    return "-".join(partes) + ".pdf"

def pdf_para_txt(caminho_pdf: str, caminho_txt_saida: str) -> None:
    """
    Extrai texto de cada página de um PDF e salva em um arquivo TXT,
    separando páginas com uma marcação.

    Args:
        caminho_pdf (str): caminho do arquivo PDF de entrada
        caminho_txt_saida (str): caminho completo do arquivo TXT de saída
    """

    reader = PdfReader(caminho_pdf)

    with open(caminho_txt_saida, "w", encoding="utf-8") as f:
        for i, page in enumerate(reader.pages, start=1):
            texto = page.extract_text() or ""

            f.write(f"========== PAGE {i} ==========\n")
            f.write(texto.strip())
            f.write("\n\n")

# ============================================================== #
# EXECUÇÃO
# ============================================================== #

def cropper_logic_neoenergia(input_path, pasta_cropper, pasta_poppler, ind_dir, template, poppler):
    
    # Abre o PDF no fitz
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    recortes = None
    novo_nome = None

    for i in range(len(doc)):
    
        page = doc.load_page(i)
        tipo_pagina, texto_pagina, textos_ind, score_pagina = _classificar_pagina_neoenergia(page, template)

        if tipo_pagina == "COLETIVA":
            recortes = template["AGRUPADA"]
            textos_agrupada = []

            for r in recortes:
                recorte = fitz.Rect(r[0], r[1], r[2], r[3])
                texto_recorte = page.get_text(clip=recorte).strip()
                textos_agrupada.append(texto_recorte)

                if recorte.width > 0 and recorte.height > 0:
                    new_page = new_doc.new_page(width=recorte.width, height=recorte.height)
                    new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)

            if novo_nome is None:
                novo_nome = _montar_nome_agrupada(textos_agrupada)                
        elif tipo_pagina in {"VERSO_NEW", "VERSO_OLD"}:
            continue
        elif tipo_pagina in {"INDIVIDUAL_NEW", "INDIVIDUAL_OLD"}:
            recortes_ind = template[tipo_pagina]

            textos_ind = _extrair_textos_recortes(page, recortes_ind)

            nome_pdf = _montar_nome_individual(input_path, texto_pagina, tipo_pagina, textos_ind)   
            nome_pdf_cropped = nome_pdf.replace(".pdf", "_Cropped.pdf") # Este é apenas o nome, não um Path
            nome_pdf_poppler = nome_pdf.replace(".pdf", "_Poppler.txt") # Este é apenas o nome, não um Path

            caminho_pdf_original = obter_caminho_unico(ind_dir, nome_pdf)            
            caminho_pdf_cropped = obter_caminho_unico(pasta_cropper, nome_pdf_cropped)
            caminho_pdf_poppler = obter_caminho_unico(pasta_poppler, nome_pdf_poppler)


            # Salva a página individual completa na pasta de faturas originais.
            with fitz.open() as doc_original:
                doc_original.insert_pdf(
                    doc,
                    from_page=i,
                    to_page=i
                )
                doc_original.save(caminho_pdf_original)            

            # Salva a versão recortada da fatura individual na pasta Cropped do município.            
            doc_ind = fitz.open()
            for r in recortes_ind:
                recorte = fitz.Rect(r[0], r[1], r[2], r[3])
                if recorte.width > 0 and recorte.height > 0:
                    new_page = doc_ind.new_page(width=recorte.width, height=recorte.height)
                    new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)
            doc_ind.save(caminho_pdf_cropped)

            with open(caminho_pdf_poppler, "w", encoding="utf-8") as f:
                for i, page in enumerate(doc_ind, start=1):
                    texto = page.get_text("text") or ""

                    f.write(f"========== PAGE {i} ==========\n")
                    f.write(texto.strip())
                    f.write("\n\n")
            doc_ind.close()


        else:
            print(f"[Neoenergia] Página {i + 1} ignorada: tipo não reconhecido (score={score_pagina}).")


    new_doc.close()
    doc.close()  

    return 
