"""Geração de anexos e sumário (mix-in).

Este módulo extrai os métodos de automação anexos/sumário do antigo
`Documentaiser.py` para um mixin.

Ele assume que a classe que o herda implementa/possui os atributos de UI:

- selected_path
- auto_selected_empresa
- auto_preview_text_widget

E os métodos/atributos usados internamente (widgets para preview e UI):
- _auto_show_preview
- (e usa `messagebox` e `subprocess`)

Dependências externas:
- automacao_documentaiser_helpers
- utils.py (não é necessário aqui)

Este mixin é "comportamental" (chama PdfReader/PdfWriter e pdflatex).
"""

from __future__ import annotations
import os
import subprocess
from pathlib import Path
from pathlib import Path
from typing import Optional
import re
import subprocess

import tkinter as tk
from tkinter import messagebox

# automacao_documentaiser_helpers fica no mesmo diretório dos mixins
import sys
UTILS_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(__file__).resolve().parent
if str(UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(UTILS_DIR))
if str(DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_DIR))

from automacao_documentaiser_helpers import (
    find_municipios_from_dir,
    locate_docs_for_municipio,
    count_pages,
    render_text_preview,
)


from automacao_documentaiser_helpers import parse_adt_numbers  # mantém compat (pode ser usado em futuras refatorações)


