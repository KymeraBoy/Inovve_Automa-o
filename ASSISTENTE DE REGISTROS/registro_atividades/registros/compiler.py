"""Compilação de registros diários em arquivo consolidado."""

from __future__ import annotations

from pathlib import Path


def _record_sort_key(path: Path) -> str:
    return path.stem.replace("Registro-", "")


def compile_month_records(month_dir: Path) -> Path | None:
    """Consolida arquivos Registro-AAAA-MM-DD.txt do mês em um único TXT."""
    records = sorted(month_dir.glob("Registro-*.txt"), key=_record_sort_key)
    if not records:
        return None

    month_tag = month_dir.parent.name + "-" + month_dir.name
    output = month_dir / f"Consolidado-{month_tag}.txt"

    chunks: list[str] = []
    for item in records:
        body = item.read_text(encoding="utf-8").strip()
        chunks.append(f"{'=' * 72}\nARQUIVO: {item.name}\n{'=' * 72}\n{body}\n")

    output.write_text("\n".join(chunks).strip() + "\n", encoding="utf-8")
    return output
