import os
import re
import fitz


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


def _resolver_caminho_duplicado(caminho, caminho_atual=None):
    pasta, nome_arquivo = os.path.split(caminho)
    nome_base, extensao = os.path.splitext(nome_arquivo)
    candidato = caminho
    contador = 0

    while os.path.exists(candidato) and os.path.normcase(candidato) != os.path.normcase(caminho_atual or ""):
        contador += 1
        sufixo = " - Copia" if contador == 1 else f" - Copia {contador}"
        candidato = os.path.join(pasta, f"{nome_base}{sufixo}{extensao}")

    return candidato


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


def _extrair_texto_de_pdf(caminho_pdf):
    with fitz.open(caminho_pdf) as documento:
        partes = [pagina.get_text("text") for pagina in documento]
    partes_validas = [parte.strip("\r\n") for parte in partes if parte and parte.strip()]
    if not partes_validas:
        return ""
    if len(partes_validas) == 1:
        return partes_validas[0].strip() + "\n"

    blocos = []
    for indice, parte in enumerate(partes_validas, start=1):
        blocos.append(parte)
        if indice < len(partes_validas):
            blocos.append(f"\n===== FIM_PAGINA_{indice} | INICIO_PAGINA_{indice + 1} =====\n")
    return "\n".join(blocos).strip() + "\n"


def _normalizar_nome_por_tag(nome_base, tag):
    nome_limpo = re.sub(r"(?:_(?:Cropped|Poppler))+\Z", "", nome_base, flags=re.IGNORECASE)
    return f"{nome_limpo}_{tag}"


def _salvar_txt_poppler_individual(caminho_pdf_individual, pasta_poppler=None):
    base_pdf = os.path.splitext(os.path.basename(caminho_pdf_individual))[0]
    nome_txt = _normalizar_nome_por_tag(base_pdf, "Poppler") + ".txt"
    pasta_destino = pasta_poppler or os.path.dirname(caminho_pdf_individual)
    os.makedirs(pasta_destino, exist_ok=True)
    caminho_txt = os.path.join(pasta_destino, nome_txt)
    caminho_txt = _resolver_caminho_duplicado(caminho_txt)
    texto_fatura = _extrair_texto_de_pdf(caminho_pdf_individual)

    with open(caminho_txt, "w", encoding="utf-8") as arquivo_txt:
        arquivo_txt.write(texto_fatura or "")

    return caminho_txt


def cropper_logic_neoenergiaPE(input_path, output_path, template, output_poppler_dir=None):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    recortes = None
    novo_nome = None
    pasta_cropped = os.path.dirname(output_path)

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

            pasta_original = os.path.dirname(input_path)
            nome_pasta = os.path.basename(pasta_original)
            subpasta = os.path.join(pasta_original, nome_pasta + "-INDIVIDUAIS")
            os.makedirs(subpasta, exist_ok=True)

            caminho_pdf_original = _resolver_caminho_duplicado(os.path.join(subpasta, nome_pdf))

            nome_pdf_cropped = nome_pdf.replace(".pdf", "_Cropped.pdf")
            caminho_pdf_cropped = _resolver_caminho_duplicado(os.path.join(pasta_cropped, nome_pdf_cropped))

            # Salva a página individual completa na pasta de faturas originais.
            doc_original = fitz.open()
            page_original = doc_original.new_page(width=page.rect.width, height=page.rect.height)
            page_original.show_pdf_page(page_original.rect, doc, i)
            doc_original.save(caminho_pdf_original)
            doc_original.close()

            # Salva a versão recortada da fatura individual na pasta Cropped do município.
            doc_ind = fitz.open()
            for r in recortes_ind:
                recorte = fitz.Rect(r[0], r[1], r[2], r[3])
                if recorte.width > 0 and recorte.height > 0:
                    new_page = doc_ind.new_page(width=recorte.width, height=recorte.height)
                    new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)
            doc_ind.save(caminho_pdf_cropped)
            doc_ind.close()

            # Gera o TXT da fatura individual a partir da versão recortada.
            _salvar_txt_poppler_individual(caminho_pdf_cropped, output_poppler_dir)
        else:
            print(f"[Neoenergia] Página {i + 1} ignorada: tipo não reconhecido (score={score_pagina}).")

    if novo_nome:
        dir_path = os.path.dirname(output_path)
        output_path = os.path.join(dir_path, novo_nome.replace(".pdf", "_Cropped.pdf"))
        output_path = _resolver_caminho_duplicado(output_path)

    if len(new_doc) > 0:
        new_doc.save(output_path)
    new_doc.close()
    doc.close()

    if novo_nome:
        dir_path = os.path.dirname(input_path)
        new_input_path = os.path.join(dir_path, novo_nome)
        new_input_path = _resolver_caminho_duplicado(new_input_path, input_path)
        if input_path != new_input_path:
            os.rename(input_path, new_input_path)

    return output_path
