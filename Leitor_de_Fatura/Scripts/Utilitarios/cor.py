import fitz  # PyMuPDF
from PIL import Image
import io
import matplotlib.pyplot as plt

# ===== CONFIG =====
FATOR_SIMPLIFICACAO = 32
REDUCAO_IMAGEM = (100, 100)


def simplificar_cor(cor, fator=FATOR_SIMPLIFICACAO):
    return tuple((c // fator) * fator for c in cor)


def extrair_cores(pdf_path):
    doc = fitz.open(pdf_path)
    cores = set()

    for page in doc:

        # ===== VETORES =====
        desenhos = page.get_drawings()
        for d in desenhos:
            if "color" in d and d["color"]:
                cor = tuple(int(c * 255) for c in d["color"])
                cores.add(simplificar_cor(cor))

            if "fill" in d and d["fill"]:
                cor = tuple(int(c * 255) for c in d["fill"])
                cores.add(simplificar_cor(cor))

        # ===== TEXTO =====
        blocos = page.get_text("dict")["blocks"]
        for bloco in blocos:
            if "lines" in bloco:
                for linha in bloco["lines"]:
                    for span in linha["spans"]:
                        cor = span.get("color")
                        if cor is not None:
                            r = (cor >> 16) & 255
                            g = (cor >> 8) & 255
                            b = cor & 255
                            cores.add(simplificar_cor((r, g, b)))

        # ===== IMAGENS =====
        imagens = page.get_images(full=True)
        for img in imagens:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image = image.resize(REDUCAO_IMAGEM)

            for pixel in image.getdata():
                cores.add(simplificar_cor(pixel))

    return cores


# ===== MOSTRAR TEXTO =====
def mostrar_cores(nome, cores):
    print(f"\n🎨 Cores em {nome}:")
    for cor in sorted(cores):
        print(f"RGB{cor} | HEX #{cor[0]:02X}{cor[1]:02X}{cor[2]:02X}")
    print(f"Total: {len(cores)}")


# ===== VISUALIZAR CORES =====
def mostrar_paleta(nome, cores):
    cores = list(cores)

    cols = 10
    rows = (len(cores) // cols) + 1

    fig, ax = plt.subplots(figsize=(cols, rows))
    ax.set_title(nome)

    for i, cor in enumerate(cores):
        r, g, b = cor
        col_x = i % cols
        row_y = i // cols
        ax.add_patch(plt.Rectangle(
            (col_x, row_y),
            1, 1,
            color=(r/255, g/255, b/255)
        ))
        # Escolhe cor do texto (preto ou branco) para contraste
        luminancia = 0.299 * r + 0.587 * g + 0.114 * b
        cor_texto = "black" if luminancia > 128 else "white"
        ax.text(
            col_x + 0.5, row_y + 0.5,
            f"#{r:02X}{g:02X}{b:02X}",
            ha="center", va="center",
            fontsize=5, color=cor_texto
        )

    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.invert_yaxis()

    plt.show()


# ===== COMPARAÇÃO =====
def comparar_pasta(pasta):
    import os
    pdfs = sorted([os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith(".pdf")])

    if not pdfs:
        print("⚠️  Nenhum PDF encontrado na pasta.")
        return

    print(f"🔍 Processando {len(pdfs)} PDFs...\n")

    # Extrai cores de cada PDF
    cores_por_pdf = {}
    for pdf in pdfs:
        nome = os.path.basename(pdf)
        print(f"  Extraindo cores: {nome}")
        cores_por_pdf[nome] = extrair_cores(pdf)

    # Combina as paletas e monta um mapa invertido: cor -> PDFs onde ela aparece
    pdfs_por_cor = {}
    for nome, cores in cores_por_pdf.items():
        for cor in cores:
            pdfs_por_cor.setdefault(cor, []).append(nome)

    total_pdfs = len(cores_por_pdf)
    cores_filtradas = {
        cor: arquivos
        for cor, arquivos in pdfs_por_cor.items()
        if len(arquivos) < total_pdfs
    }

    print(f"\n📊 Paleta combinada da pasta sem cores comuns a todos os PDFs ({len(cores_filtradas)} cor(es) encontrada(s)):\n")
    for cor in sorted(cores_filtradas):
        r, g, b = cor
        arquivos = sorted(cores_filtradas[cor])
        print(f"RGB{cor} | HEX #{r:02X}{g:02X}{b:02X}")
        print(f"  Presente em {len(arquivos)} PDF(s):")
        for arquivo in arquivos:
            print(f"    • {arquivo}")

    if cores_filtradas:
        mostrar_paleta("Paleta combinada filtrada da pasta", sorted(cores_filtradas))
    else:
        print("\nNenhuma cor restante: todas as cores encontradas aparecem em todos os PDFs da pasta.")


# Pasta com os PDFs
PASTA = r"C:\Users\arthu\Documents\GitHub\Inovve_Automa-o\Leitor_de_Fatura\Faturas\Layouts"
comparar_pasta(PASTA)
