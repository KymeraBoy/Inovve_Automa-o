# ============================================================== #
#     BIBLIOTECAS
# ============================================================== #

import sys
import re
import unicodedata
from pathlib import Path
from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

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
# MAPEAMENTO DAS FUNCOES DE FORMATACAO
# ============================================================== #

FORMATADORES = {
    # "ENEL": format_enel,
    "ENERGISA": format_energisa,
    "NEOENERGIA": format_neoenergia,
}

THIN_SIDE = Side(style="thin", color="D9E2F3")
BORDER_LIGHT = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)
FONT_HEADER = Font(name="Calibri", bold=True, color="FFFFFF")
FONT_BODY = Font(name="Calibri", color="1F1F1F")
FONT_BODY_BOLD = Font(name="Calibri", bold=True, color="1F1F1F")
ALIGN_LEFT = Alignment(horizontal="left", vertical="center")
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
FILL_HEADER = PatternFill("solid", fgColor="1F4E78")
FILL_SUBHEADER = PatternFill("solid", fgColor="5B9BD5")
FILL_ZEBRA = PatternFill("solid", fgColor="F7FBFF")
FILL_WHITE = PatternFill("solid", fgColor="FFFFFF")
FILL_CHANGE = PatternFill("solid", fgColor="FFF2CC")


# ============================================================== #
# FUNCOES
# ============================================================== #

def limpar_estado_processamento():
    # Evita acumular dados de execucoes anteriores na mesma sessao.
    aba_info_geral.clear()
    aba_historico_consumo.clear()
    historico.clear()


def limpar_arquivos_texter(dst_dir):
    arquivos_removidos = 0
    for item in dst_dir.iterdir():
        if item.is_file():
            item.unlink()
            arquivos_removidos += 1
    if arquivos_removidos:
        print(f"[OK] {arquivos_removidos} arquivo(s) antigos removidos de: {dst_dir}")


def _montar_nome_saida_texter(nome_entrada):
    nome_saida = nome_entrada.replace("Poppler", "Texter")
    if nome_saida == nome_entrada:
        return nome_entrada.replace(".txt", "_Texter.txt")
    return nome_saida


def _converter_para_texto_saida(conteudo_formatado):
    if isinstance(conteudo_formatado, dict):
        return conteudo_formatado.get("texto", "")
    return str(conteudo_formatado)


def _extrair_indicador_tribf_irrf(conteudo_poppler):
    texto = (conteudo_poppler or "").upper()
    return "PRESENTE" if ("TRIBF-IRRF" in texto or "TIBF-IRRF" in texto) else "AUSENTE"


def _normalizar_poppler_para_parser(conteudo_poppler):
    if not conteudo_poppler:
        return ""

    padrao_divisoria = re.compile(
        r"^\s*=+\s*FIM_PAGINA_\d+\s*\|\s*INICIO_PAGINA_\d+\s*=+\s*$",
        flags=re.IGNORECASE,
    )

    linhas_filtradas = []
    for linha in conteudo_poppler.splitlines():
        if padrao_divisoria.match(linha):
            continue
        linhas_filtradas.append(linha)

    return "\n".join(linhas_filtradas)


def _extrair_campos_texter(conteudo_texter):
    campos = {}
    for linha in (conteudo_texter or "").splitlines():
        linha = linha.strip()
        if not linha:
            continue

        if "\t" in linha:
            chave, valor = linha.split("\t", 1)
        elif ":" in linha:
            chave, valor = linha.split(":", 1)
        else:
            continue

        campos[_normalizar_chave_campo(chave)] = valor.strip()
    return campos


def _normalizar_chave_campo(chave):
    chave_normalizada = unicodedata.normalize("NFKD", str(chave or ""))
    chave_normalizada = "".join(
        caractere for caractere in chave_normalizada if not unicodedata.combining(caractere)
    )
    return chave_normalizada.strip().upper()


def _obter_campo(campos, *aliases, default="UNK"):
    for alias in aliases:
        valor = campos.get(_normalizar_chave_campo(alias))
        if valor:
            return valor
    return default


def _chave_ordenacao_referencia(referencia):
    ref = (referencia or "").strip().upper()
    meses = {
        "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4, "MAI": 5, "JUN": 6,
        "JUL": 7, "AGO": 8, "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12,
    }

    partes = ref.split("/")
    if len(partes) != 2:
        return (9999, 99, ref)

    mes_raw = partes[0].strip()
    ano_raw = partes[1].strip()

    if mes_raw.isdigit():
        mes = int(mes_raw)
    else:
        mes = meses.get(mes_raw[:3], 99)

    if ano_raw.isdigit():
        ano = int(ano_raw)
        if ano < 100:
            ano += 2000
    else:
        ano = 9999

    return (ano, mes, ref)