class GeracaoAnexosSumarioMixin:
    def _auto_get_empresa_assets(self, empresa: str) -> dict[str, str]:
        base = Path(__file__).resolve().parent
        empresa_dir = base / empresa
        return {
            "CONTRATO_SOCIAL": str(empresa_dir / f"Contrato social da empresa {empresa}.pdf"),
            "REPRESENTANTE": str(empresa_dir / "Documento de identificação do representante.pdf"),
        }

    def _auto_validate_and_prepare(self) -> tuple[list[str], str, list[int], dict[int, bool], bool, bool]:
        workdir = Path(self.selected_path.get())
        if self.selected_path.get() == "Nenhuma pasta selecionada" or not workdir.exists():
            raise ValueError("Selecione um diretório de trabalho")

        empresa = self.auto_selected_empresa.get().strip().upper()
        mun_list = find_municipios_from_dir(workdir)
        if not mun_list:
            raise ValueError(
                "Não foi possível detectar MUNICÍPIOs a partir dos arquivos PDF (nomenclatura <MUNICIPIO>_CTR.pdf, etc.)."
            )

        municipios = mun_list
        if len(municipios) != 1:
            raise ValueError(
                f"Detectados múltiplos MUNICÍPIOs ({len(municipios)}). Ajuste para processamento em lote ainda não implementado: {municipios[:5]}"
            )

        municipio = municipios[0]
        docs = locate_docs_for_municipio(workdir, municipio)

        # Token de procuração conforme helper/arquivo real: MUNICIPIO_RAS_PROC.pdf
        has_ras_proc = docs.get("RAS_PROC") is not None or docs.get("RAS_PROC_01") is not None


        has_ras_ctr = docs.get("RAS_CTR") is not None

        # Aditivos são opcionais: ANEXOS III+ só existem se houver PDFs *_ADT_XX.pdf
        adt_nums = docs.get("ADT_NUMS") or []

        adt_has_ras: dict[int, bool] = {}
        for n in adt_nums:
            token = f"RAS_ADT_{n:02d}"
            adt_has_ras[n] = docs.get(token) is not None


        required_tokens = ["PROC", "KIT", "CTR", "PUB_CTR"]
        missing = [t for t in required_tokens if docs.get(t) is None]
        if missing:
            for t in missing:
                expected = {
                    "PROC": f"{municipio}_PROC.pdf",
                    "KIT": f"{municipio}_KIT.pdf",
                    "CTR": f"{municipio}_CTR.pdf",
                    "PUB_CTR": f"{municipio}_PUB_CTR.pdf",
                }[t]
                raise ValueError(f"Documento {expected} não encontrado.")

        for n in adt_nums:
            adt_tok = f"ADT_{n:02d}"
            pub_tok = f"PUB_ADT_{n:02d}"
            if docs.get(adt_tok) is None:
                raise ValueError(f"Documento {municipio}_ADT_{n:02d}.pdf não encontrado.")
            if docs.get(pub_tok) is None:
                raise ValueError(f"Documento {municipio}_PUB_ADT_{n:02d}.pdf não encontrado.")

        empresa_assets = self._auto_get_empresa_assets(empresa)
        contrato_path = Path(empresa_assets["CONTRATO_SOCIAL"])
        rep_path = Path(empresa_assets["REPRESENTANTE"])
        if not contrato_path.exists():
            raise ValueError(f"Documento de Contrato Social da empresa não encontrado: {contrato_path}")
        if not rep_path.exists():
            raise ValueError(f"Documento do Representante da empresa não encontrado: {rep_path}")

        return municipios, municipio, adt_nums, adt_has_ras, has_ras_proc, has_ras_ctr

    def _auto_validate_documents(self) -> None:
        _ = self._auto_validate_and_prepare()
        messagebox.showinfo("Validação", "Documentos obrigatórios encontrados. Tudo ok.")

    def _auto_visualize_structure(self) -> None:
        municipios, municipio, adt_nums, adt_has_ras, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
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

    def _auto_show_preview(self, text: str) -> None:
        if getattr(self, "auto_preview_text_widget", None) is None:
            return
        self.auto_preview_text_widget.config(state=tk.NORMAL)
        self.auto_preview_text_widget.delete("1.0", tk.END)
        self.auto_preview_text_widget.insert(tk.END, text)
        self.auto_preview_text_widget.config(state=tk.DISABLED)

    def _auto_generate_anexos(self) -> None:
        from pypdf import PdfReader, PdfWriter

        workdir = Path(self.selected_path.get())
        _, municipio, adt_nums, _adt_has_ras, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
        empresa = self.auto_selected_empresa.get().strip().upper()

        docs = locate_docs_for_municipio(workdir, municipio)
        assets = self._auto_get_empresa_assets(empresa)
        contrato_path = Path(assets["CONTRATO_SOCIAL"])
        rep_path = Path(assets["REPRESENTANTE"])

        out_dir = workdir / "documentaiser_export"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Formato solicitado:
        # - 1º anexo (I): INSTRUMENTOS PROCURATÓRIOS
        # - 2º anexo (II): DOCUMENTOS CONTRATUAIS
        # - 3º em diante (III, IV...): TERMO ADITIVO <num do aditivo> (conforme ADT)
        def _build_anexo_filename(municipio_token: str, annex_roman: str, suffix: str) -> str:
            return f"{municipio.replace('_', r' ')} - ANEXO {annex_roman} - {suffix}.pdf"

        def _roman(n: int) -> str:
            # n >= 1
            romans = [
                (1000, "M"),
                (900, "CM"),
                (500, "D"),
                (400, "CD"),
                (100, "C"),
                (90, "XC"),
                (50, "L"),
                (40, "XL"),
                (10, "X"),
                (9, "IX"),
                (5, "V"),
                (4, "IV"),
                (1, "I"),
            ]
            val = n
            out = []
            for r_val, r_sym in romans:
                while val >= r_val:
                    out.append(r_sym)
                    val -= r_val
            return "".join(out)


        # ANEXO I
        annex1_parts: list[Path] = []
        annex1_parts.append(Path(docs["PROC"].path))
        if has_ras_proc:
            # seu arquivo é MUNICIPIO_RAS_PROC.pdf => token no helper é RAS_PROC
            annex1_parts.append(Path(docs["RAS_PROC"].path))

        annex1_parts.append(Path(docs["KIT"].path))
        # contrato + representante ficam após os instrumentos/procuração
        annex1_parts.append(contrato_path)
        annex1_parts.append(rep_path)

        municipio_token = municipio
        anexo1_path = out_dir / _build_anexo_filename(municipio_token, "I", "INSTRUMENTOS PROCURATÓRIOS")
        writer = PdfWriter()
        for p in annex1_parts:
            reader = PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)
        anexo1_path.parent.mkdir(parents=True, exist_ok=True)
        with open(anexo1_path, "wb") as f:
            writer.write(f)


        # ANEXO II
        annex2_parts: list[Path] = []
        annex2_parts.append(Path(docs["CTR"].path))
        if has_ras_ctr:
            annex2_parts.append(Path(docs["RAS_CTR"].path))
        annex2_parts.append(Path(docs["PUB_CTR"].path))

        anexo2_path = out_dir / _build_anexo_filename(municipio_token, "II", "DOCUMENTOS CONTRATUAIS")
        writer = PdfWriter()
        for p in annex2_parts:
            reader = PdfReader(str(p))
            for page in reader.pages:
                writer.add_page(page)
        anexo2_path.parent.mkdir(parents=True, exist_ok=True)
        with open(anexo2_path, "wb") as f:
            writer.write(f)

        
        # ANEXOS de aditivos (ANEXO III, IV, ...)
        for idx, n in enumerate(adt_nums, start=3):
            tok_adt = f"ADT_{n:02d}"
            tok_ras = f"RAS_ADT_{n:02d}"
            tok_pub = f"PUB_ADT_{n:02d}"

            parts: list[Path] = [Path(docs[tok_adt].path)]
            if docs.get(tok_ras) is not None:
                parts.append(Path(docs[tok_ras].path))
            parts.append(Path(docs[tok_pub].path))

            # idx = 3 -> ANEXO III, idx = 4 -> ANEXO IV ...
            annex_roman = _roman(idx)
            # TERMO ADITIVO <n> (n vem do ADT)
            suffix = f"TERMO ADITIVO {n}"
            anexo_path = out_dir / _build_anexo_filename(municipio_token, annex_roman, suffix)
            writer = PdfWriter()
            for p in parts:
                reader = PdfReader(str(p))
                for page in reader.pages:
                    writer.add_page(page)
            anexo_path.parent.mkdir(parents=True, exist_ok=True)
            with open(anexo_path, "wb") as f:
                writer.write(f)



        # Comprimir anexos gerados de forma agressiva e corrigida para caminhos com espaços
        def _compress_pdf_in_place(pdf_path: Path) -> None:
            """Usa o Ghostscript com parâmetros agressivos de compressão.
            Corrigido para evitar o erro /undefinedfilename no Windows com caminhos complexos.
            """
            import os
            
            # Garante caminhos absolutos e normalizados para o SO
            pdf_absoluto = pdf_path.resolve()
            tmp_out = pdf_absoluto.with_suffix(".compressed.pdf")
            
            executaveis_gs = ["gswin64c", "gs", "gswin32c"]
            sucesso = False

            for exe in executaveis_gs:
                try:
                    # Passamos os caminhos usando os.fspath para garantir que o Python 
                    # os envie como strings limpas e protegidas para o subprocess
                    cmd = [
                        exe,
                        "-sDEVICE=pdfwrite",
                        "-dCompatibilityLevel=1.4",
                        "-dPDFSETTINGS=/screen", # Altere para /ebook se achar 72 dpi muito baixo
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
                        os.fspath(pdf_absoluto)
                    ]
                    
                    # Roda o processo especificando text=True e capturando erros
                    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                    
                    # Se o arquivo temporário foi criado com sucesso e tem dados
                    if tmp_out.exists() and tmp_out.stat().st_size > 0:
                        sucesso = True
                        break
                        
                except FileNotFoundError:
                    continue
                except Exception:
                    break

            # Substituição segura
            if sucesso and tmp_out.exists():
                try:
                    tam_original = pdf_absoluto.stat().st_size
                    tam_comprimido = tmp_out.stat().st_size
                    
                    # Só substitui se realmente reduziu o tamanho
                    if tam_comprimido < tam_original:
                        # Força a remoção do original antes de substituir (evita trava de permissão no Windows)
                        pdf_absoluto.unlink()
                        tmp_out.rename(pdf_absoluto)
                    else:
                        tmp_out.unlink()
                except Exception:
                    if tmp_out.exists():
                        tmp_out.unlink()

        # Compactar somente os anexos produzido (I, II e III+ quando existirem)
        for p in sorted(out_dir.glob("*.pdf")):
            if " - ANEXO " in p.name:
                _compress_pdf_in_place(p)

        messagebox.showinfo("Anexos", f"Anexos gerados e otimizados com sucesso em: {out_dir}")

    def _auto_generate_sumario(self) -> None:
        workdir = Path(self.selected_path.get())
        _, municipio, adt_nums, _adt_has_ras, _has_ras_proc, _has_ras_ctr = self._auto_validate_and_prepare()
        empresa = self.auto_selected_empresa.get().strip().upper()

        export_dir = workdir / "documentaiser_export"
        
        def _build_anexo_path(annex_roman: str, suffix: str) -> Path:
            return export_dir / f"{municipio.replace('_', r' ')} - ANEXO {annex_roman} - {suffix}.pdf"

        anexos: list[Path] = [
            _build_anexo_path("I", "INSTRUMENTOS PROCURATÓRIOS"),
            _build_anexo_path("II", "DOCUMENTOS CONTRATUAIS"),
        ]

        def _roman(n: int) -> str:
            romans = [
                (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")
            ]
            val = n
            out = []
            for r_val, r_sym in romans:
                while val >= r_val:
                    out.append(r_sym)
                    val -= r_val
            return "".join(out)

        # Monta a lista completa de caminhos dos anexos de aditivos
        for idx, n in enumerate(adt_nums, start=3):
            suffix = f"TERMO ADITIVO {n}"
            annex_roman = _roman(idx)
            anexos.append(_build_anexo_path(annex_roman, suffix))
        if not all(p.exists() for p in anexos):
            raise ValueError("Gere os anexos antes de gerar o sumário.")

        pages_per_anexo = [count_pages(p) for p in anexos]

        tex_base = Path(__file__).resolve().parent / "Sumario.tex"
        tex_content = tex_base.read_text(encoding="utf-8")

        # Garante as imagens do cabeçalho
        header_pngs = ["HLA_Header.png", "Ruda_Header.png"]
        for png_name in header_pngs:
            src_png = Path(__file__).resolve().parent / png_name
            if src_png.exists():
                dst_png = export_dir / png_name
                if not dst_png.exists():
                    dst_png.write_bytes(src_png.read_bytes())
               
        tex_content = re.sub(r"<<EMPRESA>>", empresa, tex_content)
        
        municipio_formatado = municipio.replace('_', r' ')
        tex_content = re.sub(r"SUMÁRIO", f"SUMÁRIO - {{{municipio_formatado}}}", tex_content)

        # --- GERAÇÃO DINÂMICA DAS PÁGINAS DO SUMÁRIO ---
        page_cursor = 1
        
        # 1. Atualiza a página inicial do Anexo I
        tex_content = re.sub(r"(Anexo I[^\n]*\\dotfill\s*)\d+", rf"\g<1>{page_cursor}", tex_content)
        page_cursor += pages_per_anexo[0]
        
        # 2. Atualiza a página inicial do Anexo II
        tex_content = re.sub(r"(Anexo II[^\n]*\\dotfill\s*)\d+", rf"\g<1>{page_cursor}", tex_content)
        page_cursor += pages_per_anexo[1]

        # 3. Constrói o bloco LaTeX completo para os Aditivos
        bloco_aditivos_latex = []
        for idx, n in enumerate(adt_nums, start=3):
            annex_roman = _roman(idx)
            
            # Monta o esqueleto identado do enumerate do LaTeX para o aditivo
            item_aditivo = (
                f"  \\item \\textbf{{Anexo {annex_roman} -- {n}º Termo Aditivo \\dotfill {page_cursor}}}\n"
                f"  \\begin{{enumerate}}\n"
                f"    \\item {n}º Aditivo \\dotfill {page_cursor}\n"
            )
            
            # Como a publicação fica dentro do aditivo, ela herda o cursor, 
            # mas no seu script atual pypdf une tudo em um único arquivo por anexo,
            # então mantemos a indicação visual da página inicial do bloco.
            item_aditivo += (
                f"    \\item Publicação do {n}º Aditivo em Diário Oficial \\dotfill {page_cursor}\n"
                f"  \\end{{enumerate}}\n\n"
            )
            
            bloco_aditivos_latex.append(item_aditivo)
            
            # Avança o cursor para o próximo documento
            page_cursor += pages_per_anexo[idx - 1]

        # Substitui a tag de marcação pelo bloco gerado (ou remove se não houver aditivos)
        texto_aditivos = "".join(bloco_aditivos_latex) if bloco_aditivos_latex else ""
        
        # O uso do lambda aqui evita qualquer erro de "bad escape \d" com as barras do LaTeX
        tex_content = re.sub(
            r"%\s*<<ADITIVOS>>",
            lambda match: texto_aditivos,
            tex_content
        )

        # Correção: Adicionado 'f' na string para de fato injetar a variável 'municipio' no nome do arquivo
        tex_filename = f"{municipio} - SUMÁRIO.tex"
        out_tex = export_dir / tex_filename

        out_tex.write_text(tex_content, encoding="utf-8")

        # Correção: Passando o nome correto do arquivo gerado para o pdflatex
        cmd = ["pdflatex", "-interaction=nonstopmode", tex_filename]
        
        # Adicionado errors="replace" para evitar o travamento por encoding (UnicodeDecodeError)
        p = subprocess.run(
            cmd, 
            cwd=str(export_dir), 
            capture_output=True, 
            text=True, 
            errors="replace"
        )
        
        if p.returncode != 0:
            raise RuntimeError("Falha ao compilar SUMARIO.pdf via pdflatex.\n" + p.stdout + p.stderr)

        desired_pdf = export_dir / f"{municipio} - SUMÁRIO.pdf"

        # Limpeza de temporários
        try:
            for f in export_dir.iterdir():
                if f.is_file() and f.suffix.lower() != ".pdf":
                    f.unlink()
        except Exception:
            pass

        messagebox.showinfo("Sumário", f"{desired_pdf.name} gerado com sucesso.")

    def _auto_generate_all(self) -> None:
        self._auto_validate_documents()
        self._auto_visualize_structure()
        self._auto_generate_anexos()
        self._auto_generate_sumario()