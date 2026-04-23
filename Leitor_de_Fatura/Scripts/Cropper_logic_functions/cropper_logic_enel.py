import fitz


def cropper_logic_enel(input_path, output_path, template):
    """
    Essa função serve apenas para aplicar os cortes no modelo de fatura agrupada da Enel.
    """
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    for i in range(len(doc)):
        if i == 0:
            continue
        if i == 1:
            recortes = template["RESUMO"]
        elif i % 2 == 0:
            recortes = template["INDIVIDUAL_FRENTE"]
        else:
            continue

        for r in recortes:
            recorte = fitz.Rect(r[0], r[1], r[2], r[3])
            if recorte.width > 0 and recorte.height > 0:
                new_page = new_doc.new_page(width=recorte.width, height=recorte.height)
                new_page.show_pdf_page(new_page.rect, doc, i, clip=recorte)

    if len(new_doc) > 0:
        new_doc.save(output_path)
    new_doc.close()
    doc.close()
    return output_path
