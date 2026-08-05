"""Operações de arquivo com foco em preservação de conteúdo textual."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib


@dataclass(slots=True)
class TextFileSnapshot:
    """Representa o conteúdo de um arquivo de texto e seu estilo de quebra de linha."""

    content: str
    newline: str


def detect_newline(content: str) -> str:
    """Detecta o estilo de newline predominante em um texto."""
    if "\r\n" in content:
        return "\r\n"
    return "\n"


def read_text_snapshot(path: Path) -> TextFileSnapshot:
    """Lê arquivo UTF-8 preservando o estilo de quebra de linha."""
    text = path.read_text(encoding="utf-8")
    return TextFileSnapshot(content=text, newline=detect_newline(text))


def write_text_if_changed(path: Path, new_content: str, newline: str = "\n") -> bool:
    """Escreve o arquivo somente se o conteúdo tiver mudado."""
    old_content = path.read_text(encoding="utf-8") if path.exists() else ""
    if old_content == new_content:
        return False

    normalized = new_content.replace("\r\n", "\n")
    if newline == "\r\n":
        normalized = normalized.replace("\n", "\r\n")

    path.write_text(normalized, encoding="utf-8", newline="")
    return True


def sha256_text(value: str) -> str:
    """Retorna hash SHA-256 de um texto UTF-8."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