def _referencia_valida(referencia):
    ano, mes, _ = _chave_ordenacao_referencia(referencia)
    return ano != 9999 and mes != 99


def _chave_referencia_mais_recente(referencia):
    ano, mes, ref = _chave_ordenacao_referencia(referencia)
    if ano == 9999 or mes == 99:
        return (0, -1, -1, ref)
    return (1, ano, mes, ref)


def _valor_preenchido(valor):
    return str(valor or "").strip().upper() not in {"", "UNK", "SEM DADO", "SEM_ENDERECO", "SEM_CLIENTE", "SEM_FORNECIMENTO"}


def _mesclar_registro_geral(registro_atual, novo_registro):
    if registro_atual is None:
        return dict(novo_registro)

    registro_mesclado = dict(registro_atual)
    for chave, valor in novo_registro.items():
        if chave == "referencia":
            continue
        if not _valor_preenchido(registro_mesclado.get(chave)) and _valor_preenchido(valor):
            registro_mesclado[chave] = valor

    referencia_atual = registro_mesclado.get("referencia", "")
    referencia_nova = novo_registro.get("referencia", "")
    if not _referencia_valida(referencia_atual) and _referencia_valida(referencia_nova):
        registro_mesclado["referencia"] = referencia_nova

    return registro_mesclado


def _normalizar_texto(valor):
    return str(valor or "").strip() or "SEM DADO"


def _valor_placeholder(valor):
    texto = _normalizar_texto(valor)
    return texto if texto else "SEM DADO"


def _extrair_registro_texter(arquivo):
    campos = _extrair_campos_texter(carregar_arquivo(arquivo))
    return {
        "arquivo": arquivo.name,
        "uc": _valor_placeholder(_obter_campo(campos, "UNIDADE CONSUMIDORA", "UC", default="SEM DADO")),
        "referencia": _valor_placeholder(_obter_campo(campos, "MES/ANO REFERENCIA", "REFERÊNCIA", "REFERENCIA", default="SEM DADO")),
        "cliente": _valor_placeholder(_obter_campo(campos, "CLIENTE", default="SEM DADO")),
        "endereco_unidade_consumidora": _valor_placeholder(
            _obter_campo(
                campos,
                "ENDEREÇO DA UNIDADE CONSUMIDORA",
                "ENDERECO DA UNIDADE CONSUMIDORA",
                "ENDERECO DE ENTREGA",
                "ENDEREÇO DE ENTREGA",
                default="SEM DADO",
            )
        ),
        "classificacao": _valor_placeholder(_obter_campo(campos, "CLASSIFICACAO", "CLASSIFICAÇÃO", default="SEM DADO")),
        "subclasse": _valor_placeholder(_obter_campo(campos, "SUBCLASSE", default="SEM DADO")),
        "grupo_tarifario": _valor_placeholder(_obter_campo(campos, "GRUPO TARIFÁRIO", "GRUPO TARIFARIO", default="SEM DADO")),
        "modalidade_tarifaria": _valor_placeholder(_obter_campo(campos, "MODALIDADE TARIFÁRIA", "MODALIDADE TARIFARIA", default="SEM DADO")),
        "tensao_fornecimento": _valor_placeholder(_obter_campo(campos, "TENSÃO DE FORNECIMENTO", "TENSAO DE FORNECIMENTO", default="SEM DADO")),
        "distribuidora": _valor_placeholder(_obter_campo(campos, "DISTRIBUIDORA", default="SEM DADO")),
        "municipio": _valor_placeholder(_obter_campo(campos, "MUNICIPIO", "MUNICÍPIO", default="SEM DADO")),
        "situacao_unidade": _valor_placeholder(_obter_campo(campos, "SITUAÇÃO DA UNIDADE", "SITUACAO DA UNIDADE", default="SEM DADO")),
        "consumo_medio": _valor_placeholder(_obter_campo(campos, "CONSUMO MÉDIO", "CONSUMO MEDIO", default="SEM DADO")),
        "demanda_contratada": _valor_placeholder(_obter_campo(campos, "DEMANDA CONTRATADA", default="SEM DADO")),
        "valor_faturado": _valor_placeholder(_obter_campo(campos, "VALOR FATURADO", default="SEM DADO")),
        "valor_medido": _valor_placeholder(_obter_campo(campos, "VALOR MEDIDO", default="SEM DADO")),
        "valor_fatura": _valor_placeholder(_obter_campo(campos, "VALOR DA FATURA", default="SEM DADO")),
        "indicador_tribf_irrf": _valor_placeholder(_obter_campo(campos, "INDICADOR TRIBF-IRRF", default="AUSENTE")),
    }


