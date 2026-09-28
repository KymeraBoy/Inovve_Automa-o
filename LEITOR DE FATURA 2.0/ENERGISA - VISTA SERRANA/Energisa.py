# ==============================================================================
# 1. BIBLIOTECAS
# ==============================================================================
from pathlib import Path
import re
import shutil
import subprocess
import pandas as pd
import numpy as np
import fitz


# ==============================================================================
# 2. DEFINIÇÕES DE VARIÁVEIS E FUNÇÕES
# ==============================================================================
# Ative ou desative o modo de desenvolvimento aqui
MODO_DESENVOLVIMENTO = True

# Diretório atual (onde o script, faturas e a planilha final estarão)
DIRETORIO_ATUAL = Path(__file__).parent if "__file__" in locals() else Path.cwd()

# Pasta onde ficam os gabaritos (.npy)
PASTA_GABARITOS = DIRETORIO_ATUAL / "Gabaritos Energisa"

# Caminho exato do executável do Poppler: \Poppler\Library\bin\pdftotext.exe
CAMINHO_PDFTOTEXT = DIRETORIO_ATUAL / "Poppler" / "Library" / "bin" / "pdftotext.exe"

# Caminho da planilha de saída na mesma pasta do script
NOME_PLANILHA_SAIDA = DIRETORIO_ATUAL / "Resultado_Energisa.xlsx"

# Caminho do arquivo txt gerado no modo de desenvolvimento
ARQUIVO_TXT_TESTE = DIRETORIO_ATUAL / "primeiro_pdf_extraido.txt"

# Pastas de saída exclusivas do modo de desenvolvimento
PASTA_PDFS_RECORTADOS = DIRETORIO_ATUAL / "PDFs recortados - desenvolvimento"
PASTA_TXTS_DESENVOLVIMENTO = DIRETORIO_ATUAL / "TXTs - desenvolvimento"

