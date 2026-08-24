# ============================================================= #
# BIBLIOTECAS
# ============================================================= #

import re
import cv2
import fitz
import subprocess
import numpy as np

from pathlib import Path

# ============================================================= #
# CONFIGURAÇÕES
# ============================================================= #

Gabaritos = Path(r"C:\Users\Usuário 1\Documents\Inovve_Automação\LEITOR DE FATURAS\Gabaritos Energisa")

# ============================================================= #
# FUNÇÕES
# ============================================================= #

# PRIMEIRA PARTE - RENOMEIAR O DOCUMENTO
def extrair_texto(doc):
    texto_completo = ""
    for pagina in doc:
        texto_completo += pagina.get_text()
    return texto_completo

def aplicar_recortes(template, layout, new_doc, doc):
    recortes = template[layout]
    for r in recortes:
        recorte = fitz.Rect(r[0], r[1], r[2], r[3])
        if recorte.width > 0 and recorte.height > 0:
            new_page = new_doc.new_page(width=recorte.width,height=recorte.height)
            new_page.show_pdf_page(new_page.rect,doc,clip=recorte)
  
def aplicar_poppler(caminho_pdf, caminho_txt, caminho_pdftotext):
  
    # Verifica se o PDF existe
    if not caminho_pdf.is_file():
        raise FileNotFoundError(f"PDF não encontrado: {caminho_pdf}")

    # Verifica se o pdftotext existe
    if not caminho_pdftotext.is_file():
        raise FileNotFoundError(f"pdftotext não encontrado: {caminho_pdftotext}")

    # Cria a pasta de destino, caso não exista
    caminho_txt.parent.mkdir(parents=True, exist_ok=True)

    # Primeiro, extrai todo o texto do PDF para descobrir as páginas
    resultado = subprocess.run(
        [
            str(caminho_pdftotext),
            "-f", "1",
            "-l", "999999",
            "-layout",
            str(caminho_pdf),
            "-"
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if resultado.returncode != 0:
        raise RuntimeError(f"Erro ao executar pdftotext:\n{resultado.stderr}")

    # ---------------------------------------------------------
    # Para numerar corretamente cada página, fazemos a extração
    # página por página até que não haja mais páginas.
    # ---------------------------------------------------------

    with caminho_txt.open("w", encoding="utf-8") as arquivo_txt:

        pagina = 1

        while True:

            resultado = subprocess.run(
                [
                    str(caminho_pdftotext),
                    "-f", str(pagina),
                    "-l", str(pagina),
                    "-layout",
                    str(caminho_pdf),
                    "-"
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )

            # Quando a página não existe mais, encerramos
            if resultado.returncode != 0:
                break

            texto = resultado.stdout.strip()

            # Se não houver conteúdo e já estivermos além
            # do final do documento, encerramos.
            if not texto and pagina > 1:
                break

            # Divisão da página com numeração de 3 dígitos
            arquivo_txt.write(
                f"========== PAGE {pagina:03d} ==========\n\n"
            )

            arquivo_txt.write(texto)
            arquivo_txt.write("\n\n")

            pagina += 1

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
    
    municipio_match = re.findall(
    r"^([^\r\n]*?)\s*\(AG:\s*\d{1,3}\)",
    texto,
    re.MULTILINE
    )

    if "DOMICÍLIO DE ENTREGA" not in texto and not municipio_match:
        return "SEM DOMICÍLIO DE ENTREGA"

    municipio_str = municipio_match[1].strip() if municipio_match else ""

    municipio_str = re.sub(
    r"\s+(?:[-/]\s*)?[A-Za-z]{2}$",
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

def gerar_nome(municipio, mes, uc):
    valores = [municipio, mes, uc]

    partes = []

    for valor in valores:
        valor = "".join(
            c if c.isalnum() else "*"
            for c in valor
        )

        valor = re.sub(r"\*+", "_", valor)
        valor = valor.strip("_")

        partes.append(valor)

    nome = "-".join(partes)

    return nome

def renomear_arquivo(input_path: Path, nome: str) -> Path:
    novo_nome = input_path.with_name(f"{nome}.pdf")
    contador = 1
    while novo_nome.exists():
        novo_nome = input_path.with_name(f"{nome}_{contador}.pdf")
        contador += 1
    input_path.rename(novo_nome)
    return 

def obter_caminho_unico(dir_path: Path, cropped_name: str) -> Path:
    """Monta um caminho único para evitar sobrescrita de arquivos recortados."""
    base_path = Path(dir_path) / cropped_name
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    new_path = base_path.with_name(f"{stem}-copia{suffix}")
    while new_path.exists():
        new_path = base_path.with_name(f"{stem}-copia({counter}){suffix}")
        counter += 1
    return new_path

# SEGUNDA PARTE - IDENTIFICAR O LAYOUT
def pdf_para_imagem_gray(doc: fitz.Document, dpi: int = 100) -> np.ndarray:

    page = doc[0]

    escala = dpi / 72
    matriz = fitz.Matrix(escala, escala)

    pix = page.get_pixmap(
        matrix=matriz,
        colorspace=fitz.csGRAY,
        alpha=False
    )

    imagem = np.frombuffer(
        pix.samples,
        dtype=np.uint8
    ).reshape(
        pix.height,
        pix.width
    )

    return imagem.copy()

def extrair_pontos_chave(imagem: np.ndarray):
    """Extrai os descritores gráficos da imagem usando o algoritmo ORB."""
    # Aplica um leve desfoque para suavizar pequenos ruídos de texto e focar na estrutura
    blur = cv2.GaussianBlur(imagem, (5, 5), 0)
    
    # Binarização/Limiarização para destacar apenas linhas, caixas e blocos gráficos
    _, thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY_INV)
    
    orb = cv2.ORB_create(nfeatures=1000)
    keypoints, descriptors = orb.detectAndCompute(thresh, None)
    return keypoints, descriptors

def comparar_layouts_graficos(img_fatura: np.ndarray, img_gabarito: np.ndarray) -> float:
    """
    Compara duas imagens graficamente e retorna uma pontuação de similaridade.
    Quanto maior o score, mais parecidos são os layouts.
    """
    _, desc_fatura = extrair_pontos_chave(img_fatura)
    _, desc_gabarito = extrair_pontos_chave(img_gabarito)

    if desc_fatura is None or desc_gabarito is None:
        return 0.0

    # Agrupador de correspondências gráficas (BFMatcher)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(desc_fatura, desc_gabarito)

    # Ordena as correspondências por distância (menor distância = maior similaridade visual)
    matches = sorted(matches, key=lambda x: x.distance)

    # Considera apenas os 15% melhores pontos de correspondência estrutural
    top_matches = matches[:max(1, int(len(matches) * 0.15))]
    
    # Calcula a pontuação baseada na qualidade visual das correspondências
    if not top_matches:
        return 0.0
    
    distancia_media = sum(m.distance for m in top_matches) / len(top_matches)
    score_similaridade = len(top_matches) / (distancia_media + 1e-5)
    
    return score_similaridade

def classificar_modelo_graficamente(doc: fitz.Document, caminho_cache: Path) -> str:
    if not caminho_cache.is_dir():
        raise FileNotFoundError(f"Cache de gabaritos não encontrado:    {caminho_cache}")

    arquivos_gabaritos = sorted(caminho_cache.glob("*.npy"))

    if not arquivos_gabaritos:
        raise ValueError(f"Nenhum gabarito .npy encontrado em:          {caminho_cache}")

    # Converte somente a fatura que está sendo analisada
    img_analise = pdf_para_imagem_gray(doc)

    resultados = []

    for caminho_gabarito in arquivos_gabaritos:
        # Carrega diretamente a imagem já processada
        img_gabarito = np.load(caminho_gabarito)
        score = comparar_layouts_graficos(img_analise, img_gabarito)
        resultados.append((caminho_gabarito, score))
    melhor_gabarito = max(resultados,key=lambda resultado: resultado[1])

    return melhor_gabarito[0].stem

# ============================================================= #
# EXECUÇÃO
# ============================================================= #

def cropper_logic_energisa(input_path, pasta_cropper, pasta_poppler, template, Poppler):
    # input_path - Endereço do arquivo PDF que será processado
    # pasta_cropper - Endereço da pasta onde o PDF cortado será salvo
    # pasta_poppler - Endereço da pasta onde o arquivo de texto será salvo 


    doc     = fitz.open(input_path)
    doc_new = fitz.open()

    # CLASSIFICAÇÃO DO LAYOUT   
    layout      = classificar_modelo_graficamente(doc, Gabaritos)

    #CRIAÇÃO DO NOVO NOME DO DOCUMENTO
    texto       = extrair_texto(doc)
    uc          = extrair_uc_energisa(texto)
    municipio   = extrair_municipio_energisa(texto)
    mes         = extrair_mes_energisa(texto)
    nome        = gerar_nome(municipio, mes, uc)

    # GERANDO ENDEREÇOS DOS ARQUIVOS CQUE SERÃO CRIADOS
    nome_pdf_cropped = f"{nome}_Cropped.pdf"
    nome_txt_poppled = f"{nome}_Poppler.txt"
    caminho_pdf_cropped = obter_caminho_unico(Path(pasta_cropper), nome_pdf_cropped)
    caminho_txt_poppled = obter_caminho_unico(Path(pasta_poppler), nome_txt_poppled)

    # APLICAÇÃO DOS RECORTES 
    aplicar_recortes(template, layout, doc_new, doc)

    # SALVANDO O PDF CORTADO E RENOMEANDO O DOCUMENTO ORIGINAL
    if len(doc_new) > 0:
        doc_new.save(caminho_pdf_cropped)
    doc_new.close()    
    doc.close()
    renomear_arquivo(input_path, nome)    

    aplicar_poppler(caminho_pdf_cropped, caminho_txt_poppled, Poppler)    
    
    return 
