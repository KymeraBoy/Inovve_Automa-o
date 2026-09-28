from pathlib import Path

# Pasta onde o script está localizado
pasta = Path(__file__).parent

# Arquivo de saída
arquivo_saida = pasta / "resultado.txt"

# Encontra todos os .txt, exceto o próprio resultado.txt
arquivos = sorted(
    arquivo for arquivo in pasta.glob("*.txt")
    if arquivo.name != arquivo_saida.name
)

with arquivo_saida.open("w", encoding="utf-8") as saida:
    for arquivo in arquivos:
        with arquivo.open("r", encoding="utf-8") as entrada:
            # Pega as 5 primeiras linhas
            primeiras_linhas = []
            for _ in range(5):
                linha = entrada.readline()
                if not linha:
                    break
                primeiras_linhas.append(linha.rstrip("\n"))

            # Escreve no arquivo de saída
            saida.write("\n".join(primeiras_linhas))
            saida.write("\n=====================\n")

print(f"Concluído! {len(arquivos)} arquivos processados.")
print(f"Resultado salvo em: {arquivo_saida}")