# Dicionário com as coordenadas dos cortes [x0, y0, x1, y1] por layout
CORTES_LAYOUTS = {
     "L1": [
            [0.0, 0.0, 195.27, 90.56],                 # DOMICILIO, CLIENTE, SUBGRUPO, CLASSE, MEDIDOR E FORNECIMENTO
            [0.0, 107.54, 367.9, 608.51],              # BLOCO PRINCIPAL
            [0.0, 611.28, 215.08, 716.01],             # INDICADORES DE QUALIDADE
            [215.08, 611.28, 367.9, 716.01],           # COMPOSICAO DO CONSUMO
            [0.0, 713.16, 274.51, 826.36],             # ATENCAO
            [274.51, 713.16, 367.9, 826.36],            # FATURAS EM ATRASO
            [0.0, 832.02, 367.9, 945.22],              # DADOS FISCAIS
        ],
        "L2": [
            [0.0, 0.0, 234.3523, 87.73],               # MUNICIPIO, CLASSIFICACAO E FASES
            [188.195, 55.9774, 348.7409, 89.9374],     # UNIDADE CONSUMIDORA
            [21.3382, 113.2, 181.5345, 188.1167],      # REFERENCIA E VALOR DA FATURA
            [183.95, 113.2, 344.1463, 188.1167],       # VENCIMENTO E CONSUMO
            [0.0, 192.44, 359.41, 263.25],             # SITUACAO DE DEBITOS
            [183.95, 447.14, 362.24, 546.29],          # COMPOSICAO DO CONSUMO
            [0.0, 448.6965, 95.7106, 534.7568],        # HISTORICO DE CONSUMO
            [95.7106, 459.6203, 181.7709, 516.2203],   # DADOS DE MEDICAO
            [0.0, 273.2648, 368.5511, 435.8949],       # DADOS DO FATURAMENTO
            [0.0, 555.3309, 283.6226, 590.4512],       # INDICADORES DE QUALIDADE
            [0.0, 588.64, 367.9, 747.12],              # ATENCAO
            [0.0, 755.61, 367.9, 914.09],              # DADOS FISCAIS
        ],
        "L3": [
            [0.0, 0.0, 189.61, 93.39],                 # MUNICIPIO, CNPJ, MEDIDOR, FORNECIMENTO E CLASSE
            [0.0, 113.2, 175.46, 192.54],              # REFERENCIA E VALOR DA FATURA
            [175.46, 113.2, 350.92, 192.54],           # VENCIMENTO E CONSUMO
            [0.0, 198.1, 367.9, 274.51],               # SITUACAO DE DEBITOS
            [185.5065, 56.6566, 345.0063, 90.6166],    # UNIDADE CONSUMIDORA
            [183.95, 455.63, 365.07, 551.95],          # COMPOSICAO DO CONSUMO
            [0.0, 457.7808, 94.4371, 546.1908],        # HISTORICO DE CONSUMO
            [97.0973, 468.2801, 183.6102, 527.8201],   # DADOS DE MEDICAO
            [0.0, 277.5664, 368.0698, 442.6937],       # DADOS DO FATURAMENTO
            [0.0, 565.434, 279.9153, 600.8373],        # INDICADORES DE QUALIDADE
            [0.0, 599.96, 367.9, 758.44],              # ATENCAO
            [0.0, 911.26, 367.9, 1052.7],              # DADOS FISCAIS
        ],
        "L4": [
            [37.8654, 50.94, 372.1354, 113.22],        # DOMICILIO DE ENTREGA
            [37.8654, 110.37, 372.1354, 135.84],       # CLASSIFICACAO E FORNECIMENTO
            [37.8654, 147.16, 227.4254, 232.06],       # CLIENTE
            [37.8654, 232.06, 326.5254, 268.85],       # MES/ANO, VENCIMENTO E VALOR
            [37.8654, 271.68, 533.2154, 328.28],       # INFORMACOES
            [0.0, 325.45, 424.5, 543.36],              # ITENS DA FATURA
            [0.0, 540.53, 314.13, 599.96],             # DADOS DE MEDICAO
            [0.0, 597.13, 532.04, 755.61],             # DADOS FISCAIS
            [373.56, 50.94, 532.04, 135.84],           # APRESENTACAO
            [328.28, 141.5, 532.04, 181.12],           # DATAS DE LEITURA
            [226.4, 181.12, 325.45, 234.89],           # CODIGO DO CLIENTE E INSTALACAO
            [424.5, 325.45, 537.7, 379.22],            # IMPOSTOS
            [424.5, 384.88, 537.7, 537.7],             # HISTORICO DE CONSUMO
            [314.13, 537.7, 532.04, 597.13],           # RESERVADO AO FISCO
        ],
        "L4_VERSO": [
            [33.96, 16.98, 333.94, 147.16],            # ATENCAO
            [33.96, 152.82, 155.65, 291.49],           # INDICADORES DE QUALIDADE
            [33.96, 288.66, 181.12, 447.14],           # COMPOSICAO DO CONSUMO
            [339.6, 16.98, 529.21, 147.16],            # SITUACAO DE DEBITOS
            [158.48, 152.82, 526.38, 291.49],          # CONSUMO DOS ULTIMOS 13 MESES
            [183.95, 288.66, 529.21, 447.14],          # ESTRUTURA DO CONSUMO
        ],
        "L5": [
            [25.47, 42.45, 314.13, 254.7],             # DOMICILIO DE ENTREGA E CLIENTE
            [325.45, 164.14, 469.78, 198.1],           # UNIDADE CONSUMIDORA
            [25.47, 251.87, 144.33, 350.92],           # VALOR, REFERENCIA E CNPJ
            [147.16, 251.87, 288.66, 350.92],          # VENCIMENTO, CONSUMO E RESERVADO AO FISCO
            [283.0, 251.87, 517.89, 311.3],            # SITUACAO DE DEBITOS
            [283.0, 311.3, 546.19, 350.92],            # DATAS DE EMISSAO/APRESENTACAO/PROXIMA LEITURA
            [25.47, 348.09, 515.06, 574.49],           # DESCRITIVO
            [25.47, 577.32, 515.06, 778.25],           # INFORMACOES FISCAIS
        ],
        "L5_VERSO": [
            [33.96, 16.98, 316.96, 147.16],            # ATENCAO
            [33.96, 152.82, 150.0, 291.49],            # INDICADORES DE QUALIDADE
            [33.96, 288.66, 171.215, 447.14],          # COMPOSICAO DO CONSUMO
            [311.3, 16.98, 500.91, 147.16],            # CANAL DE CONTATO
            [147.16, 152.82, 515.06, 291.49],          # CONSUMO DOS ULTIMOS 13 MESES
            [169.8, 288.66, 515.06, 447.14],           # ESTRUTURA DO CONSUMO
        ],
        "L6": [
            [28.3, 0.0, 198.1, 96.22],                 # DOMICILIO DE ENTREGA
            [192.44, 0.0, 413.18, 96.22],              # CLIENTE
            [28.3, 110.37, 548.83, 164.14],            # REFERENCIA/APRESENTACAO/PROXIMA LEITURA/UC
            [28.3, 169.8, 548.83, 399.03],             # DEMONSTRATIVO
            [28.3, 401.86, 203.76, 523.55],            # COMPOSICAO DO CONSUMO
            [195.27, 401.86, 537.7, 523.55],           # VENCIMENTO, TOTAL E RESERVADO AO FISCO
            [28.3, 537.7, 548.83, 752.78],             # DADOS FISCAIS
        ],
        "L6_VERSO": [
            [28.3, 0.0, 223.57, 144.33],               # CANAL DE CONTATO
            [28.3, 155.65, 390.54, 291.49],            # CONSUMO DOS ULTIMOS 12 MESES
            [28.3, 305.64, 393.37, 441.48],            # ESTRUTURA DO CONSUMO
            [215.08, 0.0, 305.64, 144.33],             # FATURAS EM ATRASO
            [308.47, 0.0, 517.89, 144.33],             # ATENCAO
            [393.37, 288.66, 512.23, 444.31],          # INDICADORES DE QUALIDADE
        ],
        "L7": [
            [15.3952, 97.1822, 223.4185, 173.5622],    # MUNICIPIO
            [21.6212, 181.4596, 310.2812, 202.4865],   # REFERENCIA, VENCIMENTO E TOTAL
            [229.5413, 108.1626, 347.3269, 164.7626],  # UNIDADE CONSUMIDORA E CODIGO DA INSTALACAO
            [18.112, 67.9483, 219.8627, 86.0683],      # CLASSIFICACAO
            [219.5514, 67.9483, 346.7882, 86.0683],    # TIPO DE FORNECIMENTO
            [0.0, 308.47, 367.9, 413.18],              # INFORMACOES
            [0.0, 415.99, 367.9, 458.46],              # DATAS DE LEITURA
            [9.9333, 468.365, 358.2929, 601.5014],     # DADOS DO FATURAMENTO
            [181.5445, 608.1104, 349.1937, 669.3412],  # TRIBUTOS
            [19.9515, 706.7642, 348.656, 756.7187],    # DADOS DE MEDICAO
            [39.6483, 618.2984, 161.6263, 703.3116],   # HISTORICO DE CONSUMO
            [189.61, 667.88, 359.41, 696.18],          # RESERVADO AO FISCO
            [0.0, 752.78, 367.9, 826.36],              # SITUACAO DE DEBITOS
            [0.0, 826.36, 367.9, 959.37],              # DADOS FISCAIS
        ],
        "L7_VERSO": [
            [0.0, 0.0, 283.0, 283.0],                  # FILL
        ],        
}


