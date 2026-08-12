"""Geração de anexos e sumário (mix-in)."""

from __future__ import annotations

import os
import re
import subprocess
import tkinter as tk

from pathlib import Path
from tkinter import messagebox

from automacao_documentaiser_helpers import find_municipios_from_dir
from automacao_documentaiser_helpers import locate_docs_for_municipio
from automacao_documentaiser_helpers import render_text_preview


class GeracaoAnexosSumarioMixin:
    def _auto_get_empresa_assets(self, empresa: str) -> dict[str, str]:
        base = Path(__file__).resolve().parent
        empresa_dir = base / "empresas" / empresa
        return {
            "CONTRATO_SOCIAL": str(empresa_dir / f"Contrato social da empresa {empresa}.pdf"),
            "REPRESENTANTE": str(empresa_dir / "Documento de identificação do representante.pdf"),
        }

    def _auto_validate_and_prepare(self) -> tuple[list[str], str, list[int], dict[int, bool], bool, bool]:
        workdir = Path(self.selected_path.get())
        if self.selected_path.get() == "Nenhuma pasta selecionada" or not workdir.exists():
            raise ValueError("Selecione um diretório de trabalho")

        empresa = self.auto_selected_empresa.get().strip().upper()
        municipios = find_municipios_from_dir(workdir)
        if not municipios:
            raise ValueError("Não foi possível detectar MUNICÍPIOs a partir dos PDFs.")
        if len(municipios) != 1:
            raise ValueError(
                f"Detectados múltiplos MUNICÍPIOs ({len(municipios)}). "
                f"Processamento em lote ainda não implementado: {municipios[:5]}"
            )

        municipio = municipios[0]
        docs = locate_docs_for_municipio(workdir, municipio)

        has_ras_proc = docs.get("RAS_PROC") is not None
        has_ras_ctr = docs.get("RAS_CTR") is not None

        adt_nums = docs.get("ADT_NUMS") or []
        adt_has_ras: dict[int, bool] = {}
        for n in adt_nums:
            adt_has_ras[n] = docs.get(f"RAS_ADT_{n:02d}") is not None

        required_tokens = ["PROC", "KIT", "CTR", "PUB_CTR"]
        missing = [t for t in required_tokens if docs.get(t) is None]
        if missing:
            expected = {
                "PROC": f"{municipio}_PROC.pdf",
                "KIT": f"{municipio}_KIT.pdf",
                "CTR": f"{municipio}_CTR.pdf",
                "PUB_CTR": f"{municipio}_PUB_CTR.pdf",
            }
            raise ValueError(f"Documento obrigatório não encontrado: {expected[missing[0]]}")

        for n in adt_nums:
            if docs.get(f"ADT_{n:02d}") is None:
                raise ValueError(f"Documento {municipio}_ADT_{n:02d}.pdf não encontrado.")
            if docs.get(f"PUB_ADT_{n:02d}") is None:
                raise ValueError(f"Documento {municipio}_PUB_ADT_{n:02d}.pdf não encontrado.")

        empresa_assets = self._auto_get_empresa_assets(empresa)
        contrato_path = Path(empresa_assets["CONTRATO_SOCIAL"])
        rep_path = Path(empresa_assets["REPRESENTANTE"])
        if not contrato_path.exists():
            raise ValueError(f"Contrato social não encontrado: {contrato_path}")
        if not rep_path.exists():
            raise ValueError(f"Documento do representante não encontrado: {rep_path}")

        return municipios, municipio, adt_nums, adt_has_ras, has_ras_proc, has_ras_ctr

    def _auto_validate_documents(self) -> None:
        try:
            self._auto_validate_and_prepare()
            messagebox.showinfo("Validação", "Documentos obrigatórios encontrados. Tudo ok.")
        except Exception as e:
            messagebox.showerror("Erro na validação", str(e))

    def _auto_visualize_structure(self) -> None:
        try:
            _, municipio, adt_nums, adt_has_ras, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
            empresa = self.auto_selected_empresa.get().strip().upper()
            preview = render_text_preview(
                municipio=municipio,
                empresa=empresa,
                adt_nums=adt_nums,
                has_ras_proc=has_ras_proc,
                has_ras_ctr=has_ras_ctr,
                adt_has_ras=adt_has_ras,
            )
            self._auto_show_preview(preview)
        except Exception as e:
            messagebox.showerror("Erro na visualização", str(e))

    def _auto_show_preview(self, text: str) -> None:
        if getattr(self, "auto_preview_text_widget", None) is None:
            return
        self.auto_preview_text_widget.config(state=tk.NORMAL)
        self.auto_preview_text_widget.delete("1.0", tk.END)
        self.auto_preview_text_widget.insert(tk.END, text)
        self.auto_preview_text_widget.config(state=tk.DISABLED)

    def _auto_generate_anexos(self, raise_on_error: bool = False) -> tuple[list[int], list[int], list[list[int]]]:
        try:
            from pypdf import PdfReader, PdfWriter

            workdir = Path(self.selected_path.get())
            _, municipio, adt_nums, _, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
            empresa = self.auto_selected_empresa.get().strip().upper()

            docs = locate_docs_for_municipio(workdir, municipio)
            assets = self._auto_get_empresa_assets(empresa)
            contrato_path = Path(assets["CONTRATO_SOCIAL"])
            rep_path = Path(assets["REPRESENTANTE"])

            out_dir = workdir / "documentaiser_export"
            out_dir.mkdir(parents=True, exist_ok=True)

            anexo1_pages: list[int] = []
            anexo2_pages: list[int] = []
            aditivos_pages: list[list[int]] = []

            def _build_anexo_filename(annex_roman: str, suffix: str) -> str:
                return f"{municipio.replace('_', ' ')} - ANEXO {annex_roman} - {suffix}.pdf"

            def _roman(n: int) -> str:
                romans = [
                    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
                ]
                val = n
                out = []
                for r_val, r_sym in romans:
                    while val >= r_val:
                        out.append(r_sym)
                        val -= r_val
                return "".join(out)

            annex1_parts: list[Path] = [Path(docs["PROC"].path)]
            if has_ras_proc and docs.get("RAS_PROC") is not None:
                annex1_parts.append(Path(docs["RAS_PROC"].path))
            annex1_parts.append(Path(docs["KIT"].path))
            annex1_parts.append(contrato_path)
            annex1_parts.append(rep_path)

            anexo1_path = out_dir / _build_anexo_filename("I", "INSTRUMENTOS PROCURATÓRIOS")
            writer = PdfWriter()
            for p in annex1_parts:
                reader = PdfReader(str(p))
                anexo1_pages.append(len(reader.pages))
                for page in reader.pages:
                    writer.add_page(page)
            with open(anexo1_path, "wb") as f:
                writer.write(f)

            annex2_parts: list[Path] = [Path(docs["CTR"].path)]
            if has_ras_ctr:
                annex2_parts.append(Path(docs["RAS_CTR"].path))
            annex2_parts.append(Path(docs["PUB_CTR"].path))

            anexo2_path = out_dir / _build_anexo_filename("II", "DOCUMENTOS CONTRATUAIS")
            writer = PdfWriter()
            for p in annex2_parts:
                reader = PdfReader(str(p))
                anexo2_pages.append(len(reader.pages))
                for page in reader.pages:
                    writer.add_page(page)
            with open(anexo2_path, "wb") as f:
                writer.write(f)

            for idx, n in enumerate(adt_nums, start=3):
                tok_adt = f"ADT_{n:02d}"
                tok_ras = f"RAS_ADT_{n:02d}"
                tok_pub = f"PUB_ADT_{n:02d}"

                parts: list[Path] = [Path(docs[tok_adt].path)]
                if docs.get(tok_ras) is not None:
                    parts.append(Path(docs[tok_ras].path))
                parts.append(Path(docs[tok_pub].path))

                anexo_path = out_dir / _build_anexo_filename(_roman(idx), f"TERMO ADITIVO {n}")
                writer = PdfWriter()
                current_adt_pages: list[int] = []
                for p in parts:
                    reader = PdfReader(str(p))
                    current_adt_pages.append(len(reader.pages))
                    for page in reader.pages:
                        writer.add_page(page)
                aditivos_pages.append(current_adt_pages)
                with open(anexo_path, "wb") as f:
                    writer.write(f)

            messagebox.showinfo("Anexos", "Anexos gerados com sucesso.")
            return anexo1_pages, anexo2_pages, aditivos_pages
        except Exception as e:
            messagebox.showerror("Erro ao gerar anexos", str(e))
            if raise_on_error:
                raise
            return [], [], []

    def _compress_pdf_in_place(self, pdf_path: Path) -> None:
        pdf_absoluto = pdf_path.resolve()
        tmp_out = pdf_absoluto.with_suffix(".compressed.pdf")
        executaveis_gs = ["gswin64c", "gs", "gswin32c"]
        sucesso = False

        for exe in executaveis_gs:
            try:
                cmd = [
                    exe,
                    "-sDEVICE=pdfwrite",
                    "-dCompatibilityLevel=1.4",
                    "-dPDFSETTINGS=/screen",
                    "-dColorImageDownsampleType=/Average",
                    "-dColorImageResolution=72",
                    "-dGrayImageDownsampleType=/Average",
                    "-dGrayImageResolution=72",
                    "-dMonoImageDownsampleType=/Average",
                    "-dMonoImageResolution=72",
                    "-dNOPAUSE",
                    "-dQUIET",
                    "-dBATCH",
                    f"-sOutputFile={os.fspath(tmp_out)}",
                    os.fspath(pdf_absoluto),
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=False)
                if tmp_out.exists() and tmp_out.stat().st_size > 0:
                    sucesso = True
                    break
            except FileNotFoundError:
                continue
            except Exception:
                break

        if sucesso and tmp_out.exists():
            try:
                if tmp_out.stat().st_size < pdf_absoluto.stat().st_size:
                    pdf_absoluto.unlink()
                    tmp_out.rename(pdf_absoluto)
                else:
                    tmp_out.unlink()
            except Exception:
                if tmp_out.exists():
                    tmp_out.unlink()

    def _auto_generate_sumario(
        self,
        anexo1_pages: list[int] | None = None,
        anexo2_pages: list[int] | None = None,
        aditivos_pages: list[list[int]] | None = None,
    ) -> None:
        try:
            if anexo1_pages is None or anexo2_pages is None or aditivos_pages is None:
                anexo1_pages, anexo2_pages, aditivos_pages = self._auto_generate_anexos(raise_on_error=True)

            workdir = Path(self.selected_path.get())
            _, municipio, adt_nums, _, _, _ = self._auto_validate_and_prepare()
            empresa = self.auto_selected_empresa.get().strip().upper()
            export_dir = workdir / "documentaiser_export"

            def _build_anexo_path(annex_roman: str, suffix: str) -> Path:
                return export_dir / f"{municipio.replace('_', ' ')} - ANEXO {annex_roman} - {suffix}.pdf"

            def _roman(n: int) -> str:
                romans = [
                    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
                ]
                val, out = n, []
                for r_val, r_sym in romans:
                    while val >= r_val:
                        out.append(r_sym)
                        val -= r_val
                return "".join(out)

            anexos_paths = [
                _build_anexo_path("I", "INSTRUMENTOS PROCURATÓRIOS"),
                _build_anexo_path("II", "DOCUMENTOS CONTRATUAIS"),
            ]
            for idx, n in enumerate(adt_nums, start=3):
                anexos_paths.append(_build_anexo_path(_roman(idx), f"TERMO ADITIVO {n}"))
            if not all(p.exists() for p in anexos_paths):
                raise ValueError("Gere os anexos antes de gerar o sumário.")

            if len(anexo1_pages) not in [4, 5]:
                raise ValueError(f"Quantidade de documentos do anexo I inválida ({len(anexo1_pages)} itens).")

            p_proc = 1
            if len(anexo1_pages) == 5:
                p_rel = p_proc + anexo1_pages[0]
                p_kit = p_rel + anexo1_pages[1]
                p_cont = p_kit + anexo1_pages[2]
                p_rep = p_cont + anexo1_pages[3]
                rel_ass = fr"    \item Validação das assinaturas \dotfill {p_rel}"
            else:
                p_kit = p_proc + anexo1_pages[0]
                p_cont = p_kit + anexo1_pages[1]
                p_rep = p_cont + anexo1_pages[2]
                rel_ass = ""

            anexo_i = fr"""\textbf{{Anexo I -- Instrumentos procuratórios \dotfill 1}}
\begin{{enumerate}}
    \item Procuração \dotfill {p_proc}
    {f'{rel_ass}\n' if rel_ass else ''}    \item Kit prefeito \dotfill {p_kit}
    \item Contrato Social da Empresa \dotfill {p_cont}
    \item Documento de Identificação do Representante \dotfill {p_rep}
\end{{enumerate}}"""

            if len(anexo2_pages) not in [2, 3]:
                raise ValueError(f"Quantidade de documentos do anexo II inválida ({len(anexo2_pages)} itens).")

            p_ctr = 1
            if len(anexo2_pages) == 3:
                p_ras_ctr = p_ctr + anexo2_pages[0]
                p_pub_ctr = p_ras_ctr + anexo2_pages[1]
                rel_ctr = fr"    \item Validação das assinaturas do Contrato \dotfill {p_ras_ctr}"
            else:
                p_pub_ctr = p_ctr + anexo2_pages[0]
                rel_ctr = ""

            anexo_ii = fr"""\textbf{{Anexo II -- Documentos Contratuais \dotfill 1}}
\begin{{enumerate}}
    \item Contrato \dotfill {p_ctr}
    {f'{rel_ctr}\n' if rel_ctr else ''}    \item Publicação do Contrato em Diário Oficial \dotfill {p_pub_ctr}
\end{{enumerate}}"""

            bloco_aditivos_latex = []
            for idx, n in enumerate(adt_nums, start=3):
                current_adt = aditivos_pages[idx - 3]
                annex_roman = _roman(idx)

                p_adt_termo = 1
                if len(current_adt) == 3:
                    p_adt_ras = p_adt_termo + current_adt[0]
                    p_adt_pub = p_adt_ras + current_adt[1]
                    rel_adt = f"    \\item Validação das assinaturas do {n}º Aditivo \\dotfill {p_adt_ras}\n"
                else:
                    p_adt_pub = p_adt_termo + current_adt[0]
                    rel_adt = ""

                item_aditivo = (
                    f"\\textbf{{Anexo {annex_roman} -- {n}º Termo Aditivo \\dotfill 1}}\n"
                    f"\\begin{{enumerate}}\n"
                    f"    \\item {n}º Termo Aditivo \\dotfill {p_adt_termo}\n"
                    f"{rel_adt}"
                    f"    \\item Publicação do {n}º Aditivo em Diário Oficial \\dotfill {p_adt_pub}\n"
                    f"\\end{{enumerate}}\n\n"
                )
                bloco_aditivos_latex.append(item_aditivo)

            tex_base = Path(__file__).resolve().parent / "Sumario.tex"
            tex_content = tex_base.read_text(encoding="utf-8")

            header_pngs = ["HLA_Header.png", "Ruda_Header.png", "ABEL_Header.png"]
            for png_name in header_pngs:
                src_png = Path(__file__).resolve().parent / png_name
                if src_png.exists():
                    dst_png = export_dir / png_name
                    if not dst_png.exists():
                        dst_png.write_bytes(src_png.read_bytes())

            tex_content = re.sub(r"<<EMPRESA>>", empresa, tex_content)
            municipio_formatado = municipio.replace("_", " ")
            tex_content = tex_content.replace("<<MUNICIPIO>>", municipio_formatado)
            tex_content = re.sub(r"<<ANEXO I>>", lambda _m: anexo_i, tex_content)
            tex_content = re.sub(r"<<ANEXO II>>", lambda _m: anexo_ii, tex_content)
            tex_content = re.sub(r"<<ADITIVOS>>", lambda _m: "".join(bloco_aditivos_latex), tex_content)

            tex_filename = f"{municipio} - SUMÁRIO.tex"
            out_tex = export_dir / tex_filename
            out_tex.write_text(tex_content, encoding="utf-8")

            cmd = ["xelatex", "-interaction=nonstopmode", tex_filename]
            proc = subprocess.run(cmd, cwd=str(export_dir), capture_output=True, text=True, errors="replace")
            if proc.returncode != 0:
                raise RuntimeError("Falha ao compilar SUMARIO.pdf via xelatex.\n" + proc.stdout + proc.stderr)

            try:
                for f in export_dir.iterdir():
                    if f.is_file() and f.suffix.lower() != ".pdf":
                        f.unlink()
            except Exception:
                pass

            desired_pdf = export_dir / f"{municipio} - SUMÁRIO.pdf"
            messagebox.showinfo("Sumário", f"{desired_pdf.name} gerado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro ao gerar sumário", str(e))

    def _auto_generate_all(self) -> None:
        try:
            self._auto_validate_and_prepare()
            self._auto_visualize_structure()
            anexo1_pages, anexo2_pages, aditivos_pages = self._auto_generate_anexos(raise_on_error=True)
            self._auto_generate_sumario(anexo1_pages, anexo2_pages, aditivos_pages)
        except Exception as e:
            messagebox.showerror("Erro ao gerar tudo", str(e))