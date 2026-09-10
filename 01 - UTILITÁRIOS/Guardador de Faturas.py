import os
import shutil
import unicodedata
import re
from pathlib import Path


# ============================================================
# CONFIGURAÇÃO
# ============================================================

PASTA_SALVAR = Path(
    r"C:\Users\Usuário 1\Downloads\SALVAR"
)

PASTA_EMPRESA = Path(
    r"C:\Users\Usuário 1\OneDrive\PASTA ENERGIA 1\PARCEIROS\Municípios Thamires e Ruda"
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_nome(nome):
    """
    Normaliza um nome para facilitar a comparação.

    Exemplos:

        São José  -> sao jose
        SÃO JOSÉ  -> sao jose
        Aguiar    -> aguiar
    """

    nome = nome.strip().lower()

    # Remove acentos
    nome = unicodedata.normalize("NFD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if unicodedata.category(caractere) != "Mn"
    )

    # Remove espaços duplicados
    nome = " ".join(nome.split())

    return nome


def listar_pastas(caminho):
    """
    Retorna somente as pastas diretamente dentro do caminho.
    """

    try:

        return [
            pasta
            for pasta in caminho.iterdir()
            if pasta.is_dir()
        ]

    except PermissionError:

        print(
            f"\nERRO: Sem permissão para acessar:"
            f"\n{caminho}"
        )

        return []


# ============================================================
# IDENTIFICAR MUNICÍPIO
# ============================================================

def extrair_municipio(nome_pasta):
    """
    Extrai o município do nome da pasta.

    Exemplo:

    FATURAMENTO ENERGISA VENCT 23-09-2026 - PM Aguiar

    Resultado:

    Aguiar
    """

    nome_normalizado = nome_pasta.strip()

    # Procura "PM " no nome.
    #
    # O (?:^|\s) garante que estamos procurando
    # PM como uma palavra separada.
    #
    # O restante do nome depois de PM será
    # considerado o município.

    resultado = re.search(
        r"(?:^|\s)PM\s+(.+?)\s*$",
        nome_normalizado,
        flags=re.IGNORECASE
    )

    if resultado:

        municipio = resultado.group(1).strip()

        return municipio

    return None


# ============================================================
# LOCALIZAR MUNICÍPIO NA ESTRUTURA DA EMPRESA
# ============================================================

def encontrar_municipio(nome_municipio):
    """
    Procura o município dentro da estrutura:

        PASTA_EMPRESA
        ├── Estado
        │   ├── Município
        │   │   └── Documentos
        │   │       └── Faturas
        │   └── Município
        │
        └── Estado

    Retorna todas as correspondências encontradas.
    """

    municipio_normalizado = normalizar_nome(
        nome_municipio
    )

    resultados = []

    # Percorre os estados
    for pasta_estado in listar_pastas(PASTA_EMPRESA):

        # Percorre os municípios daquele estado
        for pasta_municipio in listar_pastas(
            pasta_estado
        ):

            if (
                normalizar_nome(pasta_municipio.name)
                == municipio_normalizado
            ):

                resultados.append(
                    pasta_municipio
                )

    return resultados


# ============================================================
# LOCALIZAR DOCUMENTOS / FATURAS
# ============================================================

def encontrar_pasta_faturas(pasta_municipio):
    """
    Dentro do município procura:

        Documentos
            └── Faturas
    """

    pasta_documentos = None

    for pasta in listar_pastas(
        pasta_municipio
    ):

        if (
            normalizar_nome(pasta.name)
            == "documentos"
        ):

            pasta_documentos = pasta
            break

    if pasta_documentos is None:
        return None

    # Procura Faturas dentro de Documentos
    for pasta in listar_pastas(
        pasta_documentos
    ):

        if (
            normalizar_nome(pasta.name)
            == "faturas"
        ):

            return pasta

    return None


# ============================================================
# ANALISAR MOVIMENTAÇÕES
# ============================================================

def analisar_movimentacoes():

    movimentacoes = []
    problemas = []

    pastas_salvar = listar_pastas(
        PASTA_SALVAR
    )

    if not pastas_salvar:

        print(
            "\nNenhuma pasta foi encontrada em SALVAR."
        )

        return movimentacoes, problemas

    print("\nAnalisando pastas...")
    print("-" * 80)

    for pasta_origem in pastas_salvar:

        nome_pasta = pasta_origem.name

        # ----------------------------------------------------
        # Extrair município do nome
        # ----------------------------------------------------

        municipio = extrair_municipio(
            nome_pasta
        )

        if municipio is None:

            problemas.append({
                "origem": pasta_origem,
                "motivo": (
                    "Não foi possível identificar "
                    "o município no nome da pasta."
                )
            })

            continue

        print(
            f"\nPasta encontrada:"
            f"\n  {nome_pasta}"
        )

        print(
            f"Município identificado:"
            f"\n  {municipio}"
        )

        # ----------------------------------------------------
        # Procurar município
        # ----------------------------------------------------

        resultados = encontrar_municipio(
            municipio
        )

        # Município não encontrado
        if len(resultados) == 0:

            problemas.append({
                "origem": pasta_origem,
                "municipio": municipio,
                "motivo": "Município não encontrado"
            })

            continue

        # Mais de um município encontrado
        if len(resultados) > 1:

            problemas.append({
                "origem": pasta_origem,
                "municipio": municipio,
                "motivo": (
                    "Mais de um município com esse "
                    "nome foi encontrado."
                ),
                "resultados": resultados
            })

            continue

        pasta_municipio = resultados[0]

        # ----------------------------------------------------
        # Procurar Documentos/Faturas
        # ----------------------------------------------------

        pasta_faturas = encontrar_pasta_faturas(
            pasta_municipio
        )

        if pasta_faturas is None:

            problemas.append({
                "origem": pasta_origem,
                "municipio": municipio,
                "pasta_municipio": pasta_municipio,
                "motivo": (
                    "A pasta Documentos/Faturas "
                    "não foi encontrada."
                )
            })

            continue

        # ----------------------------------------------------
        # Definir destino
        # ----------------------------------------------------

        destino = (
            pasta_faturas /
            pasta_origem.name
        )

        # ----------------------------------------------------
        # Verificar conflito
        # ----------------------------------------------------

        if destino.exists():

            problemas.append({
                "origem": pasta_origem,
                "municipio": municipio,
                "destino": destino,
                "motivo": (
                    "Já existe uma pasta com esse "
                    "nome no destino."
                )
            })

            continue

        # ----------------------------------------------------
        # Registrar movimentação
        # ----------------------------------------------------

        movimentacoes.append({
            "origem": pasta_origem,
            "destino": destino,
            "municipio": pasta_municipio,
            "estado": pasta_municipio.parent
        })

    return movimentacoes, problemas


# ============================================================
# EXIBIR PRÉVIA
# ============================================================

def exibir_previa(
    movimentacoes,
    problemas
):

    print("\n")
    print("=" * 80)
    print("PRÉVIA DAS MOVIMENTAÇÕES")
    print("=" * 80)

    # --------------------------------------------------------
    # MOVIMENTAÇÕES
    # --------------------------------------------------------

    if movimentacoes:

        print(
            f"\n{len(movimentacoes)} "
            f"pasta(s) pronta(s) para movimentação.\n"
        )

        for numero, item in enumerate(
            movimentacoes,
            start=1
        ):

            print("-" * 80)

            print(
                f"MOVIMENTAÇÃO {numero}"
            )

            print(
                f"\nPasta:"
                f"\n  {item['origem'].name}"
            )

            print(
                f"\nMunicípio identificado:"
                f"\n  {item['municipio'].name}"
            )

            print(
                f"\nEstado:"
                f"\n  {item['estado'].name}"
            )

            print(
                f"\nORIGEM:"
                f"\n  {item['origem']}"
            )

            print(
                f"\nDESTINO:"
                f"\n  {item['destino']}"
            )

    else:

        print(
            "\nNenhuma movimentação válida encontrada."
        )

    # --------------------------------------------------------
    # PROBLEMAS
    # --------------------------------------------------------

    if problemas:

        print("\n")
        print("=" * 80)
        print(
            "PASTAS QUE NÃO SERÃO MOVIMENTADAS"
        )
        print("=" * 80)

        for numero, problema in enumerate(
            problemas,
            start=1
        ):

            print("-" * 80)

            print(
                f"\nPROBLEMA {numero}"
            )

            print(
                f"\nPasta:"
                f"\n  {problema['origem']}"
            )

            if "municipio" in problema:

                print(
                    f"\nMunicípio identificado:"
                    f"\n  {problema['municipio']}"
                )

            print(
                f"\nMotivo:"
                f"\n  {problema['motivo']}"
            )

            if "resultados" in problema:

                print(
                    "\nPossíveis correspondências:"
                )

                for resultado in (
                    problema["resultados"]
                ):

                    print(
                        f"  - {resultado}"
                    )


# ============================================================
# EXECUTAR MOVIMENTAÇÕES
# ============================================================

def executar_movimentacoes(
    movimentacoes
):

    sucesso = []
    erros = []

    print("\n")
    print("=" * 80)
    print("EXECUTANDO MOVIMENTAÇÕES")
    print("=" * 80)

    for item in movimentacoes:

        origem = item["origem"]
        destino = item["destino"]

        try:

            # Segurança adicional
            if not origem.exists():

                raise FileNotFoundError(
                    "A pasta de origem não existe."
                )

            # Nunca sobrescrever
            if destino.exists():

                raise FileExistsError(
                    "A pasta de destino já existe."
                )

            # Executar movimentação
            shutil.move(
                str(origem),
                str(destino)
            )

            sucesso.append(item)

            print(
                f"\n[OK] {origem.name}"
            )

            print(
                f"     → {destino}"
            )

        except Exception as erro:

            erros.append({
                "item": item,
                "erro": erro
            })

            print(
                f"\n[ERRO] {origem.name}"
            )

            print(
                f"       {erro}"
            )

    return sucesso, erros


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    print("=" * 80)
    print(
        "ORGANIZADOR DE PASTAS DE FATURAS"
    )
    print("=" * 80)

    print(
        "\nPasta SALVAR:"
        f"\n{PASTA_SALVAR}"
    )

    print(
        "\nPasta da empresa:"
        f"\n{PASTA_EMPRESA}"
    )

    # --------------------------------------------------------
    # Verificar caminhos
    # --------------------------------------------------------

    if not PASTA_SALVAR.exists():

        print(
            "\nERRO: A pasta SALVAR não existe."
        )

        input(
            "\nPressione ENTER para sair..."
        )

        return

    if not PASTA_EMPRESA.exists():

        print(
            "\nERRO: A pasta da empresa não existe."
        )

        input(
            "\nPressione ENTER para sair..."
        )

        return

    # --------------------------------------------------------
    # Analisar
    # --------------------------------------------------------

    movimentacoes, problemas = (
        analisar_movimentacoes()
    )

    # --------------------------------------------------------
    # Mostrar prévia
    # --------------------------------------------------------

    exibir_previa(
        movimentacoes,
        problemas
    )

    # --------------------------------------------------------
    # Nada para mover
    # --------------------------------------------------------

    if not movimentacoes:

        print(
            "\nNenhuma pasta será movimentada."
        )

        input(
            "\nPressione ENTER para sair..."
        )

        return

    # --------------------------------------------------------
    # CONFIRMAÇÃO
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("CONFIRMAÇÃO DE SEGURANÇA")
    print("=" * 80)

    print(
        f"\nSerão movimentadas "
        f"{len(movimentacoes)} pasta(s)."
    )

    print(
        "\nConfira cuidadosamente os destinos "
        "apresentados acima."
    )

    print(
        "\nNenhuma pasta será sobrescrita."
    )

    resposta = input(
        "\nDeseja realizar as movimentações?"
        "\nDigite [S] para SIM ou [N] para NÃO: "
    ).strip().lower()

    if resposta != "s":

        print(
            "\n"
            + "=" * 80
        )

        print(
            "OPERAÇÃO CANCELADA"
        )

        print(
            "=" * 80
        )

        print(
            "\nNenhuma pasta foi movimentada."
        )

        input(
            "\nPressione ENTER para sair..."
        )

        return

    # --------------------------------------------------------
    # Executar
    # --------------------------------------------------------

    sucesso, erros = (
        executar_movimentacoes(
            movimentacoes
        )
    )

    # --------------------------------------------------------
    # Relatório
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("RELATÓRIO FINAL")
    print("=" * 80)

    print(
        f"\nMovimentadas com sucesso: "
        f"{len(sucesso)}"
    )

    print(
        f"Erros: "
        f"{len(erros)}"
    )

    print(
        f"Não movimentadas: "
        f"{len(problemas)}"
    )

    if erros:

        print("\nERROS:")

        for erro in erros:

            print("-" * 80)

            print(
                f"Pasta:"
                f"\n  {erro['item']['origem']}"
            )

            print(
                f"\nDestino:"
                f"\n  {erro['item']['destino']}"
            )

            print(
                f"\nErro:"
                f"\n  {erro['erro']}"
            )

    print("\n")
    print("=" * 80)
    print("PROCESSO FINALIZADO")
    print("=" * 80)

    input(
        "\nPressione ENTER para sair..."
    )


# ============================================================
# INICIAR PROGRAMA
# ============================================================

if __name__ == "__main__":
    main()