# ==============================================================================
# 2.1 FUNÇÕES DE EXTRAÇÃO DE INFORMAÇÕES (CAMPO A CAMPO)
# ==============================================================================

def extrair_municipio(texto: str) -> str:
    """
    Extrai o nome do município a partir do bloco do DOMICÍLIO DE ENTREGA.
    
    Exemplo de entrada:
        DOMICÍLIO DE ENTREGA
        PREFEITURA MUNICIPAL DE VISTA SERRANA
        RUA ABÍLIO GARCIA SN - CEP:58710000 - CENTRO
        VISTA SERRANA PB (AG: 118)
    """
    if not texto:
        return "N/A"

    # Padrão 1: Procura a linha com "NOME DO MUNICIPIO UF (AG: XXX)" ou "NOME UF"
    # Exemplo: VISTA SERRANA PB (AG: 118) -> Pega 'VISTA SERRANA'
    match_uf = re.search(r"([A-ZÀ-Ú\s]+)\s+[A-Z]{2}\s*(?:\(AG:|\b)", texto)
    if match_uf:
        municipio = match_uf.group(1).strip()
        # Evita capturar termos de cabeçalho como 'DOMICILIO DE ENTREGA' se estiver na mesma linha
        if "DOMICÍLIO" not in municipio and "ENTREGA" not in municipio and len(municipio) > 2:
            return municipio

    # Padrão 2 (Fallback): Procura após "PREFEITURA MUNICIPAL DE"
    match_pref = re.search(r"PREFEITURA\s+MUNICIPAL\s+DE\s+([A-ZÀ-Ú\s]+)", texto, re.IGNORECASE)
    if match_pref:
        return match_pref.group(1).strip()

    return "Não encontrado"


