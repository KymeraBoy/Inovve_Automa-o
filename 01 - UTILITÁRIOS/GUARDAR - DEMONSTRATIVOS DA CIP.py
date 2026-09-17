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
    DEMONSTRATIVO DA CIP 08-2026 - PM Aguiar -> Aguiar
    """
    nome_normalizado = nome_pasta.strip()

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
    Procura o município dentro da estrutura de pastas.
    """
    municipio_normalizado = normalizar_nome(
        nome_municipio
    )

    resultados = []

    # Percorre os estados
    for pasta_estado in listar_pastas(PASTA_EMPRESA):
        # Percorre os municípios daquele estado
        for pasta_municipio in listar_pastas(pasta_estado):
            if (
                normalizar_nome(pasta_municipio.name)
                == municipio_normalizado
            ):
                resultados.append(pasta_municipio)

    return resultados


# ============================================================
# LOCALIZAR DOCUMENTOS / CIP
# ============================================================

def encontrar_pasta_cip(pasta_municipio):
    """
    Dentro do município procura:

        Documentos
            └── CIP (ou Demonstrativo CIP / CIP Demonstrativos)
    """
    pasta_documentos = None

    for pasta in listar_pastas(pasta_municipio):
        if normalizar_nome(pasta.name) == "documentos":
            pasta_documentos = pasta
            break

    if pasta_documentos is None:
        return None

    # Procura por CIP ou variações dentro de Documentos
    for pasta in listar_pastas(pasta_documentos):
        nome_normal = normalizar_nome(pasta.name)
        if "cip" in nome_normal:
            return pasta

    return None


# ============================================================
# ANALISAR MOVIMENTAÇÕES
# ============================================================

def analisar_movimentacoes():
    movimentacoes = []
    problemas = []

    pastas_salvar = listar_pastas(PASTA_SALVAR)

    if not pastas_salvar:
        print("\nNenhuma pasta foi encontrada em SALVAR.")
        return movimentacoes, problemas

    print("\nAnalisando pastas de CIP...")
    print("-" * 80)

    for pasta_origem in pastas_salvar:
        nome_pasta = pasta_origem.name

        # Extrair município do nome
        municipio = extrair_municipio(nome_pasta)

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

        # Procurar município na estrutura
        resultados = encontrar_municipio(municipio)

        if len(resultados) == 0:
            problemas.append({
                "origem": pasta_origem,
                "municipio": municipio,
                "motivo": "Município não encontrado"
            })
            continue

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

        # Procurar Documentos/CIP
        pasta_cip = encontrar_pasta_cip(pasta_municipio)

        if pasta_cip is None:
            problemas.append({
                "origem": pasta_origem,
                "municipio": municipio,
                "pasta_municipio": pasta_municipio,
                "motivo": (
                    "A pasta Documentos/CIP "
                    "não foi encontrada."
                )
            })
            continue

        # Definir destino
        destino = pasta_cip / pasta_origem.name

        # Verificar conflito
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

def exibir_previa(movimentacoes, problemas):
    print("\n")
    print("=" * 80)
    print("PRÉVIA DAS MOVIMENTAÇÕES - DEMONSTRATIVO CIP")
    print("=" * 80)

    if movimentacoes:
        print(
            f"\n{len(movimentacoes)} "
            f"pasta(s) pronta(s) para movimentação.\n"
        )

        for numero, item in enumerate(movimentacoes, start=1):
            print("-" * 80)
            print(f"MOVIMENTAÇÃO {numero}")
            print(f"\nPasta:\n  {item['origem'].name}")
            print(f"\nMunicípio identificado:\n  {item['municipio'].name}")
            print(f"\nEstado:\n  {item['estado'].name}")
            print(f"\nORIGEM:\n  {item['origem']}")
            print(f"\nDESTINO:\n  {item['destino']}")
    else:
        print("\nNenhuma movimentação válida encontrada.")

    if problemas:
        print("\n")
        print("=" * 80)
        print("PASTAS QUE NÃO SERÃO MOVIMENTADAS")
        print("=" * 80)

        for numero, problema in enumerate(problemas, start=1):
            print("-" * 80)
            print(f"\nPROBLEMA {numero}")
            print(f"\nPasta:\n  {problema['origem']}")

            if "municipio" in problema:
                print(f"\nMunicípio identificado:\n  {problema['municipio']}")

            print(f"\nMotivo:\n  {problema['motivo']}")

            if "resultados" in problema:
                print("\nPossíveis correspondências:")
                for resultado in problema["resultados"]:
                    print(f"  - {resultado}")


# ============================================================
# EXECUTAR MOVIMENTAÇÕES
# ============================================================

def executar_movimentacoes(movimentacoes):
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
            if not origem.exists():
                raise FileNotFoundError("A pasta de origem não existe.")

            if destino.exists():
                raise FileExistsError("A pasta de destino já existe.")

            shutil.move(str(origem), str(destino))
            sucesso.append(item)

            print(f"\n[OK] {origem.name}")
            print(f"     → {destino}")

        except Exception as erro:
            erros.append({"item": item, "erro": erro})
            print(f"\n[ERRO] {origem.name}")
            print(f"       {erro}")

    return sucesso, erros


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("=" * 80)
    print("ORGANIZADOR DE PASTAS DE DEMONSTRATIVO CIP")
    print("=" * 80)

    print(f"\nPasta SALVAR:\n{PASTA_SALVAR}")
    print(f"\nPasta da empresa:\n{PASTA_EMPRESA}")

    if not PASTA_SALVAR.exists():
        print("\nERRO: A pasta SALVAR não existe.")
        input("\nPressione ENTER para sair...")
        return

    if not PASTA_EMPRESA.exists():
        print("\nERRO: A pasta da empresa não existe.")
        input("\nPressione ENTER para sair...")
        return

    movimentacoes, problemas = analisar_movimentacoes()

    exibir_previa(movimentacoes, problemas)

    if not movimentacoes:
        print("\nNenhuma pasta será movimentada.")
        input("\nPressione ENTER para sair...")
        return

    print("\n")
    print("=" * 80)
    print("CONFIRMAÇÃO DE SEGURANÇA")
    print("=" * 80)
    print(f"\nSerão movimentadas {len(movimentacoes)} pasta(s).")
    print("\nConfira cuidadosamente os destinos apresentados acima.")
    print("\nNenhuma pasta será sobrescrita.")

    resposta = input(
        "\nDeseja realizar as movimentações?"
        "\nDigite [S] para SIM ou [N] para NÃO: "
    ).strip().lower()

    if resposta != "s":
        print("\n" + "=" * 80)
        print("OPERAÇÃO CANCELADA")
        print("=" * 80)
        print("\nNenhuma pasta foi movimentada.")
        input("\nPressione ENTER para sair...")
        return

    sucesso, erros = executar_movimentacoes(movimentacoes)

    print("\n")
    print("=" * 80)
    print("RELATÓRIO FINAL")
    print("=" * 80)

    print(f"\nMovimentadas com sucesso: {len(sucesso)}")
    print(f"Erros: {len(erros)}")
    print(f"Não movimentadas: {len(problemas)}")

    if erros:
        print("\nERROS:")
        for erro in erros:
            print("-" * 80)
            print(f"Pasta:\n  {erro['item']['origem']}")
            print(f"\nDestino:\n  {erro['item']['destino']}")
            print(f"\nErro:\n  {erro['erro']}")

    print("\n")
    print("=" * 80)
    print("PROCESSO FINALIZADO")
    print("=" * 80)

    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    main()