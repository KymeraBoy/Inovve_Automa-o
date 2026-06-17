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
# CONFIGURACOES (Serão sobrescritas dinamicamente pela GUI)
# ============================================================== #

PATH_INPUT   = Path(".")
PATH_OUTPUT  = Path(".")
PATH_ANALISE = Path(".")

# ============================================================== #
# FUNCOES
# ============================================================== #

def limpar_estado_processamento():
    aba_info_geral.clear()
    aba_historico_consumo.clear()
    historico.clear()

def limpar_pasta(caminho_pasta: Path) -> None:
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

def selecionar_subapasta(PATH: Path, municipio_name: str) -> Path:
    subfolders = [f.name for f in PATH.iterdir() if f.is_dir()]
    for folder_name in subfolders:
        if folder_name == municipio_name:
            return PATH / folder_name
    raise ValueError(f"Município '{municipio_name}' não encontrado em '{PATH}'.")

MESES_MAP = {
    'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
    'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12
}

def chave_ordenacao_mes(mes_ano):
    try:
        if '/' in str(mes_ano):
            partes = str(mes_ano).split('/')
            if partes[0].isdigit():
                return (int(partes[1]), int(partes[0]))
            else:
                return (int(partes[1]), MESES_MAP.get(partes[0].upper(), 0))
    except:
        pass
    return (9999, 0)


def gerar_base_matriz_vazia(lista_faturas_tagueadas):
    ucs_unicas = set()
    meses_unicos = set()

    for fatura in lista_faturas_tagueadas:
        uc = fatura.get("Unidade Consumidora")
        mes = fatura.get("Mês de referência")
        if uc:
            ucs_unicas.add(str(uc).strip())
        if mes:
            meses_unicos.add(str(mes).strip())

    lista_ucs_ordenada = sorted(list(ucs_unicas))
    lista_meses_ordenada = sorted(list(meses_unicos), key=chave_ordenacao_mes)

    matriz_base = []
    cabecalho = ["Unidade Consumidora"] + lista_meses_ordenada
    matriz_base.append(cabecalho)

    for uc in lista_ucs_ordenada:
        linha_vazia = [uc] + [None] * len(lista_meses_ordenada)
        matriz_base.append(linha_vazia)

    return matriz_base

def preencher_matriz_com_tag(matriz_base, lista_faturas_tagueadas, tag_valor):
    import copy
    matriz_preenchida = copy.deepcopy(matriz_base)
    cabecalho_meses = matriz_preenchida[0]

    mapa_busca = {}
    for fatura in lista_faturas_tagueadas:
        uc = str(fatura.get("Unidade Consumidora", "")).strip()
        mes = str(fatura.get("Mês de referência", "")).strip()
        valor = fatura.get(tag_valor, 0.0)
        if uc and mes:
            if uc not in mapa_busca:
                mapa_busca[uc] = {}
            mapa_busca[uc][mes] = valor

    for i in range(1, len(matriz_preenchida)):
        linha = matriz_preenchida[i]
        uc_linha = str(linha[0]).strip()
        for j in range(1, len(linha)):
            mes_coluna = str(cabecalho_meses[j]).strip()
            if uc_linha in mapa_busca and mes_coluna in mapa_busca[uc_linha]:
                linha[j] = mapa_busca[uc_linha][mes_coluna]
            else:
                linha[j] = 0.0

    return matriz_preenchida

def exportar_matrizes_para_xlsx(dicionario_abas, pasta_destino, nome_arquivo="Relatorio_Consolidado.xlsx"):
    diretorio = Path(pasta_destino)
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho_final = diretorio / nome_arquivo

    wb = Workbook()
    primeira_aba = True

    for nome_aba, matriz in dicionario_abas.items():
        if primeira_aba:
            ws = wb.active
            ws.title = nome_aba
            primeira_aba = False
        else:
            ws = wb.create_sheet(title=nome_aba)

        for linha in matriz:
            linha_tratada = [item if item is not None else "" for item in linha]
            ws.append(linha_tratada)

    fonte_v = Font(name='Verdana', size=8)
    align_c = Alignment(horizontal='center', vertical='center')

    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                cell.font = fonte_v
                cell.alignment = align_c
                if isinstance(cell.value, (int, float)) and cell.row > 1:
                    cell.number_format = '#,##0.00'

        for col in sheet.columns:
            max_l = max([len(str(c.value)) for c in col if c.value] + [12])
            sheet.column_dimensions[col[0].column_letter].width = max_l + 4

    wb.save(caminho_final)


# ============================================================== #
# ORQUESTRADOR
# ============================================================== #

def texter_orchestrator(municipio_name: str, concessionaria_name: str, progress_callback=None):
    
    municipio_name = municipio_name + "_Poppler"
    
    PATH_OUTPUT.mkdir(parents=True, exist_ok=True)
    PATH_ANALISE.mkdir(parents=True, exist_ok=True)
    
    limpar_estado_processamento()

    src_dir_path = selecionar_subapasta(PATH_INPUT, municipio_name)
    selected_subfolder = src_dir_path.name
    src_dir = src_dir_path 

    concessionaria_map = {"NEOENERGIA": 1, "ENEL": 2, "ENERGISA": 3}

    dst_dir_name    = selected_subfolder.replace("Poppler", "Texter")
    dst_dir         = PATH_OUTPUT / dst_dir_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    limpar_pasta(dst_dir)

    formatacao = concessionaria_map.get(concessionaria_name.upper())
    if formatacao is None:
        raise ValueError(f"Concessionária '{concessionaria_name}' não reconhecida para o Texter.")
     
    files = sorted([f.name for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".txt"])

    matriz = []
    total_files = len(files)

    for idx, file_name in enumerate(files):
        if progress_callback:
            progress_callback(idx + 1, total_files, f"Texter: Processando {file_name} ({idx + 1}/{total_files})...")

        input_path = src_dir / file_name
        if formatacao == 1:
            ind_data = format_neoenergia(input_path, file_name)

        matriz.append(ind_data)

    matriz_base = gerar_base_matriz_vazia(matriz)

    matriz_consumo_faturado = preencher_matriz_com_tag(matriz_base, matriz, "Consumo Faturado")
    matriz_consumo_medido = preencher_matriz_com_tag(matriz_base, matriz, "Consumo Medido")
    matriz_classificacao = preencher_matriz_com_tag(matriz_base, matriz, "Classificação")
   
    exportar_matrizes_para_xlsx(
        {        
            "Classificação": matriz_classificacao,    
            "Consumo_Faturado": matriz_consumo_faturado,
            "Consumo_Medido": matriz_consumo_medido,
        },
        PATH_ANALISE,
        nome_arquivo=f"Relatorio_Consolidado_{dst_dir_name}.xlsx"
    )

    print("\nFluxo Texter finalizado.")

if __name__ == "__main__":
    print("Este script não deve ser executado diretamente. Use a GUI.")