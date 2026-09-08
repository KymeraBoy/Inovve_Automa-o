from pathlib import Path
import re
import pandas as pd


def valor_para_tex(valor):
    """Normaliza o valor lido da planilha para string adequada ao .tex."""
    if pd.isna(valor):
        return None

    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)

    return str(valor).strip()


def nome_arquivo_por_linha(linha, indice):
    """Define o nome do arquivo .tex com prioridade para _arquivo_origem."""
    origem = valor_para_tex(linha.get("_arquivo_origem"))
    if origem:
        if not origem.lower().endswith(".tex"):
            origem = f"{origem}.tex"
        return origem

    municipio = valor_para_tex(linha.get("nomeMunicipio"))
    if not municipio:
        return f"Dados_Municipio_{indice:03d}.tex"

    municipio = re.sub(r"[\\/:*?\"<>|]", "_", municipio)
    municipio = re.sub(r"\s+", "_", municipio)
    municipio = re.sub(r"_+", "_", municipio).strip("_")

    return f"Dados_{municipio}.tex"


def extrair_input_existente(caminho_arquivo):
    """Reaproveita a linha \\input de um arquivo já existente, se houver."""
    if not caminho_arquivo.exists():
        return None

    conteudo = caminho_arquivo.read_text(encoding="utf-8")

    match = re.search(
        r"^\s*\\input\{[^}]+\}\s*$",
        conteudo,
        flags=re.MULTILINE
    )

    return match.group(0).strip() if match else None


def linha_input_concessionaria(linha, base_dir):
    """
    Monta a linha \\input da concessionária a partir
    da coluna 'Concessionária' da planilha.
    """

    coluna_concessionaria = None

    # Procura a coluna ignorando espaços e maiúsculas/minúsculas
    for coluna in linha.index:
        if str(coluna).strip().casefold() == "concessionária".casefold():
            coluna_concessionaria = coluna
            break

    if coluna_concessionaria is None:
        return None

    concessionaria = valor_para_tex(linha.get(coluna_concessionaria))

    if not concessionaria:
        return None

    # Aceita caso a planilha já tenha o nome com .tex
    if not concessionaria.lower().endswith(".tex"):
        concessionaria = f"{concessionaria}.tex"

    caminho_concessionaria = (
        base_dir / "CONCESSIONARIAS" / concessionaria
    ).as_posix()

    return f"\\input{{{caminho_concessionaria}}}"


def linha_input_planilha(linha, base_dir):
    """Monta a linha \\input a partir da coluna Input da planilha."""
    coluna_input = None

    for coluna in linha.index:
        if str(coluna).strip().casefold() == "input":
            coluna_input = coluna
            break

    if coluna_input is None:
        return None

    valor_input = valor_para_tex(linha.get(coluna_input))

    if not valor_input:
        return None

    # Aceita conteúdo já no formato \input{...}
    if re.fullmatch(r"\\input\{[^}]+\}", valor_input):
        return valor_input

    valor_input = valor_input.replace("\\", "/")

    # Se for apenas o nome da concessionária/arquivo,
    # monta o caminho padrão da pasta.
    if "/" not in valor_input and ":" not in valor_input:
        if not valor_input.lower().endswith(".tex"):
            valor_input = f"{valor_input}.tex"

        caminho = (
            base_dir / "CONCESSIONARIAS" / valor_input
        ).as_posix()

        return f"\\input{{{caminho}}}"

    if not valor_input.lower().endswith(".tex"):
        valor_input = f"{valor_input}.tex"

    return f"\\input{{{valor_input}}}"


def excel_para_tex(arquivo_excel, pasta_saida):

    arquivo_excel = Path(arquivo_excel)
    pasta_saida = Path(pasta_saida)

    # Verifica a existência da planilha
    if not arquivo_excel.exists():
        print(f"Planilha não encontrada: {arquivo_excel}")
        return

    # Lê a planilha
    df = pd.read_excel(arquivo_excel, sheet_name="Municípios", dtype=object)

    # Verifica se está vazia
    if df.empty:
        print("A planilha está vazia. Nada para gerar.")
        return

    # Identifica as colunas que serão transformadas em \newcommand
    colunas_comandos = []

    for c in df.columns:
        nome_coluna = str(c).strip()

        # Estas colunas NÃO serão transformadas em \newcommand
        if nome_coluna.casefold() in {
            "_arquivo_origem",
            "concessionária".casefold(),
            "input"
        }:
            continue

        # Nome da coluna precisa começar com letra
        # e conter somente letras e números
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", nome_coluna):
            colunas_comandos.append(c)

    if not colunas_comandos:
        print("Nenhuma coluna de comando válida foi encontrada na planilha.")
        return

    pasta_saida.mkdir(parents=True, exist_ok=True)

    total = 0

    scripts_dir = Path(__file__).resolve().parent
    base_dir = scripts_dir.parent

    for indice, (_, linha) in enumerate(df.iterrows(), start=1):

        # Nome do arquivo .tex do município
        nome_arquivo = nome_arquivo_por_linha(linha, indice)
        caminho_tex = pasta_saida / nome_arquivo

        # ==========================================================
        # INPUT DA CONCESSIONÁRIA
        # ==========================================================

        input_concessionaria = linha_input_concessionaria(
            linha,
            base_dir
        )

        # ==========================================================
        # INPUT DA COLUNA INPUT
        # ==========================================================

        input_planilha = linha_input_planilha(
            linha,
            base_dir
        )

        # Se não houver input na planilha, tenta reaproveitar
        # um input existente no arquivo
        if not input_planilha:
            input_planilha = extrair_input_existente(caminho_tex)

        # ==========================================================
        # MONTA O CONTEÚDO DO ARQUIVO TEX
        # ==========================================================

        linhas_saida = []

        # Primeiro input: concessionária
        if input_concessionaria:
            linhas_saida.append(input_concessionaria)

        # Segundo input: caso exista
        if input_planilha:
            # Evita duplicar exatamente a mesma linha
            if input_planilha not in linhas_saida:
                linhas_saida.append(input_planilha)

        # ==========================================================
        # ADICIONA OS \newcommand
        # ==========================================================

        for coluna in colunas_comandos:

            valor = valor_para_tex(linha.get(coluna))

            if valor is None:
                continue

            linhas_saida.append(
                f"\\newcommand{{\\{coluna}}}{{{valor}}}"
            )

        # ==========================================================
        # GRAVA O ARQUIVO
        # ==========================================================

        conteudo = "\n".join(linhas_saida).rstrip() + "\n"

        caminho_tex.write_text(
            conteudo,
            encoding="utf-8"
        )

        total += 1

    print(
        f"Sucesso! Arquivos .tex gerados/atualizados em: "
        f"{pasta_saida}"
    )

    print(f"Total de arquivos processados: {total}")


if __name__ == "__main__":

    scripts_dir = Path(__file__).resolve().parent
    base_dir = scripts_dir.parent

    PLANILHA_ORIGEM = (
        scripts_dir / "Planilha_Municipios.xlsx"
    )

    PASTA_SAIDA_TEX = (
        base_dir / "MUNICIPIOS"
    )

    excel_para_tex(
        PLANILHA_ORIGEM,
        PASTA_SAIDA_TEX
    )