def _coletar_registros_texter(dst_dir):
    registros = []

    for arquivo in sorted(dst_dir.iterdir()):
        if arquivo.is_file() and arquivo.suffix.lower() == ".txt":
            registros.append(_extrair_registro_texter(arquivo))

    return registros


def listar_txts_disponiveis(src_dir):
    return sorted(
        [arquivo.name for arquivo in src_dir.iterdir() if arquivo.is_file() and arquivo.suffix.lower() == ".txt"]
    )


def processar_texter(src_dir, nome_formatador, selected_files=None, limpar_saida=True, progress_callback=None, log_callback=None):
    if nome_formatador not in FORMATADORES:
        raise ValueError(f"Formatador inválido: {nome_formatador}")

    funcao_formatadora = FORMATADORES[nome_formatador]

    PATH_OUTPUT.mkdir(parents=True, exist_ok=True)
    PATH_ANALISE.mkdir(parents=True, exist_ok=True)

    dst_dir = PATH_OUTPUT / f"{src_dir.name.replace('Poppler', 'Texter')}"
    dst_dir.mkdir(parents=True, exist_ok=True)

    if limpar_saida:
        limpar_arquivos_texter(dst_dir)

    limpar_estado_processamento()

    arquivos = selected_files or listar_txts_disponiveis(src_dir)
    if not arquivos:
        raise ValueError("Nenhum TXT disponível para processamento.")

    resultados = []
    for idx, file_name in enumerate(arquivos, start=1):
        input_path = src_dir / file_name

        if log_callback:
            log_callback(f"Processando: {file_name}...")

        conteudo_bruto = carregar_arquivo(input_path)
        conteudo_para_parser = _normalizar_poppler_para_parser(conteudo_bruto)
        conteudo_formatado = funcao_formatadora(conteudo_para_parser, file_name)
        conteudo_saida = _converter_para_texto_saida(conteudo_formatado)
        indicador_tribf_irrf = _extrair_indicador_tribf_irrf(conteudo_bruto)

        if conteudo_saida and not conteudo_saida.endswith("\n"):
            conteudo_saida += "\n"
        conteudo_saida += f"INDICADOR TRIBF-IRRF\t{indicador_tribf_irrf}\n"

        output_name = _montar_nome_saida_texter(file_name)
        output_path = dst_dir / output_name
        salvar_arquivo(output_path, conteudo_saida)

        resultados.append(
            {
                "arquivo": file_name,
                "saida": output_path,
                "sucesso": True,
            }
        )

        if progress_callback:
            progress_callback(idx, len(arquivos), file_name)

        if log_callback:
            log_callback(f"[OK] Arquivo Texter criado: {output_path}")

    caminho_planilha = _gerar_planilha_texter(dst_dir)

    return {
        "origem": src_dir,
        "destino": dst_dir,
        "planilha": caminho_planilha,
        "resultados": resultados,
        "processados": len(resultados),
    }


def _coletar_uc_ordenadas(registros):
    return sorted({registro.get("uc", "SEM DADO") for registro in registros if registro.get("uc")})


def _coletar_referencias_ordenadas(registros):
    referencias = {registro.get("referencia", "SEM DADO") for registro in registros if registro.get("referencia")}
    return sorted(referencias, key=_chave_ordenacao_referencia)


def _mesclar_registros_por_uc(registros):
    mapa = {}
    for registro in registros:
        uc = registro.get("uc", "SEM DADO")
        atual = mapa.get(uc)
        if atual is None:
            mapa[uc] = dict(registro)
        else:
            mapa[uc] = _mesclar_registro_geral(atual, registro)
    return mapa


def _montar_mapa_historico(registros, campo_valor):
    mapa = {}
    for registro in registros:
        chave = (registro.get("uc", "SEM DADO"), registro.get("referencia", "SEM DADO"))
        valor = _valor_placeholder(registro.get(campo_valor, "SEM DADO"))
        if chave not in mapa or mapa[chave] == "SEM DADO":
            mapa[chave] = valor
    return mapa


