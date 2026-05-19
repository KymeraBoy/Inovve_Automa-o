import os
import re
import fitz


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


def cropper_logic_neoenergiaPE(input_path, output_path, template):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    recortes = None
    novo_nome = None

    for i in range(len(doc)):
        page = doc.load_page(i)
        recortes = template["TESTE"]

        # RECONHECIMENTO DE PÁGINA
        textos_teste = []
        for r in recortes:
            area_teste = fitz.Rect(r[0], r[1], r[2], r[3])
            texto_recorte = page.get_text(clip=area_teste).strip()
            textos_teste.append(texto_recorte)

        texto_teste = "\n".join(textos_teste)
        texto_teste_upper = texto_teste.upper()
        if "DOCUMENTO PARA PAGAMENTO DA CONTA COLETIVA" in texto_teste_upper:
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

            print(f"[Neoenergia][Pagina {i + 1}] TESTE_1: {textos_teste[0] if len(textos_teste) > 0 else ''}")
            print(f"[Neoenergia][Pagina {i + 1}] AGRUPADA_CLIENTE: {textos_agrupada[0] if len(textos_agrupada) > 0 else ''}")
            print(f"[Neoenergia][Pagina {i + 1}] AGRUPADA_REFERENCIA: {textos_agrupada[1] if len(textos_agrupada) > 1 else ''}")
            print(f"[Neoenergia][Pagina {i + 1}] AGRUPADA_CODIGO: {textos_agrupada[2] if len(textos_agrupada) > 2 else ''}")
        elif "ACESSE WWW.NEOENERGIA.COM E CONFIRA NOSSO AVISO DE PRIVACIDADE." in texto_teste_upper:
            print(f"[Neoenergia][Pagina {i + 1}] TESTE_2: {textos_teste[1] if len(textos_teste) > 1 else ''}")
        else:
            print(f"[Neoenergia][Pagina {i + 1}] TESTE: {texto_teste}")
            # Crop com INDIVIDUAL_NEW
            recortes_ind = template["INDIVIDUAL_NEW"]
            textos_ind = []
            for r in recortes_ind[:3]:
                recorte = fitz.Rect(r[0], r[1], r[2], r[3])
                texto_recorte = page.get_text(clip=recorte).strip()
                textos_ind.append(texto_recorte)

                municipio_frase = _linha_valida(textos_ind[0], 1)
                municipio = municipio_frase.split()[-1] if municipio_frase else "MUNICIPIO"
            mes_ano = _linha_valida(textos_ind[1], 1)
            unidade = _linha_valida(textos_ind[2], 1)
            nome_base = f"{municipio}-{mes_ano}-{unidade}".replace("/", "_").replace("\\", "_")
            nome_base = re.sub(r"[^\w\-_\. ]", "_", nome_base).strip(" -_.")
            nome_pdf = f"{nome_base}.pdf"

            pasta_original = os.path.dirname(input_path)
            nome_pasta = os.path.basename(pasta_original)
            subpasta = os.path.join(pasta_original, nome_pasta + "-INDIVIDUAIS")
            os.makedirs(subpasta, exist_ok=True)

            caminho_pdf = os.path.join(subpasta, nome_pdf)
            contador = 1
            while os.path.exists(caminho_pdf):
                nome_pdf = f"{nome_base} - Copia{'' if contador == 1 else f' {contador}'}.pdf"
                caminho_pdf = os.path.join(subpasta, nome_pdf)
                contador += 1

            # Crop e salva
            doc_ind = fitz.open()
            for r in recortes_ind:
                recorte = fitz.Rect(r[0], r[1], r[2], r[3])
                if recorte.width > 0 and recorte.height > 0:
                    new_page = doc_ind.new_page(width=recorte.width, height=recorte.height)
                    new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)
            doc_ind.save(caminho_pdf)
            doc_ind.close()

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
