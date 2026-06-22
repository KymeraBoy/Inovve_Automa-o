"""Helpers isolados para a automação de geração de anexos e sumário.

Este arquivo não altera o comportamento existente do Documentaiser.py.
A intenção é manter funções puras (detecção/validação/contagem/concatenação/LaTeX) fora da UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, Iterable

from pypdf import PdfReader, PdfWriter


def _norm(s: str) -> str:
    return s.strip()


@dataclass(frozen=True)
class DocRef:
    token: str  # ex: "SOBRAL_PROC" ou "SOBRAL_PUB_ADT_02"
    path: Path


@dataclass(frozen=True)
class AnexoPlan:
    anexo_key: str  # "I" | "II" | "III" ...
    title: str
    pages_start: int
    pages_end: int
    items: list[tuple[str, int, int]]  # (item_label, start, end)


def find_municipios_from_dir(workdir: Path) -> list[str]:
    """Detecta MUNICÍPIO a partir dos PDFs já renomeados: <MUNICIPIO>_CTR.pdf, etc."""
    municipios: set[str] = set()
    for p in workdir.glob("*.pdf"):
        stem = p.stem
        m = re.match(r"^(?P<mun>.+?)_(CTR|PROC|KIT|ADT|RAS|PUB).*$", stem, flags=re.IGNORECASE)
        if m:
            municipios.add(m.group("mun"))
    return sorted(municipios)


def build_expected_filenames(municipio: str) -> dict[str, str]:
    mun = municipio
    return {
        "PROC": f"{mun}_PROC.pdf",
        "KIT": f"{mun}_KIT.pdf",
        "CTR": f"{mun}_CTR.pdf",
        "PUB_CTR": f"{mun}_PUB_CTR.pdf",
        # RAS_CTR opcional
        # ADT/BASED serão tratados a partir de numeração detectada
    }


def parse_adt_numbers(workdir: Path, municipio: str) -> list[int]:
    mun = re.escape(municipio)
    pat = re.compile(rf"^{mun}_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)
    nums: set[int] = set()
    for p in workdir.glob("*.pdf"):
        m = pat.match(p.name)
        if m:
            try:
                nums.add(int(m.group(1)))
            except Exception:
                pass
    return sorted(nums)


def locate_docs_for_municipio(workdir: Path, municipio: str) -> dict[str, Optional[DocRef]]:
    """Retorna referências por token.

    Tokens esperados (por projeto):
    PROC, KIT,
    CTR, RAS_CTR (opcional), PUB_CTR,
    ADT_XX, RAS_ADT_XX (opcional), PUB_ADT_XX
    """
    mun = municipio
    result: dict[str, Optional[DocRef]] = {}

    def _maybe(token: str, filename: str) -> None:
        p = workdir / filename
        result[token] = DocRef(token=token, path=p) if p.exists() else None

    _maybe("PROC", f"{mun}_PROC.pdf")
    _maybe("KIT", f"{mun}_KIT.pdf")
    _maybe("CTR", f"{mun}_CTR.pdf")
    _maybe("RAS_CTR", f"{mun}_RAS_CTR.pdf")
    _maybe("PUB_CTR", f"{mun}_PUB_CTR.pdf")

    adt_nums = parse_adt_numbers(workdir, mun)
    result["ADT_NUMS"] = [n for n in adt_nums]  # type: ignore[assignment]

    for n in adt_nums:
        nn = f"{n:02d}"
        _maybe(f"ADT_{nn}", f"{mun}_ADT_{nn}.pdf")
        _maybe(f"RAS_ADT_{nn}", f"{mun}_RAS_ADT_{nn}.pdf")
        _maybe(f"PUB_ADT_{nn}", f"{mun}_PUB_ADT_{nn}.pdf")

    return result


def concat_pdfs(paths: Iterable[Path], out_path: Path) -> None:
    writer = PdfWriter()
    for p in paths:
        reader = PdfReader(str(p))
        for page in reader.pages:
            writer.add_page(page)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        writer.write(f)


def count_pages(path: Path) -> int:
    reader = PdfReader(str(path))
    return len(reader.pages)


def render_text_preview(municipio: str, empresa: str, adt_nums: list[int], has_ras_proc: bool, has_ras_ctr: bool, adt_has_ras: dict[int, bool]) -> str:
    lines: list[str] = []
    lines.append(f"MUNICÍPIO: {municipio}")
    lines.append(f"EMPRESA: {empresa}")
    lines.append("")
    lines.append("ANEXO I")
    lines.append("* Procuração")
    if has_ras_proc:
        lines.append("* Relatório de Assinaturas da Procuração")
    lines.append("* Kit Prefeito")
    lines.append(f"* Contrato Social {empresa}")
    lines.append(f"* Documento do Representante {empresa}")
    lines.append("")
    lines.append("ANEXO II")
    lines.append("* Contrato")
    if has_ras_ctr:
        lines.append("* Relatório de Assinaturas do Contrato")
    lines.append("* Publicação do Contrato")
    for i, n in enumerate(adt_nums):
        annex_no = 3 + i
        lines.append("")
        lines.append(f"ANEXO {annex_no:02d}")
        lines.append(f"* Aditivo {n:02d}")
        if adt_has_ras.get(n, False):
            lines.append(f"* Relatório de Assinaturas do Aditivo {n:02d}")
        lines.append(f"* Publicação do Aditivo {n:02d}")

    return "\n".join(lines)

