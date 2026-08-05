"""Templates de documentos de registro diário."""

from __future__ import annotations

from datetime import date

from constants import SECTION_DASH_BAR, SECTION_DOUBLE_BAR


def build_daily_template(reference_date: date) -> str:
    """Monta o conteúdo base do arquivo diário no formato especificado."""
    dia = reference_date.strftime("%Y-%m-%d")
    return (
        "REGISTRO DO DIA\n"
        f"{dia}\n\n"
        f"{SECTION_DOUBLE_BAR}\n"
        "INFORMAÇÕES\n"
        f"{SECTION_DOUBLE_BAR}\n\n"
        "Área destinada para:\n\n"
        "- observações\n"
        "- respostas\n"
        "- lembretes\n"
        "- correções\n"
        "- comunicados\n"
        "- qualquer anotação geral\n\n"
        f"{SECTION_DOUBLE_BAR}\n"
        "ATIVIDADES\n"
        f"{SECTION_DOUBLE_BAR}\n\n"
        "Nesta área ficarão armazenadas todas as atividades registradas automaticamente.\n\n"
        f"{SECTION_DASH_BAR}\n"
        "NOVA ATIVIDADE\n"
        f"{SECTION_DASH_BAR}\n\n"
    )