def _ajustar_larguras(ws, geral=False):
    for coluna in range(1, ws.max_column + 1):
        maior_tamanho = 0
        for row in range(1, ws.max_row + 1):
            valor = ws.cell(row=row, column=coluna).value
            if valor is None:
                continue
            texto = str(valor)
            tamanho = max(len(parte) for parte in texto.splitlines()) if texto else 0
            if tamanho > maior_tamanho:
                maior_tamanho = tamanho

        largura_base = 22 if coluna == 1 else 10
        largura = max(largura_base, min(maior_tamanho + 2, 60))
        ws.column_dimensions[get_column_letter(coluna)].width = largura


def _aplicar_moldura(ws):
    for row in ws.iter_rows():
        for cell in row:
            cell.border = BORDER_LIGHT


def _formatar_area_tabela(ws, zebra=True):
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "B2"
    ws.sheet_view.zoomScale = 90

    for cell in ws[1]:
        cell.fill = FILL_HEADER
        cell.font = FONT_HEADER
        cell.alignment = ALIGN_CENTER

    if ws.max_row >= 2:
        for row in range(2, ws.max_row + 1):
            preenchimento = FILL_ZEBRA if zebra and row % 2 == 0 else FILL_WHITE
            for col in range(1, ws.max_column + 1):
                cell = ws.cell(row=row, column=col)
                cell.fill = preenchimento
                cell.font = FONT_BODY_BOLD if col == 1 else FONT_BODY
                cell.alignment = ALIGN_LEFT

    _aplicar_moldura(ws)


def _preencher_aba_geral(ws, registros):
    cabecalhos = [
        "UNIDADE CONSUMIDORA",
        "CLIENTE",
        "CLASSE DE CONSUMO",
        "ENDEREÇO DA UNIDADE CONSUMIDORA",
        "SUBCLASSE",
        "GRUPO TARIFÁRIO",
        "MODALIDADE TARIFÁRIA",
        "TENSÃO DE FORNECIMENTO",
        "DISTRIBUIDORA",
        "MUNICÍPIO",
        "SITUAÇÃO DA UNIDADE",
        "CONSUMO MÉDIO",
        "DEMANDA CONTRATADA",
    ]

    campos_por_coluna = [
        "uc",
        "cliente",
        "classificacao",
        "endereco_unidade_consumidora",
        "subclasse",
        "grupo_tarifario",
        "modalidade_tarifaria",
        "tensao_fornecimento",
        "distribuidora",
        "municipio",
        "situacao_unidade",
        "consumo_medio",
        "demanda_contratada",
    ]

    for col, cabecalho in enumerate(cabecalhos, start=1):
        ws.cell(row=1, column=col, value=cabecalho)

    mapa = _mesclar_registros_por_uc(registros)
    for row, uc in enumerate(_coletar_uc_ordenadas(registros), start=2):
        registro = mapa.get(uc, {})
        for col, campo in enumerate(campos_por_coluna, start=1):
            ws.cell(row=row, column=col, value=_valor_placeholder(registro.get(campo, "SEM DADO")))

    ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
    _ajustar_larguras(ws, geral=True)
    _formatar_area_tabela(ws, zebra=True)
    ws.freeze_panes = "B2"


def _preencher_aba_historico(ws, registros, campo_valor, titulo_coluna):
    ucs = _coletar_uc_ordenadas(registros)
    referencias = _coletar_referencias_ordenadas(registros)
    mapa = _montar_mapa_historico(registros, campo_valor)

    ws.cell(row=1, column=1, value=titulo_coluna)
    for col, referencia in enumerate(referencias, start=2):
        ws.cell(row=1, column=col, value=referencia)

    for row, uc in enumerate(ucs, start=2):
        ws.cell(row=row, column=1, value=uc)
        for col, referencia in enumerate(referencias, start=2):
            ws.cell(row=row, column=col, value=_valor_placeholder(mapa.get((uc, referencia), "SEM DADO")))

    ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{ws.max_row}"
    _ajustar_larguras(ws, geral=False)
    _formatar_area_tabela(ws, zebra=True)

    if ws.max_row > 1 and ws.max_column > 2:
        ultima_coluna = get_column_letter(ws.max_column)
        ws.conditional_formatting.add(
            f"B2:{ultima_coluna}{ws.max_row}",
            FormulaRule(
                formula=["AND(B2<>A2,B2<>\"\",A2<>\"\")"],
                fill=FILL_CHANGE,
            ),
        )


