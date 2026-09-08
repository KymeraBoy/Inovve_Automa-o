import re
import pandas as pd
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Border,
    Side,
    Alignment
)
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter


def extrair_dados_tex(caminho_arquivo):
    """
    Lê um arquivo .tex e extrai todos os pares:

    \\newcommand{\\chave}{valor}

    e também:

    \\providecommand{\\chave}{valor}
    """

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Regex para capturar:
    # \newcommand{\nomeDoComando}{Conteudo}
    # \providecommand{\nomeDoComando}{Conteudo}
    padrao = (
        r'\\(?:newcommand|providecommand)'
        r'\{\\([^}]+)\}'
        r'\{(.*?)\}'
        r'(?=\s*(?:\\newcommand|\\providecommand|\\input|%|$))'
    )

    matches = re.findall(
        padrao,
        conteudo,
        flags=re.DOTALL
    )

    dados = {}

    for chave, valor in matches:

        # Limpa espaços em branco ou quebras de linha
        valor_limpo = valor.strip()

        # Remove comentários ao final da linha
        valor_limpo = re.sub(
            r'%.*$',
            '',
            valor_limpo
        ).strip()

        dados[chave] = valor_limpo

    return dados


def extrair_concessionaria_tex(caminho_arquivo):
    """
    Procura no arquivo .tex um comando \\input{...}
    que aponte para a pasta CONCESSIONARIAS.

    Exemplo encontrado no .tex:

    \\input{C:/Users/Usuário 1/Documents/Inovve_Automação/
    GERADOR DE DOCUMENTOS/CONCESSIONARIAS/ENEL}

    Retorna:

    ENEL

    Também funciona se houver .tex no final:

    \\input{.../CONCESSIONARIAS/ENEL.tex}

    Caso não encontre nenhuma referência para
    CONCESSIONARIAS, retorna uma string vazia.
    """

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Procura todos os comandos \input{...}
    padrao_input = r'\\input\s*\{([^}]*)\}'

    inputs = re.findall(
        padrao_input,
        conteudo
    )

    for caminho_input in inputs:

        caminho_input = caminho_input.strip()

        # Normaliza barras para facilitar a comparação
        caminho_normalizado = caminho_input.replace(
            '\\',
            '/'
        )

        # Verifica se o input aponta para CONCESSIONARIAS
        if '/CONCESSIONARIAS/' in caminho_normalizado.upper():

            # Pega tudo que vem depois de CONCESSIONARIAS/
            partes = re.split(
                r'/CONCESSIONARIAS/',
                caminho_normalizado,
                flags=re.IGNORECASE
            )

            if len(partes) > 1:

                concessionaria = partes[-1].strip()                

                # Remove barras residuais
                concessionaria = concessionaria.rstrip('/')

                return concessionaria

    return ''


def processar_pasta_tex(pasta_origem):
    """
    Processa todos os arquivos .tex encontrados diretamente
    na pasta e retorna uma lista de dicionários.

    Para cada município também identifica a concessionária
    através do comando:

    \\input{.../CONCESSIONARIAS/NOME_DA_CONCESSIONARIA}
    """

    pasta = Path(pasta_origem)

    lista_dados = []

    for arquivo in sorted(pasta.glob("*.tex")):

        dados = extrair_dados_tex(arquivo)

        if dados:

            # -------------------------------------------------
            # IDENTIFICA A CONCESSIONÁRIA DO MUNICÍPIO
            # -------------------------------------------------

            concessionaria = extrair_concessionaria_tex(
                arquivo
            )

            dados['Concessionária'] = concessionaria

            # -------------------------------------------------
            # ADICIONA O NOME DO ARQUIVO COMO REFERÊNCIA
            # -------------------------------------------------

            dados['_arquivo_origem'] = arquivo.name

            lista_dados.append(dados)

    return lista_dados


