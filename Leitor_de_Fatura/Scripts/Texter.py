# ============================================================== #
#     BIBLIOTECAS
# ============================================================== #

import sys
import shutil
import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

from texter_utils import salvar_arquivo, carregar_arquivo, aba_info_geral, aba_historico_consumo, historico
from Texter_format_functions.texter_format_enel import format_enel
from Texter_format_functions.texter_format_energisa import format_energisa
from Texter_format_functions.texter_format_neoenergia import format_neoenergia

# ============================================================== #
# CONFIGURACOES
# ============================================================== #

if getattr(sys, "frozen", False):
    diretorio = Path(sys.executable).resolve().parent
else:
    diretorio = Path(__file__).resolve().parent.parent

PATH_INPUT = diretorio / "Faturas_Poppler"
PATH_OUTPUT = diretorio / "Faturas_Texter"
PATH_ANALISE = diretorio / "Faturas_Analaiser"

# ============================================================== #
# FUNCOES
# ============================================================== #

def limpar_estado_processamento():
    # Evita acumular dados de execucoes anteriores na mesma sessao.
    aba_info_geral.clear()
    aba_historico_consumo.clear()
    historico.clear()

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

def selecionar_subapasta(PATH):
    subfolders = [f.name for f in PATH.iterdir() if f.is_dir()]
    print("\n--- SELECAO DE PASTA (ORIGEM: POPPLER) ---")
    for i, folder in enumerate(subfolders):
        print(f"{i} - {folder}")

    f_choice = int(input("Indice da pasta: "))
    return subfolders[f_choice]

MESES_MAP = {
    'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
}

def chave_ordenacao_mes(mes_ano):
    """Ordena os meses na horizontal da planilha (JAN, FEV, MAR...)"""
    try:
        if '/' in str(mes_ano):
            partes = str(mes_ano).split('/')
            # Se for formato numérico (ex: 01/2024) -> (Ano, Mês)
            if partes[0].isdigit():
                return (int(partes[1]), int(partes[0]))
            # Se for formato abreviado (ex: JAN/24) -> (Ano, Número_Mês)
            else:
                return (int(partes[1]), MESES_MAP.get(partes[0].upper(), 0))
    except:
        pass
    return (9999, 0)


# --- FUNÇÃO PARA GERAR A BASE DA MATRIZ ---
def gerar_base_matriz_vazia(lista_faturas_tagueadas):
    """
    Vasculha os dicionários, extrai UCs e Meses únicos, ordena-os
    e monta a estrutura base (matriz vazia) da planilha.
    """
    ucs_unicas = set()
    meses_unicos = set()

    # 1. Vasculha todos os vetores tagueados para coletar os rótulos
    for fatura in lista_faturas_tagueadas:
        uc = fatura.get("Unidade Consumidora")
        mes = fatura.get("Mês de referência")
        
        if uc:
            ucs_unicas.add(str(uc).strip())
        if mes:
            meses_unicos.add(str(mes).strip())

    # 2. Organiza e tira repetições (o 'set' já elimina duplicados, agora ordenamos)
    # UCs em ordem crescente (vertical) e Meses em ordem cronológica (horizontal)
    lista_ucs_ordenada = sorted(list(ucs_unicas))
    lista_meses_ordenada = sorted(list(meses_unicos), key=chave_ordenacao_mes)

    # 3. Monta a Estrutura Base da Matriz
    # A primeira linha será o cabeçalho completo
    matriz_base = []
    cabecalho = ["Unidade Consumidora"] + lista_meses_ordenada
    matriz_base.append(cabecalho)

    # Cria as linhas das UCs preenchidas com None (vazias) para os meses
    for uc in lista_ucs_ordenada:
        # Cria uma linha que começa com a UC e tem 'None' para cada mês do cabeçalho
        linha_vazia = [uc] + [None] * len(lista_meses_ordenada)
        matriz_base.append(linha_vazia)

    return matriz_base

def exportar_matriz_para_csv(matriz, pasta_destino, nome_arquivo="visualizacao_base.csv"):
    """
    Pega uma matriz (lista de listas) e grava em um arquivo CSV 
    usando pathlib para manipulação segura de caminhos no Windows.
    """
    # 1. Transforma a pasta de destino e o arquivo em objetos Path
    diretorio = Path(pasta_destino)
    
    # Garante que a pasta de destino exista (substitui o os.makedirs)
    diretorio.mkdir(parents=True, exist_ok=True)
    
    # Cria o caminho completo do arquivo final
    caminho_final = diretorio / nome_arquivo
    
    # 2. Abre e grava o arquivo CSV usando o objeto Path diretamente
    with caminho_final.open(mode='w', newline='', encoding='utf-8-sig') as arquivo_csv:
        escritor = csv.writer(arquivo_csv, delimiter=';')
        
        for linha in matriz:
            # Converte os 'None' para texto vazio ''
            linha_limpa = [str(item) if item is not None else '' for item in linha]
            escritor.writerow(linha_limpa)

