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
PATH_ANALISE        = diretorio / "Faturas_Analaiser"
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
    try:
        mes, ano = data_str.split("/")
        mes = mes.strip().upper()
        ano = re.sub(r"\D", "", ano)

        if len(ano) == 0 or mes not in meses:
            return (9999, 99)

        return (2000 + int(ano), meses[mes])
    except Exception:
        return (9999, 99)


def normalizar_valor_consumo(valor):
    if valor is None:
        return "UNK"

    texto = str(valor).strip()
    if not texto:
        return "UNK"

    if re.match(r"^\d{2}/\d{2}/\d{4}$", texto):
        return "UNK"

    return texto

def transformar(matriz_consumo):
    datas = set()
    for linha in matriz_consumo:
        for item in linha[1:]:
            if isinstance(item, tuple) and len(item) >= 1:
                d = item[0]
                if isinstance(d, str) and re.match(r"^[A-Z]{3}/\d{2,4}$", d.strip().upper()):
                    datas.add(d)

    datas_ordenadas = sorted(datas, key=parse_data)

    resultado = []
    resultado.append(["DATA"] + datas_ordenadas)

    for linha in matriz_consumo:
        id_ = linha[0]
        mapa = {}
        for item in linha[1:]:
            if isinstance(item, tuple) and len(item) >= 2:
                d, v = item[0], item[1]
                if isinstance(d, str) and re.match(r"^[A-Z]{3}/\d{2,4}$", d.strip().upper()):
                    mapa[d] = normalizar_valor_consumo(v)

        nova_linha = [id_]
        for d in datas_ordenadas:
            nova_linha.append(mapa.get(d, "UNK"))

        resultado.append(nova_linha)

    return resultado


def sanitizar_nome_arquivo(texto):
    return re.sub(r"[^0-9A-Za-z._-]+", "_", str(texto)).strip("._-") or "arquivo"


def montar_matriz_info_geral(registros_info):
    cabecalho = [
        "UNIDADE CONSUMIDORA",
        "CLASSIFICAÇÃO",
        "TIPO DE FORNECIMENTO",
        "CLIENTE",
        "ENDEREÇO DE ENTREGA",
        "NÚMERO DO MEDIDOR",
    ]

    if not registros_info:
        return [cabecalho, ["SEM DADOS", "", "", "", "", ""]]

    return [cabecalho] + registros_info


def montar_matriz_consumo_geral(registros_por_uc):
    meses_coletados = set()
    valores_por_uc = {}

    for uc, registros in registros_por_uc.items():
        mapa_consumo = {}

        for registro in registros:
            historico_consumo = registro.get("historico_consumo") or []
            for item in historico_consumo[1:]:
                if not (isinstance(item, tuple) and len(item) >= 2):
                    continue

                mes = item[0]
                valor = item[1]

                if isinstance(mes, str) and re.match(r"^[A-Z]{3}/\d{2,4}$", mes.strip().upper()):
                    meses_coletados.add(mes)
                    mapa_consumo[mes] = normalizar_valor_consumo(valor)

        valores_por_uc[uc] = mapa_consumo

    meses_ordenados = sorted(meses_coletados, key=parse_data)
    cabecalho = ["UNIDADE CONSUMIDORA"] + meses_ordenados

    if not meses_ordenados:
        return [cabecalho]

    matriz = [cabecalho]
    for uc in sorted(valores_por_uc.keys()):
        mapa_consumo = valores_por_uc[uc]
        linha = [uc]
        for mes in meses_ordenados:
            linha.append(mapa_consumo.get(mes, "UNK"))
        matriz.append(linha)

    return matriz


def montar_matriz_medidor_geral(registros_por_uc):
    referencias_coletadas = set()
    valores_por_uc = {}

    for uc, registros in registros_por_uc.items():
        mapa_medidor = {}

        for registro in registros:
            referencia = registro.get("referencia") or "SEM_REFERENCIA"
            numero_medidor = registro.get("numero_medidor") or "UNK"

            if referencia != "SEM_REFERENCIA":
                referencias_coletadas.add(referencia)
                mapa_medidor[referencia] = numero_medidor

        valores_por_uc[uc] = mapa_medidor

    referencias_ordenadas = sorted(referencias_coletadas, key=parse_data)
    cabecalho = ["UNIDADE CONSUMIDORA"] + referencias_ordenadas

    if not referencias_ordenadas:
        return [cabecalho]

    matriz = [cabecalho]
    for uc in sorted(valores_por_uc.keys()):
        mapa_medidor = valores_por_uc[uc]
        linha = [uc]
        for referencia in referencias_ordenadas:
            linha.append(mapa_medidor.get(referencia, "UNK"))
        matriz.append(linha)

    return matriz