def processar_pasta_empresas(pasta_origem):
    """
    Processa as empresas.

    Estrutura esperada:

    EMPRESAS/
    ├── Empresa A/
    │   └── preambulo.tex
    │
    ├── Empresa B/
    │   └── preambulo.tex
    │
    └── Empresa C/
        └── preambulo.tex

    Cada pasta representa uma empresa e deve possuir
    um arquivo preambulo.tex.

    São extraídos os comandos:

    \\providecommand{\\RepresentanteEmpresa}{...}
    \\providecommand{\\EmailEmpresa}{...}
    \\providecommand{\\CNPJEmpresa}{...}
    \\providecommand{\\TelefoneEmpresa}{...}
    """

    pasta = Path(pasta_origem)

    lista_empresas = []

    comandos_empresa = [
        'RepresentanteEmpresa',
        'EmailEmpresa',
        'CNPJEmpresa',
        'TelefoneEmpresa'
    ]

    if not pasta.exists():

        print(
            f"Aviso: a pasta de empresas não existe: "
            f"{pasta}"
        )

        return lista_empresas

    for pasta_empresa in sorted(pasta.iterdir()):

        if not pasta_empresa.is_dir():
            continue

        nome_empresa = pasta_empresa.name

        caminho_preambulo = (
            pasta_empresa / "preambulo.tex"
        )

        if not caminho_preambulo.exists():

            print(
                f"Aviso: a empresa '{nome_empresa}' "
                f"não possui preambulo.tex."
            )

            continue

        try:

            dados_tex = extrair_dados_tex(
                caminho_preambulo
            )

        except Exception as erro:

            print(
                f"Erro ao processar a empresa "
                f"'{nome_empresa}': {erro}"
            )

            continue

        dados_empresa = {
            'Empresa': nome_empresa
        }

        for comando in comandos_empresa:

            dados_empresa[comando] = (
                dados_tex.get(comando, '')
            )

        dados_empresa['_arquivo_origem'] = (
            str(caminho_preambulo)
        )

        lista_empresas.append(
            dados_empresa
        )

    return lista_empresas


def formatar_aba(ws, nome_tabela):
    """
    Aplica a formatação visual profissional a uma aba
    específica da planilha.
    """

    # ---------------------------------------------------------
    # PALETA DE CORES
    # ---------------------------------------------------------

    azul_escuro = "1F4E78"
    azul_claro = "D9EAF7"
    cinza_claro = "F3F6F9"
    cinza_borda = "D9E1F2"
    branco = "FFFFFF"
    preto = "1F1F1F"

    # ---------------------------------------------------------
    # ESTILOS
    # ---------------------------------------------------------

    fonte_cabecalho = Font(
        name="Calibri",
        size=11,
        bold=True,
        color=branco
    )

    preenchimento_cabecalho = PatternFill(
        fill_type="solid",
        fgColor=azul_escuro
    )

    preenchimento_origem = PatternFill(
        fill_type="solid",
        fgColor=azul_claro
    )

    preenchimento_alternado = PatternFill(
        fill_type="solid",
        fgColor=cinza_claro
    )

    borda_fina = Border(
        left=Side(
            style="thin",
            color=cinza_borda
        ),
        right=Side(
            style="thin",
            color=cinza_borda
        ),
        top=Side(
            style="thin",
            color=cinza_borda
        ),
        bottom=Side(
            style="thin",
            color=cinza_borda
        )
    )

    # ---------------------------------------------------------
    # CABEÇALHO
    # ---------------------------------------------------------

    for cell in ws[1]:

        cell.font = fonte_cabecalho

        cell.fill = preenchimento_cabecalho

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )

        cell.border = borda_fina

    ws.row_dimensions[1].height = 30

    # ---------------------------------------------------------
    # DADOS
    # ---------------------------------------------------------

    for row in ws.iter_rows(
        min_row=2,
        max_row=ws.max_row,
        min_col=1,
        max_col=ws.max_column
    ):

        for cell in row:

            cell.font = Font(
                name="Calibri",
                size=10,
                color=preto
            )

            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True
            )

            cell.border = borda_fina

        if row[0].row % 2 == 0:

            for cell in row:
                cell.fill = preenchimento_alternado

    # ---------------------------------------------------------
    # DESTAQUE DA PRIMEIRA COLUNA
    # ---------------------------------------------------------

    if ws.max_column >= 1:

        for row in range(
            2,
            ws.max_row + 1
        ):

            cell = ws.cell(
                row=row,
                column=1
            )

            cell.fill = preenchimento_origem

            cell.font = Font(
                name="Calibri",
                size=10,
                bold=True,
                color=azul_escuro
            )

            cell.alignment = Alignment(
                vertical="top",
                horizontal="left",
                wrap_text=True
            )

    # ---------------------------------------------------------
    # REMOVE TABELAS EXISTENTES
    # ---------------------------------------------------------

    for tabela_nome in list(ws.tables.keys()):
        del ws.tables[tabela_nome]

    # ---------------------------------------------------------
    # CONVERTE O INTERVALO EM UMA TABELA DO EXCEL
    # ---------------------------------------------------------

    if ws.max_row >= 2 and ws.max_column >= 1:

        ultima_coluna = get_column_letter(
            ws.max_column
        )

        referencia_tabela = (
            f"A1:{ultima_coluna}{ws.max_row}"
        )

        tabela = Table(
            displayName=nome_tabela,
            ref=referencia_tabela
        )

        estilo_tabela = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False
        )

        tabela.tableStyleInfo = estilo_tabela

        ws.add_table(tabela)

    # ---------------------------------------------------------
    # CONGELA O CABEÇALHO
    # ---------------------------------------------------------

    ws.freeze_panes = "A2"

    # ---------------------------------------------------------
    # AJUSTE AUTOMÁTICO DA LARGURA DAS COLUNAS
    # ---------------------------------------------------------

    for coluna in range(
        1,
        ws.max_column + 1
    ):

        letra_coluna = get_column_letter(
            coluna
        )

        maior_tamanho = 0

        for cell in ws[letra_coluna]:

            if cell.value is not None:

                tamanho = len(
                    str(cell.value)
                )

                if tamanho > maior_tamanho:
                    maior_tamanho = tamanho

        largura = min(
            max(maior_tamanho + 2, 12),
            45
        )

        if coluna == 1:

            largura = min(
                max(maior_tamanho + 2, 20),
                40
            )

        ws.column_dimensions[
            letra_coluna
        ].width = largura

    # ---------------------------------------------------------
    # ALTURA DAS LINHAS
    # ---------------------------------------------------------

    for linha in range(
        2,
        ws.max_row + 1
    ):

        ws.row_dimensions[
            linha
        ].height = 35

    # ---------------------------------------------------------
    # CONFIGURAÇÕES DE IMPRESSÃO
    # ---------------------------------------------------------

    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0

    ws.page_setup.orientation = "landscape"

    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    ws.print_title_rows = "1:1"

    ws.page_margins.left = 0.25
    ws.page_margins.right = 0.25
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5

    ws.sheet_view.showGridLines = False


