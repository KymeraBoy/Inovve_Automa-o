"""Processamento de texto de atividade e formatação para histórico."""

from __future__ import annotations

from constants import SECTION_DASH_BAR


def normalize_activity_text(text: str) -> str:
    """Normaliza quebras de linha e remove bordas vazias da atividade."""
    cleaned = text.replace("\r\n", "\n").strip()
    lines = [line.rstrip() for line in cleaned.split("\n")]
    return "\n".join(lines).strip()


def build_activity_block(timestamp_hhmm: str, activity_text: str) -> list[str]:
    """Monta bloco canônico de atividade com horário e separador."""
    text = normalize_activity_text(activity_text)
    block = [timestamp_hhmm, "", text, "", SECTION_DASH_BAR, ""]
    return block