def formatar_aba_planilha(ws, fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        largura_max = 0
        for cell in col:
            if cell.value is not None:
                largura_max = max(largura_max, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(largura_max + 2, 8)

    for row_idx, row in enumerate(ws.iter_rows(), start=1):
        eh_cabecalho = row_idx == 1
        for cell in row:
            cell.font = fonte_cabecalho if eh_cabecalho else fonte_padrao
            cell.alignment = alinhamento
            cell.border = borda
            if eh_cabecalho:
                cell.fill = fill_claro
            else:
                cell.fill = fill_escuro if row_idx % 2 == 0 else fill_claro


def gerar_planilhas_energisa_por_uc(src_dir, dst_dir, funcao_formatadora):
    registros_por_uc = defaultdict(list)
    erros = []

    files = sorted([f.name for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".txt"])
    for file_name in files:
        input_path = src_dir / file_name
        print(f"Processando: {file_name}...")

        try:
            conteudo_bruto = carregar_arquivo(input_path)
            registro = funcao_formatadora(conteudo_bruto, file_name)
        except Exception as exc:
            erros.append((file_name, str(exc)))
            continue

        if not isinstance(registro, dict):
            erros.append((file_name, "formatador nao retornou registro estruturado"))
            continue

        uc = registro.get("uc") or "SEM_UC"
        registros_por_uc[uc].append(registro)

    dst_dir.mkdir(parents=True, exist_ok=True)

    fonte_padrao = Font(name="Verdana", size=8)
    fonte_cabecalho = Font(name="Verdana", size=8, bold=True)
    alinhamento = Alignment(horizontal="center", vertical="center")
    borda_fina = Side(style="thin")
    borda = Border(left=borda_fina, right=borda_fina, top=borda_fina, bottom=borda_fina)
    fill_claro = PatternFill(fill_type="solid", fgColor="FFFFFF")
    fill_escuro = PatternFill(fill_type="solid", fgColor="DCE6F1")

    resumo_ucs = []

    for uc, registros in sorted(registros_por_uc.items(), key=lambda item: item[0]):
        nome_uc = sanitizar_nome_arquivo(uc)
        pasta_uc = dst_dir / nome_uc
        pasta_uc.mkdir(parents=True, exist_ok=True)

        info_rows = []
        historico_rows = []
        primeiro_registro = registros[0]

        for registro in registros:
            info_rows.append([
                registro.get("uc") or uc,
                registro.get("classificacao") or "",
                registro.get("tipo_fornecimento") or "",
                registro.get("cliente") or "",
                registro.get("endereco_entrega") or "",
                registro.get("numero_medidor") or "",
            ])

            historico_consumo = registro.get("historico_consumo") or []
            if historico_consumo:
                historico_rows.append(historico_consumo)

        matriz_info = montar_matriz_info_geral(info_rows)
        matriz_historico = transformar(historico_rows) if historico_rows else [["SEM DADOS"]]
        matriz_medidor = montar_matriz_medidor_geral({uc: registros})

        arquivo_saida = pasta_uc / f"{nome_uc}.xlsx"

        df_info = pd.DataFrame(matriz_info)
        df_hist = pd.DataFrame(matriz_historico)
        df_medidor = pd.DataFrame(matriz_medidor)

        with pd.ExcelWriter(arquivo_saida, engine="openpyxl") as writer:
            df_info.to_excel(writer, sheet_name="AGRUPADA", index=False, header=False)
            df_hist.to_excel(writer, sheet_name="HISTORICO DE CONSUMO", index=False, header=False)
            df_medidor.to_excel(writer, sheet_name="MEDIDOR", index=False, header=False)

        from openpyxl import load_workbook

        wb = load_workbook(arquivo_saida)
        formatar_aba_planilha(wb["AGRUPADA"], fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro)
        formatar_aba_planilha(wb["HISTORICO DE CONSUMO"], fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro)
        formatar_aba_planilha(wb["MEDIDOR"], fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro)
        wb.save(arquivo_saida)

        resumo_ucs.append([
            primeiro_registro.get("uc") or uc,
            primeiro_registro.get("classificacao") or "",
            primeiro_registro.get("tipo_fornecimento") or "",
            primeiro_registro.get("cliente") or "",
            primeiro_registro.get("endereco_entrega") or "",
            primeiro_registro.get("numero_medidor") or "",
        ])
        print(f"[OK] Planilha da UC gerada: {arquivo_saida}")

    resumo_matriz = (
        [[
            "UNIDADE CONSUMIDORA",
            "CLASSIFICAÇÃO",
            "TIPO DE FORNECIMENTO",
            "CLIENTE",
            "ENDEREÇO DE ENTREGA",
            "NÚMERO DO MEDIDOR",
        ]] + resumo_ucs
        if resumo_ucs
        else [["SEM DADOS"]]
    )
    arquivo_resumo = dst_dir / "Agrupada.xlsx"
    df_resumo = pd.DataFrame(resumo_matriz)
    matriz_consumo = montar_matriz_consumo_geral(registros_por_uc)
    matriz_medidor = montar_matriz_medidor_geral(registros_por_uc)
    df_consumo = pd.DataFrame(matriz_consumo)
    df_medidor = pd.DataFrame(matriz_medidor)

    with pd.ExcelWriter(arquivo_resumo, engine="openpyxl") as writer:
        df_resumo.to_excel(writer, sheet_name="AGRUPADA", index=False, header=False)
        df_consumo.to_excel(writer, sheet_name="CONSUMO", index=False, header=False)
        df_medidor.to_excel(writer, sheet_name="MEDIDOR", index=False, header=False)

    from openpyxl import load_workbook

    wb = load_workbook(arquivo_resumo)
    formatar_aba_planilha(wb["AGRUPADA"], fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro)
    formatar_aba_planilha(wb["CONSUMO"], fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro)
    formatar_aba_planilha(wb["MEDIDOR"], fonte_padrao, fonte_cabecalho, alinhamento, borda, fill_claro, fill_escuro)
    wb.save(arquivo_resumo)

    print(f"[OK] Resumo geral gerado: {arquivo_resumo}")

    if erros:
        log_erros = dst_dir / "erros_processamento.txt"
        with open(log_erros, "w", encoding="utf-8") as f:
            for nome_arquivo, erro in erros:
                f.write(f"{nome_arquivo}\t{erro}\n")
        print(f"[AVISO] {len(erros)} arquivo(s) falharam. Log: {log_erros}")

    return resumo_ucs

# ============================================================== #
# MAPEAMENTO DAS FUNÇÕES DE FORMATAÇÃO
# ============================================================== #

FORMATADORES = {
    # "ENEL": format_enel,
    "ENERGISA": format_energisa,
    "NEOENERGIA":format_neoenergia,        
}

def limpar_estado_processamento():
    # Evita acumular dados de execucoes anteriores na mesma sessao.
    aba_info_geral.clear()
    aba_historico_consumo.clear()
    historico.clear()

# ORQUESTRADOR
def texter_orchestrator():
    PATH_OUTPUT.mkdir(parents=True, exist_ok=True)  # garante que a pasta de saída exista
    limpar_estado_processamento()

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

    if funcao_formatadora is format_energisa:
        PATH_ANALISE.mkdir(parents=True, exist_ok=True)
        dst_dir_name = selected_subfolder.replace("Poppler", "Analaiser")
        dst_dir = PATH_ANALISE / dst_dir_name
        gerar_planilhas_energisa_por_uc(src_dir, dst_dir, funcao_formatadora)
        return

    # ========== 2.1 MODO DE SAÍDA ========== #
    """ Permite escolher se os arquivos Texter (txt) serão gerados ou se apenas a planilha será criada diretamente dos textos Poppler. """

    print("\n--- SAÍDA DE ARQUIVOS ---")
    print("1 - Gerar arquivos Texter (.txt) e planilha")
    print("2 - Gerar somente planilha (direto dos textos Poppler)")
    output_mode = input("Escolha a opção: ").strip()
    gerar_arquivos_texter = output_mode != "2"

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
        print(f"Processando: {file_name}...")
        
        conteudo_bruto = carregar_arquivo(input_path)
        conteudo_formatado = funcao_formatadora(conteudo_bruto, file_name)

        if gerar_arquivos_texter:
            # Regra: Trocar nome do arquivo
            output_name = file_name.replace("Poppler", "Texter")
            output_path = dst_dir / output_name
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