def criar_excel(
    dados_municipios,
    dados_concessionarias,
    dados_empresas,
    arquivo_saida_excel
):
    """
    Cria o arquivo Excel com três abas:

    1. Municípios
    2. Concessionárias
    3. Empresas
    """

    arquivo_saida_excel = Path(
        arquivo_saida_excel
    )

    arquivo_saida_excel.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # DATAFRAME DOS MUNICÍPIOS
    # ---------------------------------------------------------

    if dados_municipios:

        df_municipios = pd.DataFrame(
            dados_municipios
        )

        # Garante que Concessionária fique
        # próxima do arquivo de origem.
        colunas_municipios = (
            ['_arquivo_origem', 'Concessionária'] +
            [
                c
                for c in df_municipios.columns
                if c not in [
                    '_arquivo_origem',
                    'Concessionária'
                ]
            ]
        )

        # Remove possíveis duplicações
        colunas_municipios = list(
            dict.fromkeys(
                colunas_municipios
            )
        )

        df_municipios = df_municipios[
            colunas_municipios
        ]

    else:

        df_municipios = pd.DataFrame(
            columns=[
                '_arquivo_origem',
                'Concessionária'
            ]
        )

    # ---------------------------------------------------------
    # DATAFRAME DAS CONCESSIONÁRIAS
    # ---------------------------------------------------------

    if dados_concessionarias:

        df_concessionarias = pd.DataFrame(
            dados_concessionarias
        )

        colunas_concessionarias = (
            ['_arquivo_origem'] +
            [
                c
                for c in df_concessionarias.columns
                if c != '_arquivo_origem'
            ]
        )

        df_concessionarias = (
            df_concessionarias[
                colunas_concessionarias
            ]
        )

    else:

        df_concessionarias = pd.DataFrame(
            columns=['_arquivo_origem']
        )

    # ---------------------------------------------------------
    # DATAFRAME DAS EMPRESAS
    # ---------------------------------------------------------

    colunas_empresas = [
        'Empresa',
        'RepresentanteEmpresa',
        'EmailEmpresa',
        'CNPJEmpresa',
        'TelefoneEmpresa'
    ]

    if dados_empresas:

        df_empresas = pd.DataFrame(
            dados_empresas
        )

        for coluna in colunas_empresas:

            if coluna not in df_empresas.columns:
                df_empresas[coluna] = ''

        df_empresas = df_empresas[
            colunas_empresas
        ]

    else:

        df_empresas = pd.DataFrame(
            columns=colunas_empresas
        )

    # ---------------------------------------------------------
    # CRIA O EXCEL COM AS TRÊS ABAS
    # ---------------------------------------------------------

    with pd.ExcelWriter(
        arquivo_saida_excel,
        engine="openpyxl"
    ) as writer:

        df_municipios.to_excel(
            writer,
            index=False,
            sheet_name="Municípios"
        )

        df_concessionarias.to_excel(
            writer,
            index=False,
            sheet_name="Concessionárias"
        )

        df_empresas.to_excel(
            writer,
            index=False,
            sheet_name="Empresas"
        )

    # ---------------------------------------------------------
    # ABRE O EXCEL E FORMATA AS ABAS
    # ---------------------------------------------------------

    wb = load_workbook(
        arquivo_saida_excel
    )

    # ---------------------------------------------------------
    # ABA MUNICÍPIOS
    # ---------------------------------------------------------

    ws_municipios = wb["Municípios"]

    formatar_aba(
        ws_municipios,
        "TabelaMunicipios"
    )

    # ---------------------------------------------------------
    # ABA CONCESSIONÁRIAS
    # ---------------------------------------------------------

    ws_concessionarias = wb[
        "Concessionárias"
    ]

    formatar_aba(
        ws_concessionarias,
        "TabelaConcessionarias"
    )

    # ---------------------------------------------------------
    # ABA EMPRESAS
    # ---------------------------------------------------------

    ws_empresas = wb["Empresas"]

    formatar_aba(
        ws_empresas,
        "TabelaEmpresas"
    )

    # ---------------------------------------------------------
    # ORDEM DAS ABAS
    # ---------------------------------------------------------

    wb._sheets = [
        ws_municipios,
        ws_concessionarias,
        ws_empresas
    ]

    # ---------------------------------------------------------
    # SALVA
    # ---------------------------------------------------------

    wb.save(
        arquivo_saida_excel
    )


