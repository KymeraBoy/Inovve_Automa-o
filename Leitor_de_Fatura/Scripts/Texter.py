# ============================================================== #
#     BIBLIOTECAS 
# ============================================================== #

# Bibliotecas para manipulação de arquivos, planilhas e dados
import re
import sys
import pandas as pd
from pathlib import Path

# Bibliotecas para formatação de planilhas
from openpyxl.styles    import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils     import get_column_letter
from collections        import defaultdict

# Bibliotecas de funções específicas do Texter
from texter_utils import salvar_arquivo, carregar_arquivo, aba_info_geral, aba_historico_consumo, historico
from Texter_format_functions.texter_format_enel       import format_enel
from Texter_format_functions.texter_format_energisa   import format_energisa
from Texter_format_functions.texter_format_neoenergia import format_neoenergia

# ============================================================== #
# CONFIGURAÇÕES
# ============================================================== #

if getattr(sys, "frozen", False):
    diretorio = Path(sys.executable).resolve().parent
else:
    diretorio = Path(__file__).resolve().parent.parent  # caminho base do projeto (pasta Scripts)

PATH_INPUT          = diretorio / "Faturas_Poppler"
PATH_OUTPUT         = diretorio / "Faturas_Texter"
CABECALHO_PADRAO    = "RELATORIO DE FATURA - SISTEMA INTEGRALAISER\n" + ("=" * 50) + "\n"

meses = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
            "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
            "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
        }

# ============================================================== #
# FUNÇÕES
# ============================================================== #

def parse_data(data_str):
    mes, ano = data_str.split("/")
    mes = mes.strip().upper()
    ano = re.sub(r"\D", "", ano)

    if len(ano) == 0:
        raise ValueError(f"Ano inválido em: {data_str}")

    return (2000 + int(ano), meses[mes])

def transformar(matriz_consumo):
    datas = set()
    for linha in matriz_consumo:
        for d, _ in linha[1:]:
            datas.add(d)

    datas_ordenadas = sorted(datas, key=parse_data)

    resultado = []
    resultado.append(["DATA"] + datas_ordenadas)

    for linha in matriz_consumo:
        id_ = linha[0]
        mapa = {d: v for d, v in linha[1:]}

        nova_linha = [id_]
        for d in datas_ordenadas:
            nova_linha.append(mapa.get(d, "UNK"))

        resultado.append(nova_linha)

    return resultado

# ============================================================== #
# MAPEAMENTO DAS FUNÇÕES DE FORMATAÇÃO
# ============================================================== #

FORMATADORES = {
    # "ENEL": format_enel,
    "ENERGISA": format_energisa,
    "NEOENERGIA":format_neoenergia,        
}

