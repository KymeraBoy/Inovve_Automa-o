from pathlib import Path
import importlib
import sys


try:
	_pdf_lib = importlib.import_module("pypdf")
except ImportError:
	try:
		_pdf_lib = importlib.import_module("PyPDF2")
	except ImportError:
		print("Biblioteca de PDF nao encontrada.")
		print("Instale com o comando abaixo no mesmo Python que executa este arquivo:")
		print(f'"{sys.executable}" -m pip install pypdf')
		raise SystemExit(1)

PdfReader = _pdf_lib.PdfReader
PdfWriter = _pdf_lib.PdfWriter


def listar_pdfs(base_dir: Path) -> list[Path]:
	return sorted(base_dir.glob("*.pdf"), key=lambda item: item.name.lower())


def escolher_pdf(pdfs: list[Path]) -> Path | None:
	if not pdfs:
		print("Nenhum PDF encontrado na pasta do script.")
		return None

	print("PDFs disponiveis:")
	for indice, pdf in enumerate(pdfs, start=1):
		print(f"{indice}. {pdf.name}")

	escolha = input("\nDigite o numero do PDF que deseja dividir: ").strip()
	if not escolha.isdigit():
		print("Escolha invalida.")
		return None

	indice = int(escolha)
	if indice < 1 or indice > len(pdfs):
		print("Numero fora da lista.")
		return None

	return pdfs[indice - 1]


def dividir_em_duas_paginas(pdf_path: Path, output_dir: Path) -> int:
	reader = PdfReader(str(pdf_path))
	total_paginas = len(reader.pages)
	gerados = 0

	for inicio in range(0, total_paginas, 2):
		fim = min(inicio + 2, total_paginas)
		writer = PdfWriter()

		for pagina in range(inicio, fim):
			writer.add_page(reader.pages[pagina])

		nome_saida = f"{pdf_path.stem}_{inicio + 1:03d}-{fim:03d}.pdf"
		caminho_saida = output_dir / nome_saida

		with caminho_saida.open("wb") as arquivo_saida:
			writer.write(arquivo_saida)

		gerados += 1

	return gerados


def main() -> None:
	base_dir = Path(__file__).resolve().parent
	print(f"Pasta atual: {base_dir}")

	pdfs = listar_pdfs(base_dir)
	pdf_escolhido = escolher_pdf(pdfs)
	if pdf_escolhido is None:
		return

	pasta_saida = base_dir / f"{pdf_escolhido.stem}_dividido"
	pasta_saida.mkdir(exist_ok=True)

	try:
		quantidade = dividir_em_duas_paginas(pdf_escolhido, pasta_saida)
		print(f"Concluido. Foram gerados {quantidade} arquivo(s) em: {pasta_saida}")
	except Exception as erro:
		print(f"Erro ao dividir PDF: {erro}")


if __name__ == "__main__":
	main()