def _gerar_planilha_texter(dst_dir):
    registros = _coletar_registros_texter(dst_dir)

    PATH_ANALISE.mkdir(parents=True, exist_ok=True)
    nome_planilha = f"{dst_dir.name.replace('Texter', 'Analaiser')}.xlsx"
    caminho_planilha = PATH_ANALISE / nome_planilha

    wb = Workbook()
    ws_geral = wb.active
    ws_geral.title = "GERAL"
    _preencher_aba_geral(ws_geral, registros)

    abas_historico = [
        ("HIST_CLASSIFICACAO", "classificacao", "UNIDADE CONSUMIDORA"),
        ("HIST_SUBCLASSE", "subclasse", "UNIDADE CONSUMIDORA"),
        ("HIST_GRUPO_TARIFARIO", "grupo_tarifario", "UNIDADE CONSUMIDORA"),
        ("HIST_MODALIDADE", "modalidade_tarifaria", "UNIDADE CONSUMIDORA"),
        ("HIST_TENSAO", "tensao_fornecimento", "UNIDADE CONSUMIDORA"),
        ("HIST_DEMANDA", "demanda_contratada", "UNIDADE CONSUMIDORA"),
        ("HIST_CONSUMO_MEDIO", "consumo_medio", "UNIDADE CONSUMIDORA"),
        ("HIST_VALOR_FATURADO", "valor_faturado", "UNIDADE CONSUMIDORA"),
        ("HIST_VALOR_MEDIDO", "valor_medido", "UNIDADE CONSUMIDORA"),
        ("HIST_VALOR_FATURA", "valor_fatura", "UNIDADE CONSUMIDORA"),
    ]

    for nome_aba, campo_valor, titulo_coluna in abas_historico:
        ws = wb.create_sheet(title=nome_aba)
        _preencher_aba_historico(ws, registros, campo_valor, titulo_coluna)

    wb.save(caminho_planilha)
    return caminho_planilha


# ============================================================== #
# ORQUESTRADOR
# ============================================================== #

def texter_orchestrator():
    PATH_OUTPUT.mkdir(parents=True, exist_ok=True)
    limpar_estado_processamento()

    # 1. Selecao de pasta de origem
    subfolders = [f.name for f in PATH_INPUT.iterdir() if f.is_dir()]
    print("\n--- SELECAO DE PASTA (ORIGEM: POPPLER) ---")
    for i, folder in enumerate(subfolders):
        print(f"{i} - {folder}")

    f_choice = int(input("Indice da pasta: "))
    selected_subfolder = subfolders[f_choice]

    src_dir = PATH_INPUT / selected_subfolder
    dst_dir_name = selected_subfolder.replace("Poppler", "Texter")
    dst_dir = PATH_OUTPUT / dst_dir_name
    dst_dir.mkdir(parents=True, exist_ok=True)
    limpar_arquivos_texter(dst_dir)

    # 2. Selecao de formato
    print("\n--- QUAL FORMATACAO APLICAR? ---")
    formatos = list(FORMATADORES.keys())
    for i, nome in enumerate(formatos):
        print(f"{i} - {nome}")
    fmt_choice = int(input("Indice do formato: "))
    funcao_formatadora = FORMATADORES[formatos[fmt_choice]]

    # 3. Escopo de execucao
    print("\n--- MODO DE EXECUCAO ---")
    print("1 - Todos os documentos da subpasta")
    print("2 - Apenas um documento especifico")
    mode = input("Escolha a opcao: ").strip()

    files = sorted([f.name for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".txt"])

    if mode == "2":
        for i, file_name in enumerate(files):
            print(f"{i} - {file_name}")
        file_choice = int(input("Indice do arquivo: "))
        files = [files[file_choice]]

    # 4. Processamento de arquivos Texter
    for file_name in files:
        input_path = src_dir / file_name
        print(f"Processando: {file_name}...")

        conteudo_bruto = carregar_arquivo(input_path)
        conteudo_para_parser = _normalizar_poppler_para_parser(conteudo_bruto)
        conteudo_formatado = funcao_formatadora(conteudo_para_parser, file_name)
        conteudo_saida = _converter_para_texto_saida(conteudo_formatado)
        indicador_tribf_irrf = _extrair_indicador_tribf_irrf(conteudo_bruto)

        if conteudo_saida and not conteudo_saida.endswith("\n"):
            conteudo_saida += "\n"
        conteudo_saida += f"INDICADOR TRIBF-IRRF\t{indicador_tribf_irrf}\n"

        output_name = _montar_nome_saida_texter(file_name)
        output_path = dst_dir / output_name
        salvar_arquivo(output_path, conteudo_saida)
        print(f"[OK] Arquivo Texter criado: {output_path}")

    caminho_planilha = _gerar_planilha_texter(dst_dir)
    print(f"[OK] Planilha gerada: {caminho_planilha}")

    print("\nFluxo Texter finalizado.")


if __name__ == "__main__":
    texter_orchestrator()
