from __future__ import annotations

import os
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def get_base_dir() -> Path:
	"""
	Retorna o diretório base da aplicação.
	Em modo PyInstaller, aponta para o diretório do executável.
	Caso contrário, aponta para o diretório do script.
	"""
	if getattr(sys, "frozen", False):
		return Path(sys.executable).resolve().parent
	return Path(__file__).resolve().parent


INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def strip_accents(text: str) -> str:
	"""Remove acentos de uma string."""
	normalized = unicodedata.normalize("NFKD", text)
	return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_string_for_filename(text: str) -> str:
	"""Normaliza uma string para ser usada como nome de arquivo."""
	text = strip_accents(text)
	text = text.upper().strip()
	text = re.sub(r"\s+", "_", text)
	text = INVALID_FILENAME_CHARS.sub("-", text)
	text = re.sub(r"[^A-Z0-9_\-]", "", text)
	return text.strip("_-")


def normalize_string_for_token(value: str) -> str:
	"""Normaliza uma string para ser usada como token (sem espaços, apenas _)."""
	text = strip_accents(str(value).strip().upper())
	text = re.sub(r"[^A-Z0-9_-]+", "_", text)
	text = re.sub(r"_+", "_", text)
	return text.strip("_")


def normalize_string_for_display(value: str) -> str:
	"""Normaliza uma string para exibição (sem acentos, apenas espaços)."""
	text = strip_accents(str(value).strip().upper())
	text = re.sub(r"[^A-Z0-9\- ]+", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def clean_cell(value: object) -> str:
	"""Limpa o valor de uma célula, removendo quebras de linha e espaços extras."""
	if value is None:
		return ""
	return str(value).replace("\n", " ").strip()


def render_progress(current: int, total: int, prefix: str = "Progresso") -> None:
	"""Renderiza uma barra de progresso no console."""
	if total <= 0:
		return

	bar_width = 30
	ratio = current / total
	filled = int(bar_width * ratio)
	bar = "#" * filled + "-" * (bar_width - filled)
	percent = ratio * 100
	message = f"\r{prefix}: [{bar}] {current}/{total} ({percent:5.1f}%)"
	sys.stdout.write(message)
	sys.stdout.flush()

	if current >= total:
		sys.stdout.write("\n")


def build_unique_path(target_path: Path) -> Path:
	"""Gera um nome de arquivo único para evitar sobrescrever arquivos existentes."""
	if not target_path.exists():
		return target_path

	stem = target_path.stem
	suffix = target_path.suffix
	counter = 2
	while True:
		candidate = target_path.with_name(f"{stem}_{counter}{suffix}")
		if not candidate.exists():
			return candidate
		counter += 1


def load_pdf_backend():
	"""Carrega a biblioteca PDF (pypdf ou PyPDF2) dinamicamente."""
	try:
		from pypdf import PdfReader, PdfWriter  # pyright: ignore[reportMissingImports]
		return PdfReader, PdfWriter
	except ImportError:
		try:
			from PyPDF2 import PdfReader, PdfWriter  # pyright: ignore[reportMissingImports]
			return PdfReader, PdfWriter
		except ImportError as exc:
			raise SystemExit("Dependencia ausente: pypdf/PyPDF2. Instale com: pip install pypdf") from exc


def roman_numeral(number: int) -> str:
	"""Converte um número inteiro para numeral romano."""
	values = [
		(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
		(50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
	]
	result = []
	for value, symbol in values:
		while number >= value:
			result.append(symbol)
			number -= value
	return "".join(result)


def ordinal_word(number: int) -> str:
	"""Converte um número inteiro para sua representação ordinal por extenso (em português)."""
	words = {
		1: "PRIMEIRO", 2: "SEGUNDO", 3: "TERCEIRO", 4: "QUARTO", 5: "QUINTO",
		6: "SEXTO", 7: "SETIMO", 8: "OITAVO", 9: "NONO", 10: "DECIMO",
		11: "DECIMO PRIMEIRO", 12: "DECIMO SEGUNDO", 13: "DECIMO TERCEIRO",
		14: "DECIMO QUARTO", 15: "DECIMO QUINTO",
	}
	return words.get(number, f"{number}O")


def format_page(number: int) -> str:
	"""Formata um número de página com dois dígitos."""
	return f"{number:02d}"


def format_bytes(size: int) -> str:
	"""Formata um tamanho de arquivo em bytes para uma string legível (KB, MB, GB)."""
	units = ["B", "KB", "MB", "GB"]
	value = float(max(0, size))
	for unit in units:
		if value < 1024 or unit == units[-1]:
			if unit == "B":
				return f"{int(value)} {unit}"
			return f"{value:.2f} {unit}"
		value /= 1024
	return f"{value:.2f} GB"


def latex_escape(value: str) -> str:
	"""Escapa caracteres especiais para uso em LaTeX."""
	text = str(value)
	replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
					"_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
	for original, replacement in replacements.items():
		text = text.replace(original, replacement)
	return text


# Mapeamento de meses por extenso para número e abreviação
MONTH_MAPPINGS = {
	"janeiro": {"num": 1, "abbr": "JAN"},
	"fevereiro": {"num": 2, "abbr": "FEV"},
	"março": {"num": 3, "abbr": "MAR"},
	"marco": {"num": 3, "abbr": "MAR"}, # Para lidar com grafias sem cedilha
	"abril": {"num": 4, "abbr": "ABR"},
	"maio": {"num": 5, "abbr": "MAI"},
	"junho": {"num": 6, "abbr": "JUN"},
	"julho": {"num": 7, "abbr": "JUL"},
	"agosto": {"num": 8, "abbr": "AGO"},
	"setembro": {"num": 9, "abbr": "SET"},
	"outubro": {"num": 10, "abbr": "OUT"},
	"novembro": {"num": 11, "abbr": "NOV"},
	"dezembro": {"num": 12, "abbr": "DEZ"},
}

NUM_TO_MONTH_ABBR = {
	1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
	7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
}

MONTH_ABBR_TO_NUM = {v: k for k, v in NUM_TO_MONTH_ABBR.items()}


COMMON_SUBFOLDERS = [
	"ANEEL",
	"DOCUMENTOS_RECEBIDOS",
	"PAGAMENTO",
	"E-MAILS",
	"RECLAMACAO_FORMAL",
]