def preencher_matriz_com_tag(matriz_base, lista_faturas_tagueadas, tag_valor):
    """
    Recebe a matriz base (esqueleto) e preenche os espaços vazios (None)
    com os valores da 'tag_valor' especificada, cruzando UC e Mês.
    """
    # 1. Fazemos uma cópia profunda da matriz base para não alterar a original
    import copy
    matriz_preenchida = copy.deepcopy(matriz_base)
    
    # O cabeçalho é a primeira linha da matriz base
    cabecalho_meses = matriz_preenchida[0]

    # 2. Criamos um mapa de busca rápido (Dicionário Indexado)
    # Formato: mapa_busca[UC][Mes] = Valor
    mapa_busca = {}
    for fatura in lista_faturas_tagueadas:
        uc = str(fatura.get("Unidade Consumidora", "")).strip()
        mes = str(fatura.get("Mês de referência", "")).strip()
        valor = fatura.get(tag_valor, 0.0) # Pega o valor da tag escolhida
        
        if uc and mes:
            if uc not in mapa_busca:
                mapa_busca[uc] = {}
            mapa_busca[uc][mes] = valor

    # 3. Varremos a Matriz Base linha por linha (pulando o cabeçalho)
    for i in range(1, len(matriz_preenchida)):
        linha = matriz_preenchida[i]
        uc_linha = str(linha[0]).strip() # A UC está sempre na primeira coluna (índice 0)
        
        # Passamos por cada coluna de mês daquela linha
        for j in range(1, len(linha)):
            mes_coluna = str(cabecalho_meses[j]).strip() # Descobre qual é o mês daquela coluna
            
            # Se tivermos um valor correspondente a essa UC e a esse Mês, injetamos na célula
            if uc_linha in mapa_busca and mes_coluna in mapa_busca[uc_linha]:
                linha[j] = mapa_busca[uc_linha][mes_coluna]
            else:
                linha[j] = 0.0 # Se não houver dados, preenche com zero (ou None, se preferir)

    return matriz_preenchida

def exportar_matrizes_para_xlsx(dicionario_abas, pasta_destino, nome_arquivo="Relatorio_Consolidado.xlsx"):
    """
    Recebe um dicionário no formato: {"Nome_da_Aba": matriz_lista_de_listas}
    Gera um único arquivo .xlsx usando openpyxl com formatação profissional.
    """
    # 1. Garante que a pasta de destino exista usando Pathlib
    diretorio = Path(pasta_destino)
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho_final = diretorio / nome_arquivo

    # 2. Inicializa o Workbook do openpyxl
    wb = Workbook()
    
    # O openpyxl cria uma aba padrão chamada 'Sheet'. Vamos usá-la para a primeira matriz
    primeira_aba = True

    # 3. Varre o dicionário criando as abas e despejando as matrizes
    for nome_aba, matriz in dicionario_abas.items():
        if primeira_aba:
            ws = wb.active
            ws.title = nome_aba
            primeira_aba = False
        else:
            ws = wb.create_sheet(title=nome_aba)

        # Despeja a matriz linha por linha na aba atual
        for linha in matriz:
            # Substitui None por célula vazia no Excel, mantendo números e textos normais
            linha_tratada = [item if item is not None else "" for item in linha]
            ws.append(linha_tratada)

    # 4. ESTILIZAÇÃO (Aplica em todas as abas criadas)
    fonte_v = Font(name='Verdana', size=8)
    align_c = Alignment(horizontal='center', vertical='center')

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                cell.font = fonte_v
                cell.alignment = align_c
                
                # Formatação numérica: se for um número e não for a primeira linha (cabeçalho)
                if isinstance(cell.value, (int, float)) and cell.row > 1:
                    cell.number_format = '#,##0.00'

        # Ajuste dinâmico da largura das colunas
        for col in sheet.columns:
            # Mede o tamanho do maior texto na coluna para definir a largura ideal
            max_l = max([len(str(c.value)) for c in col if c.value] + [12])
            sheet.column_dimensions[col[0].column_letter].width = max_l + 4

    # 5. Salva o arquivo final
    wb.save(caminho_final)
# ============================================================== #
# ORQUESTRADOR
# ============================================================== #

def texter_orchestrator():
    
    PATH_OUTPUT.mkdir(parents=True, exist_ok=True)
    PATH_ANALISE.mkdir(parents=True, exist_ok=True)
    
    limpar_estado_processamento()

    # 1. Selecao de pasta de origem
    selected_subfolder = selecionar_subapasta(PATH_INPUT)

    src_dir         = PATH_INPUT / selected_subfolder   # Endereço pasta Poppler do municipio

    # Cria e limpa pasta Texter do município
    dst_dir_name    = selected_subfolder.replace("Poppler", "Texter")
    dst_dir         = PATH_OUTPUT / dst_dir_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    limpar_pasta(dst_dir)

    # 2. Selecao de formato
    print("\n--- QUAL FORMATACAO APLICAR? ---")
    print("\n 1. NEOENERGIA")
    print("\n 2. ENEL")
    print("\n 3. ENERGISA" )
    formatacao = int(input("Escolha o modelo (índice): "))

    
    
    files = sorted([f.name for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".txt"])

    matriz = []

    # 4. Processamento de arquivos Texter
    for file_name in files:
        input_path = src_dir / file_name

        if formatacao == 1:
            ind_data = format_neoenergia(input_path, file_name) 
        matriz.append(ind_data)

    # MONTAR PLANILHA

    matriz_base = gerar_base_matriz_vazia(matriz)
    exportar_matriz_para_csv(matriz_base, PATH_ANALISE, nome_arquivo=f"visualizacao_base_{dst_dir_name}.csv")

    matriz_consumo_faturado = preencher_matriz_com_tag(matriz_base, matriz, "Consumo Faturado")
    matriz_consumo_medido = preencher_matriz_com_tag(matriz_base, matriz, "Consumo Medido")
   

    exportar_matrizes_para_xlsx(
        {
            "Base_Vazia": matriz_base,
            "Consumo_Faturado": matriz_consumo_faturado,
            "Consumo_Medido": matriz_consumo_medido
        },
        PATH_ANALISE,
        nome_arquivo=f"Relatorio_Consolidado_{dst_dir_name}.xlsx"
    )

    

    print("\nFluxo Texter finalizado.")


if __name__ == "__main__":
    texter_orchestrator()
