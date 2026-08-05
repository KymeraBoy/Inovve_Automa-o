"""Aplicação de alterações no documento de registro."""

from __future__ import annotations

from dataclasses import dataclass

from monitor.activity_processor import build_activity_block
from monitor.parser import get_new_activity_buffer, parse_sections


@dataclass(slots=True)
class ProcessResult:
    """Resultado da tentativa de processar o buffer de nova atividade."""

    changed: bool
    new_content: str
    captured_activity: str


def process_document_content(content: str, timestamp_hhmm: str) -> ProcessResult:
    """Move texto de NOVA ATIVIDADE para ATIVIDADES com marcação HH:MM."""
    parsed = parse_sections(content)
    pending = get_new_activity_buffer(parsed)
    if not pending:
        return ProcessResult(changed=False, new_content=content, captured_activity="")

    lines = parsed.lines.copy()
    insert_line = parsed.activities_insert_line

    activity_block = build_activity_block(timestamp_hhmm, pending)
    lines[insert_line:insert_line] = activity_block

    start = parsed.new_activity_start_line + len(activity_block)
    del lines[start:]

    new_content = "\n".join(lines)
    if not new_content.endswith("\n"):
        new_content += "\n"

    return ProcessResult(changed=True, new_content=new_content, captured_activity=pending)