# ORQUESTRADOR
def texter_orchestrator():
    PATH_OUTPUT.mkdir(parents=True, exist_ok=True)  # garante que a pasta de saída exista

    # ========== 1. SELEÇÃO DE PASTA ========== #
    """ Lista as subpastas dentro de PATH_INPUT e permite que o usuário escolha uma delas. A pasta escolhida é então usada como diretório de origem para os arquivos a serem processados. O nome da pasta de destino é gerado automaticamente substituindo "Poppler" por "Texter". """

    subfolders = [f.name for f in PATH_INPUT.iterdir() if f.is_dir()]
    print("\n--- SELEÇÃO DE PASTA (ORIGEM: POPPLER) ---")
    for i, folder in enumerate(subfolders):
        print(f"{i} - {folder}")
    
    f_choice = int(input("Índice da pasta: "))
    selected_subfolder = subfolders[f_choice]
    
    src_dir = PATH_INPUT / selected_subfolder
    # Regra: Trocar "Poppler" por "Texter" no nome da pasta
    dst_dir_name = selected_subfolder.replace("Poppler", "Texter")
    dst_dir = PATH_OUTPUT / dst_dir_name
    
    dst_dir.mkdir(parents=True, exist_ok=True)

    # ========== 2. SELEÇÃO DE FORMATO ========== #
    """ Apresenta ao usuário uma lista de formatos disponíveis (baseados nas chaves do dicionário FORMATADORES) e permite que ele escolha um. A função de formatação correspondente à escolha do usuário é então armazenada para uso posterior no processamento dos arquivos. """

    print("\n--- QUAL FORMATAÇÃO APLICAR? ---")
    formatos = list(FORMATADORES.keys())
    for i, nome in enumerate(formatos):
        print(f"{i} - {nome}")
    fmt_choice = int(input("Índice do formato: "))
    print(fmt_choice)
    funcao_formatadora = FORMATADORES[formatos[fmt_choice]]

    # ========== 3. ESCOPO DE EXECUÇÃO ========== #
    """ Permite ao usuário escolher entre processar todos os documentos da subpasta ou apenas um documento específico. """

    print("\n--- MODO DE EXECUÇÃO ---")
    print("1 - Todos os documentos da subpasta")
    print("2 - Apenas um documento específico")
    mode = input("Escolha a opção: ")

    files = [f.name for f in src_dir.iterdir() if f.suffix.lower() == '.txt']

    if mode == "2":
        for i, f in enumerate(files):
            print(f"{i} - {f}")
        file_choice = int(input("Índice do arquivo: "))
        files = [files[file_choice]]

    # ========== 4. PROCESSAMENTO ========== #
    """ Processa os arquivos selecionados aplicando a função de formatação escolhida e salvando os resultados na pasta de destino. """

    for file_name in files:
        input_path = src_dir / file_name
        # Regra: Trocar nome do arquivo
        output_name = file_name.replace("Poppler", "Texter")
        output_path = dst_dir / output_name
        
        print(f"Formatando: {file_name}...")
        
        conteudo_bruto = carregar_arquivo(input_path)
        conteudo_formatado = funcao_formatadora(conteudo_bruto, file_name)
        
        salvar_arquivo(output_path, conteudo_formatado) 

    # ========== 5. ANÁLISES ========== #
    """ Realiza análises nos dados processados, incluindo a criação de matrizes de identificação e consumo. """

    # Análise específica para o formato ENERGISA
    if funcao_formatadora is format_energisa:

        # 5.1 ABA DE INFORMAÇÃO GERAL
        colunas_base_info_geral = ["UNIDADE", "FORNECIMENTO", "NÍVEL DE TENSÃO", "CÓDIGO", "CLASSIFICAÇÃO", "DESTINO", "ENDEREÇO","MEDIDOR"]
        max_colunas_info_geral = max((len(linha) for linha in aba_info_geral), default=0)

        cabecalho_info_geral = []
        for i in range(max_colunas_info_geral):
            if i < len(colunas_base_info_geral):
                cabecalho_info_geral.append(colunas_base_info_geral[i])
            elif i == max_colunas_info_geral - 1:
                cabecalho_info_geral.append("COMPLEMENTO")
            else:
                cabecalho_info_geral.append(f"CAMPO_{i+1}")

        info_geral = [cabecalho_info_geral] + aba_info_geral if max_colunas_info_geral > 0 else []

        # 5.2 ABA DE HISTÓRICO DE CONSUMO
        grupos_historico_consumo = defaultdict(list)
        for linha in aba_historico_consumo:
            chave = linha[0]
            grupos_historico_consumo[chave].extend(linha[1:])

        historico_consumo_agrupado = []
        for chave, valores in grupos_historico_consumo.items():
            historico_consumo_agrupado.append([chave] + valores)

        historico_consumo_tratado = transformar(historico_consumo_agrupado)

        # 5.3 FORMAÇÃO DA PLANILHA (cada matriz em uma aba)
        df_info_geral = pd.DataFrame(info_geral)
        df_historico_consumo = pd.DataFrame(historico_consumo_tratado)

        nome_planilha = dst_dir.name.replace("Texter", "Analaiser") + ".xlsx"
        arquivo = dst_dir / nome_planilha

        with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
            df_info_geral.to_excel(writer, sheet_name="INFORMAÇÃO GERAL", index=False, header=False)
            df_historico_consumo.to_excel(writer, sheet_name="HISTÓRICO DE CONSUMO", index=False, header=False)

        # 5.4 FORMATAÇÃO VISUAL DA PLANILHA
        from openpyxl import load_workbook
        wb = load_workbook(arquivo)

        # Estilos base
        fonte_padrao   = Font(name="Verdana", size=8)
        fonte_cabecalho= Font(name="Verdana", size=8, bold=True)
        alinhamento    = Alignment(horizontal="center", vertical="center")
        borda_fina     = Side(style="thin")
        borda          = Border(left=borda_fina, right=borda_fina, top=borda_fina, bottom=borda_fina)
        fill_claro     = PatternFill(fill_type="solid", fgColor="FFFFFF")
        fill_escuro    = PatternFill(fill_type="solid", fgColor="DCE6F1")  # azul claro alternado

        def formatar_aba(ws, cabecalho=True, alternado=False):
            # Ajuste de largura por coluna
            for col in ws.columns:
                col_letter = get_column_letter(col[0].column)
                largura_max = 0
                for cell in col:
                    if cell.value is not None:
                        largura_max = max(largura_max, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max(largura_max + 2, 8)

            # Formatação célula a célula
            for row_idx, row in enumerate(ws.iter_rows(), start=1):
                eh_cabecalho = (row_idx == 1 and cabecalho)
                for cell in row:
                    cell.font      = fonte_cabecalho if eh_cabecalho else fonte_padrao
                    cell.alignment = alinhamento
                    cell.border    = borda
                    if alternado and not eh_cabecalho:
                        cell.fill = fill_escuro if row_idx % 2 == 0 else fill_claro
                    elif eh_cabecalho:
                        cell.fill = fill_claro

        formatar_aba(wb["INFORMAÇÃO GERAL"], cabecalho=True, alternado=True)
        formatar_aba(wb["HISTÓRICO DE CONSUMO"], cabecalho=True, alternado=True)

        wb.save(arquivo)

    # Análise específica para o formato NEOENERGIA
    if funcao_formatadora is format_neoenergia:
        # ANALISADOR NEOENERGIA (CELPE)
        agrupados = defaultdict(list)
        for v in historico:
            chave = v[0]
            agrupados[chave].extend(v[1:])  # junta os valores
            resultado = [[k] + valores for k, valores in agrupados.items()]    
        historico[:] = [[v[0]] + list(set(v[1:])) for v in resultado]
        meses = [tupla[0] for subvetor in historico for tupla in subvetor if isinstance(tupla, tuple)]
        meses = list(set(meses))
        ordem_meses = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
            "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
            "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
        }
        meses = sorted(
            meses,
            key=lambda x: (int(x[3:]), ordem_meses[x[:3]])
        )
        meses_index = {mes: i for i, mes in enumerate(meses)}
        resultado = []
        resultado.append(meses)
        resultado[0].insert(0,"UCs")
        for subvetor in historico:
            chave = subvetor[0]
            # inicializa com zeros (um para cada mês)
            valores = ["UNK"] * len(meses)
            # percorre as tuplas do subvetor
            for item in subvetor[1:]:
                if isinstance(item, tuple):
                    mes, valor = item
                    if mes in meses_index:
                        idx = meses_index[mes]
                        valores[idx] = valor
            resultado.append([chave] + valores)
            historico[:] = resultado

        # CONSUMO
        for v in aba_historico_consumo:
            chave = v[0]
            agrupados[chave].extend(v[1:])  # junta os valores
            resultado = [[k] + valores for k, valores in agrupados.items()]    
        aba_historico_consumo[:] = [[v[0]] + list(set(v[1:])) for v in resultado]
        meses = [tupla[0] for subvetor in aba_historico_consumo for tupla in subvetor if isinstance(tupla, tuple)]
        meses = list(set(meses))
        ordem_meses = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
            "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
            "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
        }
        meses = sorted(
            meses,
            key=lambda x: (int(x[3:]), ordem_meses[x[:3]])
        )
        meses_index = {mes: i for i, mes in enumerate(meses)}
        resultado = []
        resultado.append(meses)
        resultado[0].insert(0,"UCs")
        for subvetor in aba_historico_consumo:
            chave = subvetor[0]
            # inicializa com zeros (um para cada mês)
            valores = ["UNK"] * len(meses)
            # percorre as tuplas do subvetor
            for item in subvetor[1:]:
                if isinstance(item, tuple):
                    mes, valor = item
                    if mes in meses_index:
                        idx = meses_index[mes]
                        valores[idx] = valor
            resultado.append([chave] + valores)
            aba_historico_consumo[:] = resultado

        df = pd.DataFrame(aba_info_geral)    
        df.to_excel(dst_dir / "enquadramentos.xlsx", index=False, header=False)
        df = pd.DataFrame(historico)
        df.to_excel(dst_dir / "historico.xlsx", index=False, header=False)
        df = pd.DataFrame(aba_historico_consumo)
        df.to_excel(dst_dir / "consumo.xlsx", index=False, header=False)

if __name__ == "__main__":
    texter_orchestrator()