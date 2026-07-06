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

    def _auto_generate_anexos(self) -> tuple[list[int], list[int], list[list[int]]]:
            from pypdf import PdfReader, PdfWriter
            from pathlib import Path

            workdir = Path(self.selected_path.get())
            _, municipio, adt_nums, _adt_has_ras, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
            empresa = self.auto_selected_empresa.get().strip().upper()

            docs = locate_docs_for_municipio(workdir, municipio)
            assets = self._auto_get_empresa_assets(empresa)
            contrato_path = Path(assets["CONTRATO_SOCIAL"])
            rep_path = Path(assets["REPRESENTANTE"])

            out_dir = workdir / "documentaiser_export"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Inicialização dos vetores de contagem de páginas
            anexo1_pages: list[int] = []
            anexo2_pages: list[int] = []
            aditivos_pages: list[list[int]] = []

            # Formato solicitado:
            # - 1º anexo (I): INSTRUMENTOS PROCURATÓRIOS
            # - 2º anexo (II): DOCUMENTOS CONTRATUAIS
            # - 3º em diante (III, IV...): TERMO ADITIVO <num do aditivo> (conforme ADT)
            def _build_anexo_filename(municipio_token: str, annex_roman: str, suffix: str) -> str:
                return f"{municipio.replace('_', ' ')} - ANEXO {annex_roman} - {suffix}.pdf"

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

            # ANEXO I
            annex1_parts: list[Path] = []
            annex1_parts.append(Path(docs["PROC"].path))
            if has_ras_proc:
                annex1_parts.append(Path(docs["RAS_PROC"].path))

            annex1_parts.append(Path(docs["KIT"].path))
            annex1_parts.append(contrato_path)
            annex1_parts.append(rep_path)

            municipio_token = municipio
            anexo1_path = out_dir / _build_anexo_filename(municipio_token, "I", "INSTRUMENTOS PROCURATÓRIOS")
            writer = PdfWriter()
            
            for p in annex1_parts:
                reader = PdfReader(str(p))
                num_pages = len(reader.pages)
                anexo1_pages.append(num_pages)  # Salva a quantidade de páginas do doc atual
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
                num_pages = len(reader.pages)
                anexo2_pages.append(num_pages)  # Salva a quantidade de páginas do doc atual
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

                annex_roman = _roman(idx)
                suffix = f"TERMO ADITIVO {n}"
                anexo_path = out_dir / _build_anexo_filename(municipio_token, annex_roman, suffix)
                writer = PdfWriter()
                
                current_adt_pages: list[int] = []  # Vetor temporário para o aditivo atual
                for p in parts:
                    reader = PdfReader(str(p))
                    num_pages = len(reader.pages)
                    current_adt_pages.append(num_pages)  # Salva a quantidade de páginas do doc do aditivo
                    for page in reader.pages:
                        writer.add_page(page)
                
                aditivos_pages.append(current_adt_pages)  # Alimenta o vetor de vetores
                
                anexo_path.parent.mkdir(parents=True, exist_ok=True)
                with open(anexo_path, "wb") as f:
                    writer.write(f)

            # Retorna os vetores conforme solicitado
            return anexo1_pages, anexo2_pages, aditivos_pages



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

    def _auto_generate_sumario(self, anexo1_pages: list[int], anexo2_pages: list[int], aditivos_pages: list[list[int]]) -> None:
        import re
        import subprocess
        from pathlib import Path
        from tkinter import messagebox

        # --- PREPARAÇÃO DE AMBIENTE ---
        workdir = Path(self.selected_path.get())
        _, municipio, adt_nums, _adt_has_ras, _has_ras_proc, _has_ras_ctr = self._auto_validate_and_prepare()
        empresa = self.auto_selected_empresa.get().strip().upper()
        export_dir = workdir / "documentaiser_export"
        
        def _build_anexo_path(annex_roman: str, suffix: str) -> Path:
            return export_dir / f"{municipio.replace('_', ' ')} - ANEXO {annex_roman} - {suffix}.pdf"

        def _roman(n: int) -> str:
            romans = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), 
                      (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), 
                      (5, "V"), (4, "IV"), (1, "I")]
            val, out = n, []
            for r_val, r_sym in romans:
                while val >= r_val:
                    out.append(r_sym)
                    val -= r_val
            return "".join(out)

        # Registro e validação imediata dos anexos no disco
        anexos_paths = [
            _build_anexo_path("I", "INSTRUMENTOS PROCURATÓRIOS"),
            _build_anexo_path("II", "DOCUMENTOS CONTRATUAIS"),
        ]
        for idx, n in enumerate(adt_nums, start=3):
            anexos_paths.append(_build_anexo_path(_roman(idx), f"TERMO ADITIVO {n}"))
            
        if not all(p.exists() for p in anexos_paths):
            raise ValueError("Gere os anexos antes de gerar o sumário.")

        # ==========================================
        # 1. BLOCO: ANEXO I (CONTAGEM INDEPENDENTE)
        # ==========================================
        if len(anexo1_pages) in [4, 5]:
            p_proc = 1
            if len(anexo1_pages) == 5:
                p_rel  = p_proc + anexo1_pages[0]
                p_kit  = p_rel  + anexo1_pages[1]
                p_cont = p_kit  + anexo1_pages[2]
                p_rep  = p_cont + anexo1_pages[3]
                rel_ass = fr"    \item Validação das assinaturas \dotfill {p_rel}"
            else:
                p_kit  = p_proc + anexo1_pages[0]
                p_cont = p_kit  + anexo1_pages[1]
                p_rep  = p_cont + anexo1_pages[2]
                rel_ass = ""

            anexo_i = fr"""\textbf{{Anexo I -- Instrumentos procuratórios \dotfill 1}}
\begin{{enumerate}}
    \item Procuração \dotfill {p_proc} 
    {f'{rel_ass}\n' if rel_ass else ''}    \item Kit prefeito \dotfill {p_kit}
    \item Contrato Social da Empresa \dotfill {p_cont} 
    \item Documento de Identificação do Representante \dotfill {p_rep} 
\end{{enumerate}}"""
        else:
            raise ValueError(f"Quantidade de documentos do anexo I inválida ({len(anexo1_pages)} itens).")

        # ==========================================
        # 2. BLOCO: ANEXO II (CONTAGEM REINICIA EM 1)
        # ==========================================
        if len(anexo2_pages) in [2, 3]:
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
        else:
            raise ValueError(f"Quantidade de documentos do anexo II inválida ({len(anexo2_pages)} itens).")

        # ==========================================
        # 3. BLOCO: ADITIVOS (CONTAGEM REINICIA EM 1)
        # ==========================================
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
                f"  \\item \\textbf{{Anexo {annex_roman} -- {n}º Termo Aditivo \\dotfill 1}}\n"
                f"  \\begin{{enumerate}}\n"
                f"    \\item {n}º Termo Aditivo \\dotfill {p_adt_termo}\n"
                f"{rel_adt}"
                f"    \\item Publicação do {n}º Aditivo em Diário Oficial \\dotfill {p_adt_pub}\n"
                f"  \\end{{enumerate}}\n\n"
            )
            bloco_aditivos_latex.append(item_aditivo)

        # ==========================================
        # 4. PROCESSAMENTO DO ARQUIVO TEX
        # ==========================================
        tex_base = Path(__file__).resolve().parent / "Sumario.tex"
        tex_content = tex_base.read_text(encoding="utf-8")

        # Configuração de Metadados e Cabeçalho
        header_pngs = ["HLA_Header.png", "Ruda_Header.png"]
        for png_name in header_pngs:
            src_png = Path(__file__).resolve().parent / png_name
            if src_png.exists():
                dst_png = export_dir / png_name
                if not dst_png.exists():
                    dst_png.write_bytes(src_png.read_bytes())
               
        tex_content = re.sub(r"<<EMPRESA>>", empresa, tex_content)
        municipio_formatado = municipio.replace('_', ' ')
        tex_content = re.sub(r"SUMÁRIO", f"SUMÁRIO - {{{municipio_formatado}}}", tex_content)

        # Injeção Dinâmica Protegida (Evita o erro bad escape)
        tex_content = re.sub(r"<<ANEXO I>>", lambda m: anexo_i, tex_content)        
        tex_content = re.sub(r"<<ANEXO II>>", lambda m: anexo_ii, tex_content)        
        
        texto_aditivos = "".join(bloco_aditivos_latex) if bloco_aditivos_latex else ""
        tex_content = re.sub(r"<<ADITIVOS>>", lambda m: texto_aditivos, tex_content)

        # ==========================================
        # 5. COMPILAÇÃO E LIMPEZA DOS TEMPORÁRIOS
        # ==========================================
        tex_filename = f"{municipio} - SUMÁRIO.tex"
        out_tex = export_dir / tex_filename
        out_tex.write_text(tex_content, encoding="utf-8")

        cmd = ["xelatex", "-interaction=nonstopmode", tex_filename]
        p = subprocess.run(cmd, cwd=str(export_dir), capture_output=True, text=True, errors="replace")
        
        if p.returncode != 0:
            raise RuntimeError("Falha ao compilar SUMARIO.pdf via pdflatex.\n" + p.stdout + p.stderr)

        # Remover arquivos residuais de compilação do LaTeX (.log, .aux, .tex, etc)
        try:
            for f in export_dir.iterdir():
                if f.is_file() and f.suffix.lower() != ".pdf":
                    f.unlink()
        except Exception:
            pass

        desired_pdf = export_dir / f"{municipio} - SUMÁRIO.pdf"
        messagebox.showinfo("Sumário", f"{desired_pdf.name} gerado com sucesso.")

    def _auto_generate_all(self) -> None:
        self._auto_validate_documents()
        self._auto_visualize_structure()        
        # Captura os vetores de páginas retornados pela geração dos anexos
        anexo1_pages, anexo2_pages, aditivos_pages = self._auto_generate_anexos()  
   
        # Passa os vetores capturados para a geração do sumário
        self._auto_generate_sumario(anexo1_pages, anexo2_pages, aditivos_pages)