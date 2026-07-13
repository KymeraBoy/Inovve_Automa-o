from pathlib import Path

def interpretar(texto):
    # Apenas <NL> é convertido em quebra de linha.
    return texto.replace("<NL>", "\n")


def substituir_texto(arquivos):
    texto_antigo = input("\nTexto que deseja substituir:\n> ")

    if texto_antigo == "":
        print("O texto a ser substituído não pode ser vazio.")
        return

    texto_novo = input(
        "\nNovo texto (use <NL> para quebra de linha; deixe vazio para apagar):\n> "
    )

    texto_novo = interpretar(texto_novo)

    total = 0

    for arquivo in arquivos:
        conteudo = arquivo.read_text(encoding="utf-8")

        ocorrencias = conteudo.count(texto_antigo)

        if ocorrencias:
            conteudo = conteudo.replace(texto_antigo, texto_novo)
            arquivo.write_text(conteudo, encoding="utf-8")

            print(f"{arquivo.name}: {ocorrencias} substituição(ões)")
            total += ocorrencias

    print(f"\nTotal de substituições: {total}")


def inserir_no_inicio_da_linha(arquivos):
    try:
        linha = int(input("\nNúmero da linha: "))
    except ValueError:
        print("Número de linha inválido.")
        return

    texto = input("Texto a inserir (use <NL> para quebra de linha): ")
    texto = interpretar(texto)

    modificados = 0

    for arquivo in arquivos:
        linhas = arquivo.read_text(encoding="utf-8").splitlines(keepends=True)

        if 1 <= linha <= len(linhas):
            linhas[linha - 1] = texto + linhas[linha - 1]

            arquivo.write_text("".join(linhas), encoding="utf-8")

            print(f"{arquivo.name}: linha {linha} modificada")
            modificados += 1
        else:
            print(f"{arquivo.name}: possui apenas {len(linhas)} linhas")

    print(f"\nArquivos modificados: {modificados}")


def deletar_linhas(arquivos):
    try:
        linha_inicial = int(input("\nLinha inicial a remover: "))
        linha_final = int(input("Linha final a remover: "))
    except ValueError:
        print("Número de linha inválido.")
        return

    if linha_inicial < 1 or linha_final < linha_inicial:
        print("Intervalo inválido.")
        return

    modificados = 0

    for arquivo in arquivos:
        linhas = arquivo.read_text(encoding="utf-8").splitlines(keepends=True)

        if linha_inicial > len(linhas):
            print(f"{arquivo.name}: possui apenas {len(linhas)} linhas")
            continue

        fim = min(linha_final, len(linhas))

        del linhas[linha_inicial - 1:fim]

        arquivo.write_text("".join(linhas), encoding="utf-8")

        print(f"{arquivo.name}: removidas as linhas {linha_inicial} até {fim}")
        modificados += 1

    print(f"\nArquivos modificados: {modificados}")


def main():
    pasta = Path(__file__).parent
    arquivos = list(pasta.glob("*.tex"))

    if not arquivos:
        print("Nenhum arquivo .tex encontrado.")
        return

    print("=" * 60)
    print("EDITOR DE ARQUIVOS .TEX")
    print("=" * 60)
    print("1 - Substituir texto")
    print("2 - Inserir texto no começo de uma linha")
    print("3 - Deletar linha(s)")
    print("=" * 60)

    opcao = input("Escolha uma opção: ")

    if opcao == "1":
        substituir_texto(arquivos)

    elif opcao == "2":
        inserir_no_inicio_da_linha(arquivos)

    elif opcao == "3":
        deletar_linhas(arquivos)

    else:
        print("Opção inválida.")


if __name__ == "__main__":
    main()