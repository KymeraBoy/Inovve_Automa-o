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


def dividir_pdf_em_blocos(pdf_path: Path, output_dir: Path, paginas_por_arquivo: int = 2) -> int:
	"""Divide um PDF em arquivos menores com quantidade fixa de páginas.

	Retorna a quantidade de arquivos gerados.
	"""
	reader = PdfReader(str(pdf_path))
	total_paginas = len(reader.pages)
	arquivos_gerados = 0

	for inicio in range(0, total_paginas, paginas_por_arquivo):
		fim = min(inicio + paginas_por_arquivo, total_paginas)
		writer = PdfWriter()

		for indice in range(inicio, fim):
			writer.add_page(reader.pages[indice])

		nome_saida = f"{pdf_path.stem}_{inicio + 1:03d}-{fim:03d}.pdf"
		caminho_saida = output_dir / nome_saida

		with caminho_saida.open("wb") as arquivo_saida:
			writer.write(arquivo_saida)

		arquivos_gerados += 1

	return arquivos_gerados


def main() -> None:
	pasta = input("Digite o endereco da pasta com os PDFs: ").strip().strip('"')
	pasta_path = Path(pasta)

	if not pasta_path.exists() or not pasta_path.is_dir():
		print("Endereco invalido. Informe uma pasta existente.")
		return

	pdfs = sorted(pasta_path.glob("*.pdf"))
	if not pdfs:
		print("Nenhum arquivo PDF encontrado na pasta informada.")
		return

	output_base = pasta_path / "PDFs_Divididos"
	output_base.mkdir(exist_ok=True)

	print(f"PDFs encontrados: {len(pdfs)}")
	total_arquivos_gerados = 0

	for pdf in pdfs:
		pasta_pdf = output_base / pdf.stem
		pasta_pdf.mkdir(exist_ok=True)

		try:
			gerados = dividir_pdf_em_blocos(pdf, pasta_pdf, paginas_por_arquivo=2)
			total_arquivos_gerados += gerados
			print(f"OK: {pdf.name} -> {gerados} arquivo(s) em {pasta_pdf}")
		except Exception as erro:
			print(f"ERRO ao processar {pdf.name}: {erro}")

	print(f"Concluido. Total de arquivos gerados: {total_arquivos_gerados}")


if __name__ == "__main__":
	main()