# ==============================================================================
# 2.2 FUNÇÕES DE PROCESSAMENTO DE PDF E POPPLER
# ==============================================================================

# --- ETAPA 1: IDENTIFICAÇÃO DO LAYOUT ---
def identificar_layout(caminho_pdf: Path, pasta_gabaritos: Path) -> str:
    """
    Identifica o layout da primeira página comparando-a com os gabaritos .npy.
    """
    if not pasta_gabaritos.exists():
        return "Pasta de gabaritos não encontrada"

    gabaritos = sorted(pasta_gabaritos.glob("L[1-7].npy"))
    if not gabaritos:
        return "Nenhum gabarito .npy encontrado"

    try:
        documento = fitz.open(caminho_pdf)
        if not documento.page_count:
            return "PDF sem páginas"

        pagina = documento[0]
        proporcao_pdf = pagina.rect.width / pagina.rect.height
        melhor_layout = None
        menor_erro = float("inf")

        for caminho_gabarito in gabaritos:
            gabarito = np.asarray(np.load(caminho_gabarito, allow_pickle=False))
            if gabarito.ndim not in (2, 3) or min(gabarito.shape[:2]) == 0:
                continue

            altura, largura = gabarito.shape[:2]
            pixmap = pagina.get_pixmap(
                matrix=fitz.Matrix(largura / pagina.rect.width, altura / pagina.rect.height),
                colorspace=fitz.csRGB,
                alpha=False
            )
            imagem = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(altura, largura, 3)

            if gabarito.ndim == 3:
                gabarito = gabarito[:, :, :3].mean(axis=2)
            imagem = imagem.mean(axis=2)

            gabarito = gabarito.astype(np.float32)
            imagem = imagem.astype(np.float32)
            gabarito -= gabarito.mean()
            imagem -= imagem.mean()

            energia_gabarito = np.linalg.norm(gabarito)
            energia_imagem = np.linalg.norm(imagem)
            if energia_gabarito == 0 or energia_imagem == 0:
                continue

            correlacao = float(np.sum(gabarito * imagem) / (energia_gabarito * energia_imagem))
            proporcao_gabarito = largura / altura
            erro_proporcao = abs(proporcao_pdf - proporcao_gabarito) / proporcao_gabarito
            erro = (1 - correlacao) + erro_proporcao

            if erro < menor_erro:
                menor_erro = erro
                melhor_layout = caminho_gabarito.stem

        return melhor_layout or "Layout não identificado"
    except (OSError, ValueError, RuntimeError) as erro:
        return f"Erro ao identificar layout: {erro}"
    finally:
        if "documento" in locals():
            documento.close()


