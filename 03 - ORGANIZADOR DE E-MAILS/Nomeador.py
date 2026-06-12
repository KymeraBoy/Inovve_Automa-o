from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


def iter_pdf_files(root_folder: Path) -> Iterable[Path]:
	"""Yield all PDF files recursively from the root folder."""
	return sorted(path for path in root_folder.rglob("*.pdf") if path.is_file())


def extract_text_from_pdf(pdf_path: Path) -> str:
	"""Extract text from every page in a PDF file."""
	reader = PdfReader(str(pdf_path))
	pages_text = []

	for index, page in enumerate(reader.pages, start=1):
		page_text = page.extract_text() or ""
		pages_text.append(f"===== PAGE {index} =====\n{page_text.strip()}\n")

	return "\n".join(pages_text).strip() + "\n"


def normalize_datetime(date_text: str) -> str | None:
	"""Normalize datetimes to YYYY-MM-DD_HH-MM for file naming."""
	patterns = [
		r"\b(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\b",
		r"\b(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})\b",
	]

	for pattern in patterns:
		match = re.search(pattern, date_text)
		if not match:
			continue

		date_part, time_part = match.groups()

		try:
			if "/" in date_part:
				parsed = datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M")
			else:
				parsed = datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M")
			return parsed.strftime("%Y-%m-%d_%H-%M")
		except ValueError:
			continue

	return None


def extract_sent_datetime(extracted_text: str) -> str | None:
	"""Find sent datetime after the first comma near the 'Data' field."""
	lines = extracted_text.splitlines()

	for index, line in enumerate(lines):
		if "Data" not in line:
			continue

		if "," in line:
			after_comma = line.split(",", 1)[1].strip()
			datetime_value = normalize_datetime(after_comma)
			if datetime_value:
				return datetime_value

		if index + 1 < len(lines) and "," in lines[index + 1]:
			after_comma = lines[index + 1].split(",", 1)[1].strip()
			datetime_value = normalize_datetime(after_comma)
			if datetime_value:
				return datetime_value

	return None


def build_unique_target_path(folder: Path, filename: str) -> Path:
	"""Generate a non-conflicting file path in the target folder."""
	target = folder / filename
	if not target.exists():
		return target

	stem = target.stem
	suffix = target.suffix
	counter = 2
	while True:
		candidate = folder / f"{stem}_{counter}{suffix}"
		if not candidate.exists():
			return candidate
		counter += 1


def rename_pdf_with_datetime(pdf_path: Path, datetime_value: str) -> Path:
	"""Rename a PDF using only normalized datetime as filename."""
	new_name = f"{datetime_value}.pdf"
	target_path = build_unique_target_path(pdf_path.parent, new_name)
	if target_path.resolve() == pdf_path.resolve():
		return pdf_path

	pdf_path.rename(target_path)
	return target_path


def rename_pdfs_by_sent_datetime(source_folder: Path) -> None:
	"""Rename each PDF to the sent date and time extracted from its content."""
	if not source_folder.exists() or not source_folder.is_dir():
		raise FileNotFoundError(f"Source folder not found: {source_folder}")

	pdf_files = list(iter_pdf_files(source_folder))

	if not pdf_files:
		print(f"No PDF files found in: {source_folder}")
		return

	rename_count = 0
	datetime_not_found_count = 0
	error_count = 0

	for pdf_file in pdf_files:
		try:
			extracted_text = extract_text_from_pdf(pdf_file)
			sent_datetime = extract_sent_datetime(extracted_text)

			if sent_datetime:
				final_pdf_path = rename_pdf_with_datetime(pdf_file, sent_datetime)
				if final_pdf_path != pdf_file:
					rename_count += 1
					print(f"[OK] {pdf_file.name} -> {final_pdf_path.name}")
				else:
					print(f"[SKIP] {pdf_file.name} already has target name.")
			else:
				datetime_not_found_count += 1
				print(f"[WARN] Datetime not found in {pdf_file.name}; keeping original name.")
		except Exception as exc:
			error_count += 1
			print(f"[ERROR] {pdf_file} | {exc}")

	print("\nFinished processing.")
	print(f"PDF files renamed: {rename_count}")
	print(f"Datetime not found: {datetime_not_found_count}")
	print(f"Errors: {error_count}")


if __name__ == "__main__":
	base_dir = Path(__file__).resolve().parent
	emails_folder = base_dir / "E-mails"

	rename_pdfs_by_sent_datetime(emails_folder)
