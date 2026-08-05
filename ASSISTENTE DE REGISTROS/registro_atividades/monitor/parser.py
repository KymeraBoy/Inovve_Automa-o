"""Parser do documento de registro para localizar seções monitoradas."""

from __future__ import annotations

from dataclasses import dataclass

from constants import SECTION_ATIVIDADES, SECTION_DASH_BAR, SECTION_NOVA_ATIVIDADE


@dataclass(slots=True)
class ParsedSections:
    """Limites de seções relevantes no documento."""

    lines: list[str]
    activities_insert_line: int
    new_activity_start_line: int


def _find_line(lines: list[str], value: str) -> int:
    for idx, line in enumerate(lines):
        if line.strip() == value:
            return idx
    return -1


def parse_sections(content: str) -> ParsedSections:
    """Retorna posições de inserção em ATIVIDADES e início de NOVA ATIVIDADE."""
    lines = content.splitlines()

    idx_atividades = _find_line(lines, SECTION_ATIVIDADES)
    idx_nova = _find_line(lines, SECTION_NOVA_ATIVIDADE)

    if idx_atividades < 0 or idx_nova < 0 or idx_nova <= idx_atividades:
        raise ValueError("Estrutura do documento inválida: seções não encontradas.")

    # Busca separador imediatamente antes de NOVA ATIVIDADE para manter layout.
    insert_line = idx_nova
    if idx_nova > 0 and lines[idx_nova - 1].strip() == SECTION_DASH_BAR:
        insert_line = idx_nova - 1

    # Conteúdo útil de NOVA ATIVIDADE começa após o separador inferior.
    start_line = idx_nova + 1
    if start_line < len(lines) and lines[start_line].strip() == SECTION_DASH_BAR:
        start_line += 1

    return ParsedSections(
        lines=lines,
        activities_insert_line=insert_line,
        new_activity_start_line=start_line,
    )


def get_new_activity_buffer(parsed: ParsedSections) -> str:
    """Extrai o texto bruto da caixa NOVA ATIVIDADE."""
    if parsed.new_activity_start_line >= len(parsed.lines):
        return ""
    raw = "\n".join(parsed.lines[parsed.new_activity_start_line :])
    return raw.strip()
