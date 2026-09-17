from pathlib import Path

"""Esse programa serve para gerar um documento .txt contendo a lista de nomes das pastas dentro da pasta onde ele estiver.
    Funcionamento: Por o código na pasta e executa-lo"""

# Pasta onde o script está localizado
pasta_script = Path(__file__).resolve().parent

# Lista apenas as subpastas
subpastas = sorted(
    pasta.name
    for pasta in pasta_script.iterdir()
    if pasta.is_dir()
)

# Caminho do arquivo TXT que será criado
arquivo_txt = pasta_script / "LISTA DAS SUBPASTAS.txt"

# Salva a lista no arquivo
arquivo_txt.write_text(
    "\n".join(subpastas),
    encoding="utf-8"
)