def tex_para_excel(
    pasta_municipios,
    pasta_concessionarias,
    pasta_empresas,
    arquivo_saida_excel
):
    """
    Processa:

    MUNICIPIOS/
    CONCESSIONARIAS/
    EMPRESAS/

    e gera um único Excel com:

    - Aba Municípios
    - Aba Concessionárias
    - Aba Empresas
    """

    pasta_municipios = Path(
        pasta_municipios
    )

    pasta_concessionarias = Path(
        pasta_concessionarias
    )

    pasta_empresas = Path(
        pasta_empresas
    )

    # ---------------------------------------------------------
    # PROCESSA MUNICÍPIOS
    # ---------------------------------------------------------

    dados_municipios = processar_pasta_tex(
        pasta_municipios
    )

    # ---------------------------------------------------------
    # PROCESSA CONCESSIONÁRIAS
    # ---------------------------------------------------------

    dados_concessionarias = processar_pasta_tex(
        pasta_concessionarias
    )

    # ---------------------------------------------------------
    # PROCESSA EMPRESAS
    # ---------------------------------------------------------

    dados_empresas = processar_pasta_empresas(
        pasta_empresas
    )

    # ---------------------------------------------------------
    # AVISOS
    # ---------------------------------------------------------

    if not dados_municipios:

        print(
            "Aviso: nenhum arquivo .tex "
            "foi encontrado na pasta MUNICIPIOS."
        )

    if not dados_concessionarias:

        print(
            "Aviso: nenhum arquivo .tex "
            "foi encontrado na pasta CONCESSIONARIAS."
        )

    if not dados_empresas:

        print(
            "Aviso: nenhuma empresa válida "
            "foi encontrada na pasta EMPRESAS."
        )

    # ---------------------------------------------------------
    # CRIA O EXCEL
    # ---------------------------------------------------------

    criar_excel(
        dados_municipios,
        dados_concessionarias,
        dados_empresas,
        arquivo_saida_excel
    )

    # ---------------------------------------------------------
    # MENSAGENS
    # ---------------------------------------------------------

    print(
        f"Sucesso! Planilha gerada em: "
        f"{arquivo_saida_excel}"
    )

    print(
        f"Total de municípios processados: "
        f"{len(dados_municipios)}"
    )

    print(
        f"Total de concessionárias processadas: "
        f"{len(dados_concessionarias)}"
    )

    print(
        f"Total de empresas processadas: "
        f"{len(dados_empresas)}"
    )


# =============================================================
# CONFIGURAÇÃO E EXECUÇÃO
# =============================================================

if __name__ == "__main__":

    # Usa caminhos relativos ao script
    # para funcionar em qualquer máquina.

    scripts_dir = Path(
        __file__
    ).resolve().parent

    base_dir = scripts_dir.parent

    # ---------------------------------------------------------
    # PASTAS DE ORIGEM
    # ---------------------------------------------------------

    PASTA_MUNICIPIOS = (
        base_dir / "MUNICIPIOS"
    )

    PASTA_CONCESSIONARIAS = (
        base_dir / "CONCESSIONARIAS"
    )

    PASTA_EMPRESAS = (
        base_dir / "EMPRESAS"
    )

    # ---------------------------------------------------------
    # ARQUIVO DE SAÍDA
    # ---------------------------------------------------------

    PLANILHA_SAIDA = (
        scripts_dir /
        "Planilha_Municipios.xlsx"
    )

    # ---------------------------------------------------------
    # EXECUTA
    # ---------------------------------------------------------

    tex_para_excel(
        PASTA_MUNICIPIOS,
        PASTA_CONCESSIONARIAS,
        PASTA_EMPRESAS,
        PLANILHA_SAIDA
    )
