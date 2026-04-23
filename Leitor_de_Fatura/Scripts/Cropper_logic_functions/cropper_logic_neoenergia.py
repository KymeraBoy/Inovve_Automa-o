import os
import re

import fitz


def cropper_logic_neoenergiaPE(input_path, output_path, template):
    doc = fitz.open(input_path)
    new_doc = fitz.open()
    recortes = None

    for i in range(len(doc)):
        page = doc.load_page(i)
        texto = page.get_text()

        if "DOCUMENTO PARA PAGAMENTO DA CONTA COLETIVA" in texto:
            recortes = template["AGRUPADA"]
        elif "chave de acesso:" in texto:
            recortes = template["INDIVIDUAL_NEW"]
        elif "CONTA DE ENERGIA ELÉTRICA" in texto:
            recortes = template["INDIVIDUAL_OLD"]
        else:
            continue

        for r in recortes:
            recorte = fitz.Rect(r[0], r[1], r[2], r[3])
            if recorte.width > 0 and recorte.height > 0:
                new_page = new_doc.new_page(width=recorte.width, height=recorte.height)
                new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)

    novo_nome = ""
    if recortes == template["INDIVIDUAL_NEW"]:
        for i in [0, 1, 2]:
            page = new_doc.load_page(i)
            texto = page.get_text()
            linhas = texto.splitlines()
            if i == 0:
                novo_nome += re.sub("PREF MUNICIPAL DE ", "", linhas[1]) + "_"
                novo_nome = novo_nome.replace("PREFEITURA MUNICIPAL DE ", "")
            if i == 1:
                novo_nome += linhas[1] + "_"
            if i == 2:
                novo_nome += linhas[5]

    if recortes == template["INDIVIDUAL_OLD"]:
        for i in [0, 1, 2]:
            page = new_doc.load_page(i)
            texto = page.get_text()
            linhas = texto.splitlines()
            if i == 0:
                novo_nome += re.sub("PREF MUNICIPAL DE ", "", linhas[1]) + "_"
                novo_nome = novo_nome.replace("PREFEITURA MUNICIPAL DE ", "")
            if i == 1:
                novo_nome += linhas[1] + "_"
            if i == 2:
                print(texto)
                novo_nome += linhas[5]

    novo_nome = re.sub(r"[^\w\-_\. ]", "-", novo_nome) + ".pdf"

    dir_path = os.path.dirname(output_path)
    cropped_name = novo_nome.replace(".pdf", "_Cropped.pdf")
    output_path = os.path.join(dir_path, cropped_name)
    print(f"Salvando arquivo croppado como: {output_path}")

    if len(new_doc) > 0:
        new_doc.save(output_path)
    new_doc.close()
    doc.close()

    dir_path = os.path.dirname(input_path)
    new_input_path = os.path.join(dir_path, novo_nome)
    os.rename(input_path, new_input_path)
    return output_path
