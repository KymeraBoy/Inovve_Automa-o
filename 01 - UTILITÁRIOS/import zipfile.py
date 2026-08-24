import zipfile
from pathlib import Path

try:
    import py7zr
except ImportError:
    print("A biblioteca 'py7zr' não está instalada.")
    print("Instale com: pip install py7zr")
    input("\nPressione Enter para sair...")
    exit()

# Pasta onde o script está localizado
pasta = Path(__file__).resolve().parent

# Procura ZIPs e 7Zs
arquivos = list(pasta.glob("*.zip")) + list(pasta.glob("*.7z"))

if not arquivos:
    print("Nenhum arquivo .zip ou .7z encontrado.")
else:
    for arquivo in arquivos:
        destino = pasta / arquivo.stem
        destino.mkdir(exist_ok=True)

        print(f"\nExtraindo: {arquivo.name}")

        try:
            if arquivo.suffix.lower() == ".zip":
                with zipfile.ZipFile(arquivo, "r") as zip_ref:
                    zip_ref.extractall(destino)

            elif arquivo.suffix.lower() == ".7z":
                with py7zr.SevenZipFile(arquivo, mode="r") as seven_zip:
                    seven_zip.extractall(path=destino)

            print(f"OK: {destino}")

        except zipfile.BadZipFile:
            print(f"ERRO: {arquivo.name} não é um ZIP válido.")

        except Exception as erro:
            print(f"ERRO ao extrair {arquivo.name}: {erro}")

    print("\nTodos os arquivos foram processados!")

input("\nPressione Enter para sair...")