# --- ETAPA 2: APLICAÇÃO DOS RECORTE DE ACORDO COM O LAYOUT ---
def obter_cortes_layout(nome_layout: str) -> list:
    """
    Retorna a lista de coordenadas [x0, y0, x1, y1] referente ao layout informado.
    """
    return CORTES_LAYOUTS.get(nome_layout, [])


# --- ETAPA 3: CONVERTER PDF RECORTADO EM TXT ESTRUTURADO COM POPPLER ---
def extrair_texto_poppler_recortado(caminho_pdf: Path, cortes: list) -> str:
    """
    Aplica os recortes no PDF e converte cada bloco em texto estruturado
    utilizando a ferramenta pdftotext do Poppler.
    """
    if not CAMINHO_PDFTOTEXT.exists():
        return f"Erro: Executável pdftotext não encontrado em: {CAMINHO_PDFTOTEXT}"

    if not cortes:
        return "Erro: Nenhuma coordenada de corte definida para este layout."

    texto_completo = ""

    for idx, coord in enumerate(cortes):
        x0, y0, x1, y1 = coord
        
        x = int(round(x0))
        y = int(round(y0))
        w = int(round(x1 - x0))
        h = int(round(y1 - y0))

        # Executa o pdftotext com delimitadores de caixa -x -y -W -H e flag -layout
        comando = [
            str(CAMINHO_PDFTOTEXT),
            "-layout",
            "-x", str(x),
            "-y", str(y),
            "-W", str(w),
            "-H", str(h),
            str(caminho_pdf),
            "-"
        ]

        try:
            resultado = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                check=True
            )
            
            texto_bloco = resultado.stdout.strip()
            texto_completo += f"--- BLOCO {idx + 1} {coord} ---\n"
            texto_completo += texto_bloco + "\n\n"

        except subprocess.CalledProcessError as e:
            texto_completo += f"--- BLOCO {idx + 1} {coord} ---\nErro ao extrair: {e.stderr}\n\n"
        except Exception as e:
            texto_completo += f"--- BLOCO {idx + 1} {coord} ---\nErro inesperado: {e}\n\n"

    return texto_completo


def extrair_texto_pdf(caminho_pdf: Path) -> str:
    """Converte todas as páginas de um PDF em um único texto estruturado."""
    if not CAMINHO_PDFTOTEXT.exists():
        return f"Erro: Executável pdftotext não encontrado em: {CAMINHO_PDFTOTEXT}"

    comando = [
        str(CAMINHO_PDFTOTEXT),
        "-layout",
        str(caminho_pdf),
        "-"
    ]

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True
        )
        return resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Erro ao extrair texto do PDF: {e.stderr}"
    except Exception as e:
        return f"Erro inesperado ao extrair texto do PDF: {e}"


# ==============================================================================
# 3. ÁREA DE DESENVOLVIMENTO E TESTES
# ==============================================================================
def preparar_pastas_desenvolvimento():
    """Cria as pastas de desenvolvimento e remove resultados de execuções anteriores."""
    for pasta in (PASTA_PDFS_RECORTADOS, PASTA_TXTS_DESENVOLVIMENTO):
        pasta.mkdir(parents=True, exist_ok=True)
        for item in pasta.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


def adicionar_pdf_recortado(documento_origem, documento_saida, coordenadas: list):
    """Adiciona ao PDF de saída uma página contendo a área indicada."""
    pagina_origem = documento_origem[0]
    x0, y0, x1, y1 = coordenadas
    recorte = fitz.Rect(x0, y0, x1, y1)
    pagina_recortada = documento_saida.new_page(
        width=recorte.width,
        height=recorte.height
    )
    pagina_recortada.show_pdf_page(pagina_recortada.rect, documento_origem, 0, clip=recorte)


def testes_desenvolvimento(faturas_pdf: list[Path]):
    """
    Função de desenvolvimento: salva um PDF recortado e um TXT correspondente por fatura.
    """
    print("=" * 60)
    print(" [MODO DESENVOLVIMENTO ATIVO] ")
    print("=" * 60)

    if not faturas_pdf:
        print("Nenhum PDF encontrado para testes.")
        return

    for caminho_pdf in faturas_pdf:
        print(f"Inspecionando fatura de teste: {caminho_pdf.name}")

        # 1. Identificação do layout
        layout = identificar_layout(caminho_pdf, PASTA_GABARITOS)
        print(f"Layout identificado: {layout}")

        # 2. Criação de um PDF com uma página para cada recorte
        cortes = obter_cortes_layout(layout)
        caminho_pdf_recortado = PASTA_PDFS_RECORTADOS / f"{caminho_pdf.stem}_recortado.pdf"
        documento_origem = fitz.open(caminho_pdf)
        documento_saida = fitz.open()

        try:
            for idx, coordenadas in enumerate(cortes, start=1):
                adicionar_pdf_recortado(documento_origem, documento_saida, coordenadas)

            documento_saida.save(caminho_pdf_recortado)
            print(f"  PDF com {len(cortes)} páginas: {caminho_pdf_recortado.name}")

            # 3. Extração de todas as páginas do PDF recortado em um único TXT
            texto_recortado = extrair_texto_pdf(caminho_pdf_recortado)
            caminho_txt = PASTA_TXTS_DESENVOLVIMENTO / f"{caminho_pdf.stem}_recortado.txt"
            caminho_txt.write_text(texto_recortado, encoding="utf-8")
            print(f"  TXT com todas as páginas: {caminho_txt.name}")
        finally:
            documento_saida.close()
            documento_origem.close()

    print("=" * 60 + "\n")


# ==============================================================================
# 4. FLUXO PRINCIPAL
# ==============================================================================
def main():
    print(f"Diretório de trabalho: {DIRETORIO_ATUAL}")

    if MODO_DESENVOLVIMENTO:
        preparar_pastas_desenvolvimento()
    
    # Busca todas as faturas PDF no diretório do script
    faturas_pdf = list(DIRETORIO_ATUAL.glob("*.pdf"))
    
    if not faturas_pdf:
        print("Nenhuma fatura PDF encontrada no diretório atual.")
        return

    print(f"Encontradas {len(faturas_pdf)} faturas para processamento.\n")

    # Executa a inspeção e geração do .txt de teste caso o modo dev esteja True
    if MODO_DESENVOLVIMENTO:
        testes_desenvolvimento(faturas_pdf)

    # Processamento em lote das faturas
    dados_compilados = []

    for caminho_pdf in faturas_pdf:
        print(f"Processando: {caminho_pdf.name}...")
        
        # 1. Identificação do layout
        layout = identificar_layout(caminho_pdf, PASTA_GABARITOS)
        
        # 2. Aplicação dos recortes de acordo com o layout
        cortes = obter_cortes_layout(layout)
        
        # 3. Extração do texto recortado via Poppler
        texto_recortado = extrair_texto_poppler_recortado(caminho_pdf, cortes)

        # 4. Extração dos campos
        municipio = extrair_municipio(texto_recortado)

        # Montagem das informações da fatura
        dados_compilados.append({
            "Nome do PDF": caminho_pdf.name,
            "Layout": layout,
            "Município": municipio
        })

    # 5. Gerar a planilha Excel
    df = pd.DataFrame(dados_compilados)
    df.to_excel(NOME_PLANILHA_SAIDA, index=False)
    
    print(f"\nProcessamento concluído! Planilha gerada em: {NOME_PLANILHA_SAIDA.name}")


if __name__ == "__main__":
    main()