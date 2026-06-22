import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import re
from typing import Optional

# Garantir import do utils.py (fica em ../utils.py)
import sys
UTILS_DIR = Path(__file__).resolve().parent.parent
if str(UTILS_DIR) not in sys.path:
	sys.path.insert(0, str(UTILS_DIR))

from utils import normalize_string_for_filename

# Automação anexos/sumário
from automacao_documentaiser_helpers import (
    find_municipios_from_dir,
    locate_docs_for_municipio,
    concat_pdfs,
    count_pages,
    render_text_preview,
    parse_adt_numbers,
)

import subprocess
import tempfile




class Documentaiser:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Documentaiser v3.0")
        self.root.geometry("1100x720")

        # Estado do programa (antigos botões)
        self.selected_path = tk.StringVar(value="Nenhuma pasta selecionada")

        # Estado do módulo de renomeação inteligente
        self.ri_dir: Optional[Path] = None
        self.ri_pdf_files: list[Path] = []
        self.ri_idx: int = -1

        # Classificação atual (etapa por cliques)
        self.ri_selected_t1: Optional[str] = None
        self.ri_selected_ras_or_pub_kind: Optional[str] = None  # ex: RAS_CTR / RAS_ADT / RAS_PROC / PUB_CTR / PUB_ADT
        self.ri_selected_adt_number: Optional[int] = None

        # Municípo (derivado automaticamente) do arquivo atual
        self.ri_current_municipio: Optional[str] = None

        # Desfazer/validação
        self.ri_undo_stack: list[tuple[Path, Path]] = []  # (old_path, new_path)
        self.ri_used_names_in_session: set[str] = set()  # full filename

        # Flags
        self.ri_last_confirmed_token: Optional[str] = None

        # Estado automação anexos/sumário
        self.auto_selected_empresa = tk.StringVar(value="RUDA")
        self.auto_municipios_cache: list[str] = []
        self.auto_preview_text_widget = None  # criado na UI
        
        self._setup_ui()


    def _setup_ui(self) -> None:
        # Layout principal
        main_frame = tk.Frame(self.root, padx=16, pady=16)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Cabeçalho
        header = tk.Frame(main_frame)
        header.pack(fill=tk.X)
        tk.Label(header, text="Documentaiser", font=("Arial", 18, "bold")).pack(side=tk.LEFT)

        # Topo: seleção de diretório
        top = tk.Frame(main_frame)
        top.pack(fill=tk.X, pady=10)

        tk.Label(top, text="Diretório de Trabalho:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        path_frame = tk.Frame(top)
        path_frame.pack(fill=tk.X, pady=4)

        tk.Entry(path_frame, textvariable=self.selected_path, state='readonly').pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        tk.Button(path_frame, text="Navegar...", command=self.browse_folder).pack(side=tk.LEFT)

        # Separador
        tk.Frame(main_frame, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=14)

        # Grade 2 colunas
        # Container com scroll (caso a janela fique pequena)
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno dentro do canvas
        grid = tk.Frame(canvas)
        grid_id = canvas.create_window((0, 0), window=grid, anchor="nw")

        def _on_frame_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        grid.bind("<Configure>", _on_frame_configure)

        # Ajusta largura do frame interno quando o canvas redimensiona
        def _on_canvas_resize(event):
            canvas.itemconfig(grid_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_resize)

        left = tk.Frame(grid)
        right = tk.Frame(grid)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)


        # ----- RIGHT: Renomeação Inteligente -----
        right_controls = tk.LabelFrame(right, text="Renomeação Inteligente (Contratos)", padx=12, pady=12)
        right_controls.pack(fill=tk.BOTH, expand=True)

        # Linha: escolher diretório do módulo e listar PDFs
        module_top = tk.Frame(right_controls)
        module_top.pack(fill=tk.X)

        tk.Label(module_top, text="Pasta de PDFs (apenas nível da pasta):").pack(anchor=tk.W)

        module_dir_frame = tk.Frame(module_top)
        module_dir_frame.pack(fill=tk.X, pady=4)

        self.ri_dir_label = tk.Label(module_dir_frame, text="Nenhuma pasta escolhida", fg="#666")
        self.ri_dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(module_dir_frame, text="Selecionar...", command=self.ri_choose_dir).pack(side=tk.RIGHT)

        # Lista de PDFs
        list_frame = tk.Frame(right_controls)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        tk.Label(list_frame, text="Arquivos .pdf disponíveis:").pack(anchor=tk.W)

        self.ri_listbox = tk.Listbox(list_frame, height=10)
        self.ri_listbox.pack(fill=tk.BOTH, expand=True, pady=6)
        self.ri_listbox.bind("<<ListboxSelect>>", self.ri_on_select_from_list)

        # Navegação
        nav_frame = tk.Frame(right_controls)
        nav_frame.pack(fill=tk.X, pady=(0, 8))

        self.ri_btn_prev = tk.Button(nav_frame, text="◀ Anterior", width=14, command=self.ri_prev)
        self.ri_btn_prev.pack(side=tk.LEFT)

        self.ri_btn_next = tk.Button(nav_frame, text="Próximo ▶", width=14, command=self.ri_next)
        self.ri_btn_next.pack(side=tk.LEFT, padx=10)

        self.ri_btn_skip = tk.Button(nav_frame, text="Pular", width=10, command=self.ri_skip)
        self.ri_btn_skip.pack(side=tk.LEFT, padx=10)

        self.ri_btn_undo = tk.Button(nav_frame, text="Desfazer", width=12, command=self.ri_undo)
        self.ri_btn_undo.pack(side=tk.LEFT)

        # Painel Nome Original / Novo Nome
        name_frame = tk.Frame(right_controls)
        name_frame.pack(fill=tk.X, pady=(8, 8))

        self.ri_lbl_original = tk.Label(name_frame, text="Nome Original: -", anchor="w")
        self.ri_lbl_original.pack(fill=tk.X)

        self.ri_lbl_new = tk.Label(name_frame, text="Novo Nome: -", anchor="w", font=("Arial", 10, "bold"))
        self.ri_lbl_new.pack(fill=tk.X, pady=(4, 0))

        # Etapa 1: T1
        t1_frame = tk.LabelFrame(right_controls, text="Tipo Principal (T1)")
        t1_frame.pack(fill=tk.X, pady=(6, 8))

        self.ri_btn_ctr = tk.Button(t1_frame, text="CTR - Contrato", command=lambda: self.ri_choose_t1("CTR"), width=18)
        self.ri_btn_adt = tk.Button(t1_frame, text="ADT - Aditivo", command=lambda: self.ri_choose_t1("ADT"), width=18)
        self.ri_btn_ras = tk.Button(t1_frame, text="RAS - Rel. Assinaturas", command=lambda: self.ri_choose_t1("RAS"), width=22)
        self.ri_btn_pub = tk.Button(t1_frame, text="PUB - Publicação", command=lambda: self.ri_choose_t1("PUB"), width=18)
        self.ri_btn_proc = tk.Button(t1_frame, text="PROC - Procuração", command=lambda: self.ri_choose_t1("PROC"), width=18)
        self.ri_btn_kit = tk.Button(t1_frame, text="KIT - Kit Prefeito", command=lambda: self.ri_choose_t1("KIT"), width=18)

        self.ri_btn_ctr.grid(row=0, column=0, padx=6, pady=6)
        self.ri_btn_adt.grid(row=0, column=1, padx=6, pady=6)
        self.ri_btn_ras.grid(row=0, column=2, padx=6, pady=6)
        self.ri_btn_pub.grid(row=1, column=0, padx=6, pady=6)
        self.ri_btn_proc.grid(row=1, column=1, padx=6, pady=6)
        self.ri_btn_kit.grid(row=1, column=2, padx=6, pady=6)

        # Etapa 2 dinâmica
        t2_frame = tk.LabelFrame(right_controls, text="Etapas Complementares (T2)")
        t2_frame.pack(fill=tk.X, pady=(0, 8))

        self.ri_t2_container = tk.Frame(t2_frame)
        self.ri_t2_container.pack(fill=tk.X, padx=8, pady=8)

        # ADT numeração sugerida
        self.ri_lbl_adt_suggestion = tk.Label(right_controls, text="", fg="#333")
        self.ri_lbl_adt_suggestion.pack(fill=tk.X)

        # Confirmação
        confirm_frame = tk.Frame(right_controls)
        confirm_frame.pack(fill=tk.X, pady=(10, 0))

        self.ri_btn_confirm = tk.Button(confirm_frame, text="✅ Confirmar Renomeação", height=2, bg="#28a745", fg="white", command=self.ri_confirm)
        self.ri_btn_confirm.pack(side=tk.LEFT)

        self.ri_state_refresh()

        # -------------------- Automação anexos e sumário --------------------
        auto_frame = tk.LabelFrame(left if False else right, text="GERAÇÃO DE ANEXOS E SUMÁRIO", padx=12, pady=10)
        auto_frame.pack(fill=tk.X, pady=(14, 0))

        empresa_box = tk.LabelFrame(auto_frame, text="EMPRESA RESPONSÁVEL", padx=10, pady=8)
        empresa_box.pack(fill=tk.X, pady=(0, 10))

        empresa_row = tk.Frame(empresa_box)
        empresa_row.pack(fill=tk.X)

        tk.Radiobutton(empresa_row, text="RUDA", variable=self.auto_selected_empresa, value="RUDA").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(empresa_row, text="HLA", variable=self.auto_selected_empresa, value="HLA").pack(side=tk.LEFT, padx=10)

        btns_frame = tk.Frame(auto_frame)
        btns_frame.pack(fill=tk.X)

        tk.Button(btns_frame, text="Validar Documentos", command=self._auto_validate_documents, height=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btns_frame, text="Visualizar Estrutura", command=self._auto_visualize_structure, height=2).pack(side=tk.LEFT, padx=5)

        btns_frame2 = tk.Frame(auto_frame)
        btns_frame2.pack(fill=tk.X, pady=(6, 0))

        tk.Button(btns_frame2, text="Gerar Anexos", command=self._auto_generate_anexos, height=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btns_frame2, text="Gerar Sumário", command=self._auto_generate_sumario, height=2).pack(side=tk.LEFT, padx=5)
        tk.Button(btns_frame2, text="Gerar Tudo", command=self._auto_generate_all, height=2, bg="#1e90ff", fg="white").pack(side=tk.LEFT, padx=5)

        tk.Label(auto_frame, text="Prévia textual (obrigatória):").pack(anchor=tk.W, pady=(10, 4))
        self.auto_preview_text_widget = tk.Text(auto_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.auto_preview_text_widget.pack(fill=tk.BOTH, expand=False)

    # -------------------- Utilitário (pasta existente) --------------------

    def browse_folder(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.selected_path.set(directory)

    def create_subfolder(self) -> None:
        current_dir = self.selected_path.get()
        if current_dir == "Nenhuma pasta selecionada":
            messagebox.showwarning("Aviso", "Por favor, selecione uma pasta primeiro!")
            return

        standard_folders = [
            "ANEEL",
            "DOCUMENTOS RECEBIDOS",
            "PAGAMENTOS",
            "RECLAMAÇÃO FORMAL",
            "E-MAILS",
        ]

        def to_regex(name: str) -> re.Pattern:
            pattern = re.sub(r"[\s_-]+", r"[\s_-]*", name.strip())
            return re.compile(f"^{pattern}$", re.IGNORECASE)

        try:
            existing_dirs = [p for p in Path(current_dir).iterdir() if p.is_dir()]

            for standard in standard_folders:
                regex = to_regex(standard)

                matched_folder = None
                for folder in existing_dirs:
                    if regex.match(folder.name):
                        matched_folder = folder
                        break

                target_path = Path(current_dir) / standard

                if matched_folder and matched_folder.name != standard:
                    matched_folder.rename(target_path)
                elif not matched_folder:
                    target_path.mkdir(exist_ok=True)

            messagebox.showinfo("Sucesso", "Pastas normalizadas e criadas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao processar pastas: {e}")

    def organize_pdfs(self) -> None:
        current_dir = self.selected_path.get()
        if current_dir == "Nenhuma pasta selecionada":
            messagebox.showwarning("Aviso", "Por favor, selecione uma pasta primeiro!")
            return

        base_path = Path(current_dir)
        if not base_path.exists() or not base_path.is_dir():
            messagebox.showerror("Erro", "Diretório inválido.")
            return

        standard_folders = [
            "ANEEL",
            "RECLAMAÇÃO FORMAL",
            "PAGAMENTO",
            "E-MAILS",
            "DOCUMENTOS RECEBIDOS",
        ]

        pdf_files = sorted(base_path.glob("*.pdf"), key=lambda p: p.name.lower())
        if not pdf_files:
            messagebox.showwarning("Aviso", "Nenhum arquivo .pdf encontrado na pasta selecionada.")
            return

        created_folders_count = 0
        moved_count = 0
        errors: list[str] = []

        for pdf_path in pdf_files:
            try:
                reclama_name = pdf_path.stem
                target_reclamacao_dir = base_path / reclama_name

                for sub in standard_folders:
                    sub_dir = target_reclamacao_dir / sub
                    if not sub_dir.exists():
                        sub_dir.mkdir(parents=True, exist_ok=True)
                        created_folders_count += 1

                target_pdf_path = target_reclamacao_dir / "RECLAMAÇÃO FORMAL" / pdf_path.name

                if target_pdf_path.resolve() == pdf_path.resolve():
                    continue
                if target_pdf_path.exists():
                    errors.append(f"[IGNORADO] Já existe: {target_pdf_path}")
                    continue

                pdf_path.replace(target_pdf_path)
                moved_count += 1

            except Exception as e:
                errors.append(f"[ERRO] {pdf_path.name}: {e}")

        msg = (
            f"Concluído!\n"
            f"PDFs movidos: {moved_count}\n"
            f"Subpastas criadas (quando necessário): {created_folders_count}"
        )
        if errors:
            msg += "\n\nOcorreram alguns avisos/erros:\n" + "\n".join(errors[:30])
            messagebox.showwarning("Finalizado com avisos", msg)
        else:
            messagebox.showinfo("Sucesso", msg)

    # -------------------- Renomeação Inteligente --------------------
    def ri_choose_dir(self) -> None:
        directory = filedialog.askdirectory()
        if not directory:
            return

        self.ri_dir = Path(directory)
        self.ri_used_names_in_session.clear()
        self.ri_undo_stack.clear()
        self.ri_selected_t1 = None
        self.ri_selected_ras_or_pub_kind = None
        self.ri_selected_adt_number = None
        self.ri_current_municipio = None
        self.ri_last_confirmed_token = None

        # Apenas nível da pasta (como definido)
        self.ri_pdf_files = sorted(self.ri_dir.glob("*.pdf"), key=lambda p: p.name.lower())

        self.ri_listbox.delete(0, tk.END)
        for p in self.ri_pdf_files:
            self.ri_listbox.insert(tk.END, p.name)

        if not self.ri_pdf_files:
            messagebox.showwarning("Aviso", "Nenhum PDF encontrado na pasta selecionada (nível da pasta).")
            self.ri_idx = -1
            self.ri_state_refresh()
            self._ri_clear_name_panel()
            self.ri_clear_t2()
            return

        self.ri_idx = 0
        self.ri_listbox.select_set(0)
        self.ri_listbox.see(0)
        self.ri_load_current_pdf()
        self.ri_state_refresh()

    def ri_on_select_from_list(self, _evt=None) -> None:
        if self.ri_dir is None:
            return

        sel = self.ri_listbox.curselection()
        if not sel:
            return
        i = int(sel[0])
        if i < 0 or i >= len(self.ri_pdf_files):
            return
        self.ri_idx = i
        self.ri_reset_classification_for_new_pdf()
        self.ri_load_current_pdf()

    def ri_reset_classification_for_new_pdf(self) -> None:
        self.ri_selected_t1 = None
        self.ri_selected_ras_or_pub_kind = None
        self.ri_selected_adt_number = None
        self.ri_selected_t2 = None  # compat não usado
        self.ri_current_municipio = None
        self.ri_lbl_adt_suggestion.config(text="")
        self.ri_clear_t2()
        self._ri_update_new_name_preview()

    def ri_load_current_pdf(self) -> None:
        if self.ri_idx < 0 or self.ri_idx >= len(self.ri_pdf_files):
            return

        pdf_path = self.ri_pdf_files[self.ri_idx]
        self.ri_lbl_original.config(text=f"Nome Original: {pdf_path.name}")

        municipio = self.ri_get_municipio_for_file(pdf_path)
        self.ri_current_municipio = municipio

        # Painel novo nome já depende da classificação (por enquanto pode estar -)
        self._ri_update_new_name_preview()

    def ri_get_municipio_for_file(self, pdf_path: Path) -> str:
        """Regra corrigida: MUNICÍPIO = nome da pasta avô do PDF.

        Motivo: o módulo estava usando o pai imediato (ex: pegava C em /A/B/C/D).
        Agora sobe uma hierarquia e pega B.
        """
        parent = pdf_path.parent
        grand_parent = parent.parent.parent
        # fallback: se não existir avô, usa pai imediato
        return grand_parent.name if grand_parent != parent else parent.name


    def ri_clear_t2(self) -> None:
        for w in self.ri_t2_container.winfo_children():
            w.destroy()

    def ri_state_refresh(self) -> None:
        enabled = self.ri_dir is not None and self.ri_idx >= 0 and self.ri_idx < len(self.ri_pdf_files)

        state = tk.NORMAL if enabled else tk.DISABLED
        for b in [
            self.ri_btn_prev, self.ri_btn_next, self.ri_btn_skip,
            self.ri_btn_undo, self.ri_btn_confirm,
            self.ri_btn_ctr, self.ri_btn_adt, self.ri_btn_ras,
            self.ri_btn_pub, self.ri_btn_proc, self.ri_btn_kit,
        ]:
            try:
                b.config(state=state)
            except Exception:
                pass

        # Desabilita numeração/etapas se não houver arquivo

    def ri_prev(self) -> None:
        if self.ri_idx <= 0:
            return
        self.ri_idx -= 1
        self.ri_listbox.select_clear(0, tk.END)
        self.ri_listbox.select_set(self.ri_idx)
        self.ri_listbox.see(self.ri_idx)
        self.ri_reset_classification_for_new_pdf()
        self.ri_load_current_pdf()
        self.ri_state_refresh()

    def ri_next(self) -> None:
        if self.ri_dir is None:
            return
        if self.ri_idx < 0:
            return
        if self.ri_idx >= len(self.ri_pdf_files) - 1:
            return
        self.ri_idx += 1
        self.ri_listbox.select_clear(0, tk.END)
        self.ri_listbox.select_set(self.ri_idx)
        self.ri_listbox.see(self.ri_idx)
        self.ri_reset_classification_for_new_pdf()
        self.ri_load_current_pdf()
        self.ri_state_refresh()

    def ri_skip(self) -> None:
        # pula sem renomear
        self.ri_next()

    def ri_undo(self) -> None:
        if not self.ri_undo_stack:
            messagebox.showinfo("Info", "Nada para desfazer.")
            return

        old_path, new_path = self.ri_undo_stack.pop()

        try:
            # Reverte: new -> old
            if new_path.exists():
                new_path.replace(old_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao desfazer: {e}")
            return

        # Recalcula estado do nome já utilizado
        self.ri_used_names_in_session.discard(new_path.name)
        self.ri_confirmed_history.pop() if getattr(self, "ri_confirmed_history", None) else None

        # Atualiza preview atual (sem alterar classificação atual)
        self._ri_update_new_name_preview()

    def ri_choose_t1(self, t1: str) -> None:
        if self.ri_current_municipio is None:
            return

        self.ri_selected_t1 = t1
        self.ri_selected_ras_or_pub_kind = None
        self.ri_selected_adt_number = None
        self.ri_lbl_adt_suggestion.config(text="")

        # IMPORTANTE: ao trocar T1, limpar somente a área T2
        # para não "sumir" com o botão de confirmar.
        self.ri_clear_t2()

        # RAS e PUB precisam de T2 específico
        if t1 == "RAS":
            self._ri_build_t2_buttons_ras()
        elif t1 == "PUB":
            self._ri_build_t2_buttons_pub()
        elif t1 == "ADT":
            # Sugere numeração
            self.ri_selected_adt_number = self.ri_suggest_next_adt_number()
            if self.ri_selected_adt_number is not None:
                self.ri_lbl_adt_suggestion.config(
                    text=f"Sugestão ADT: {self.ri_selected_adt_number:02d} (clique em Confirmar)"
                )
        else:
            # CTR/PROC/KIT: sem T2 extra
            pass

        self._ri_update_new_name_preview()

    def _ri_build_t2_buttons_ras(self) -> None:
        # RAS: CTR / ADT / PROC
        kind_frame = self.ri_t2_container

        tk.Label(kind_frame, text="Selecione o tipo dentro de RAS:").pack(anchor="w")

        btn_ctr = tk.Button(kind_frame, text="RAS - CTR", width=18, command=lambda: self.ri_choose_ras_kind("RAS_CTR"))
        btn_adt = tk.Button(kind_frame, text="RAS - ADT", width=18, command=lambda: self.ri_choose_ras_kind("RAS_ADT"))
        btn_proc = tk.Button(kind_frame, text="RAS - PROC", width=18, command=lambda: self.ri_choose_ras_kind("RAS_PROC"))

        btn_ctr.pack(side=tk.LEFT, padx=6, pady=6)
        btn_adt.pack(side=tk.LEFT, padx=6, pady=6)
        btn_proc.pack(side=tk.LEFT, padx=6, pady=6)

    def _ri_build_t2_buttons_pub(self) -> None:
        # PUB: CTR / ADT
        kind_frame = self.ri_t2_container

        tk.Label(kind_frame, text="Selecione o tipo dentro de PUB:").pack(anchor="w")

        btn_ctr = tk.Button(kind_frame, text="PUB - CTR", width=18, command=lambda: self.ri_choose_pub_kind("PUB_CTR"))
        btn_adt = tk.Button(kind_frame, text="PUB - ADT", width=18, command=lambda: self.ri_choose_pub_kind("PUB_ADT"))

        btn_ctr.pack(side=tk.LEFT, padx=6, pady=6)
        btn_adt.pack(side=tk.LEFT, padx=6, pady=6)

    def ri_choose_ras_kind(self, kind: str) -> None:
        self.ri_selected_ras_or_pub_kind = kind
        self.ri_selected_adt_number = None
        self.ri_lbl_adt_suggestion.config(text="")

        if kind == "RAS_ADT":
            self.ri_selected_adt_number = self.ri_suggest_next_adt_number(ras_or_pub_prefix="RAS_ADT")
            if self.ri_selected_adt_number is not None:
                self.ri_lbl_adt_suggestion.config(
                    text=f"Sugestão RAS_ADT: {self.ri_selected_adt_number:02d} (clique em Confirmar)"
                )

        self._ri_update_new_name_preview()

    def ri_choose_pub_kind(self, kind: str) -> None:
        self.ri_selected_ras_or_pub_kind = kind
        self.ri_selected_adt_number = None
        self.ri_lbl_adt_suggestion.config(text="")

        if kind == "PUB_ADT":
            self.ri_selected_adt_number = self.ri_suggest_next_adt_number(ras_or_pub_prefix="PUB_ADT")
            if self.ri_selected_adt_number is not None:
                self.ri_lbl_adt_suggestion.config(
                    text=f"Sugestão PUB_ADT: {self.ri_selected_adt_number:02d} (clique em Confirmar)"
                )

        self._ri_update_new_name_preview()

    def ri_suggest_next_adt_number(self, ras_or_pub_prefix: Optional[str] = None) -> Optional[int]:
        if self.ri_dir is None or self.ri_current_municipio is None:
            return None

        municipio = normalize_string_for_filename(self.ri_current_municipio)

        # scan nos nomes atuais (mesmo nível), formato já normalizado do sistema
        # Aditivo direto: MUNICIPIO_ADT_XX
        # RAS ADT: MUNICIPIO_RAS_ADT_XX
        # PUB ADT: MUNICIPIO_PUB_ADT_XX

        if ras_or_pub_prefix == "RAS_ADT":
            pattern = re.compile(rf"^{re.escape(municipio)}_RAS_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)
        elif ras_or_pub_prefix == "PUB_ADT":
            pattern = re.compile(rf"^{re.escape(municipio)}_PUB_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)
        else:
            pattern = re.compile(rf"^{re.escape(municipio)}_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)

        max_num = 0
        for p in self.ri_dir.glob("*.pdf"):
            m = pattern.match(p.name)
            if m:
                try:
                    n = int(m.group(1))
                    max_num = max(max_num, n)
                except Exception:
                    pass

        # Próximo
        return max_num + 1

    def _ri_update_new_name_preview(self) -> None:
        if self.ri_idx < 0 or self.ri_idx >= len(self.ri_pdf_files):
            self.ri_lbl_new.config(text="Novo Nome: -")
            return

        pdf_path = self.ri_pdf_files[self.ri_idx]

        new_name = self._ri_build_new_name(pdf_path)
        if new_name is None:
            self.ri_lbl_new.config(text="Novo Nome: -")
        else:
            self.ri_lbl_new.config(text=f"Novo Nome: {new_name}")

    def _ri_build_new_name(self, pdf_path: Path) -> Optional[str]:
        if self.ri_current_municipio is None or self.ri_selected_t1 is None:
            return None

        municipio = normalize_string_for_filename(self.ri_current_municipio)

        t1 = self.ri_selected_t1

        if t1 == "CTR":
            return f"{municipio}_CTR.pdf"

        if t1 == "PROC":
            return f"{municipio}_PROC.pdf"

        if t1 == "KIT":
            return f"{municipio}_KIT.pdf"

        if t1 == "ADT":
            if self.ri_selected_adt_number is None:
                return None
            return f"{municipio}_ADT_{self.ri_selected_adt_number:02d}.pdf"

        if t1 == "RAS":
            if self.ri_selected_ras_or_pub_kind == "RAS_CTR":
                return f"{municipio}_RAS_CTR.pdf"
            if self.ri_selected_ras_or_pub_kind == "RAS_PROC":
                return f"{municipio}_RAS_PROC.pdf"
            if self.ri_selected_ras_or_pub_kind == "RAS_ADT":
                if self.ri_selected_adt_number is None:
                    return None
                return f"{municipio}_RAS_ADT_{self.ri_selected_adt_number:02d}.pdf"

        if t1 == "PUB":
            if self.ri_selected_ras_or_pub_kind == "PUB_CTR":
                return f"{municipio}_PUB_CTR.pdf"
            if self.ri_selected_ras_or_pub_kind == "PUB_ADT":
                if self.ri_selected_adt_number is None:
                    return None
                return f"{municipio}_PUB_ADT_{self.ri_selected_adt_number:02d}.pdf"

        return None

    def _ri_clear_name_panel(self) -> None:
        self.ri_lbl_original.config(text="Nome Original: -")
        self.ri_lbl_new.config(text="Novo Nome: -")

    def ri_confirm(self) -> None:
        if self.ri_idx < 0 or self.ri_idx >= len(self.ri_pdf_files):
            return

        pdf_path = self.ri_pdf_files[self.ri_idx]
        new_name = self._ri_build_new_name(pdf_path)
        if new_name is None:
            messagebox.showwarning("Aviso", "Selecione as opções para gerar o novo nome.")
            return

        # valida duplicidade no mesmo diretório
        target_path = pdf_path.with_name(new_name)

        if target_path.exists():
            messagebox.showwarning("Aviso", f"Já existe um arquivo com esse nome: {new_name}")
            return

        if new_name in self.ri_used_names_in_session:
            messagebox.showwarning("Aviso", f"Nome já usado nesta sessão: {new_name}")
            return

        # renomear
        old_path = pdf_path
        try:
            old_path.replace(target_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao renomear: {e}")
            return

        self.ri_used_names_in_session.add(new_name)
        self.ri_undo_stack.append((old_path, target_path))

        # atualizar lista interna com o novo caminho
        self.ri_pdf_files[self.ri_idx] = target_path

        # atualizar mostrador da GUI
        self.ri_lbl_original.config(text=f"Nome Original: {target_path.name}")
        self._ri_update_new_name_preview()

        # atualizar o texto do item selecionado no Listbox
        try:
            self.ri_listbox.delete(self.ri_idx)
            self.ri_listbox.insert(self.ri_idx, target_path.name)
            self.ri_listbox.select_set(self.ri_idx)
            self.ri_listbox.see(self.ri_idx)
        except Exception:
            pass


        # Sugestão inteligente simples: token do último confirmado
        self.ri_last_confirmed_token = new_name.replace(".pdf", "")

        # avançar automaticamente
        self.ri_next()


# -------------------- Automação anexos e sumário --------------------
    def _auto_get_empresa_assets(self, empresa: str) -> dict[str, str]:
        base = Path(__file__).resolve().parent
        empresa_dir = base / empresa
        # nomes fixos (conforme pastas existentes no projeto)
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
            raise ValueError("Não foi possível detectar MUNICÍPIOs a partir dos arquivos PDF (nomenclatura <MUNICIPIO>_CTR.pdf, etc.).")

        municipios = mun_list
        if len(municipios) != 1:
            # por hora o task especifica montagem por MUNICÍPIO no exemplo; mantemos simples.
            raise ValueError(f"Detectados múltiplos MUNICÍPIOs ({len(municipios)}). Ajuste para processamento em lote ainda não implementado: {municipios[:5]}")

        municipio = municipios[0]
        docs = locate_docs_for_municipio(workdir, municipio)

        has_ras_proc = docs.get("RAS_PROC") is not None
        # RAS_CTR é opcional
        has_ras_ctr = docs.get("RAS_CTR") is not None

        # aditivos
        adt_nums = docs.get("ADT_NUMS") or []
        if not adt_nums:
            raise ValueError(f"Nenhum aditivo encontrado para {municipio} (esperado: {municipio}_ADT_XX.pdf)")

        adt_has_ras: dict[int, bool] = {}
        for n in adt_nums:
            token = f"RAS_ADT_{n:02d}"
            adt_has_ras[n] = docs.get(token) is not None

        # obrigatórios
        required_tokens = ["PROC", "KIT", "CTR", "PUB_CTR"]
        missing = [t for t in required_tokens if docs.get(t) is None]
        if missing:
            # mensagem estilo task
            for t in missing:
                expected = {
                    "PROC": f"{municipio}_PROC.pdf",
                    "KIT": f"{municipio}_KIT.pdf",
                    "CTR": f"{municipio}_CTR.pdf",
                    "PUB_CTR": f"{municipio}_PUB_CTR.pdf",
                }[t]
                raise ValueError(f"Documento {expected} não encontrado.")

        # valida PUB/RAS para cada aditivo
        for n in adt_nums:
            adt_tok = f"ADT_{n:02d}"
            pub_tok = f"PUB_ADT_{n:02d}"
            if docs.get(adt_tok) is None:
                raise ValueError(f"Documento {municipio}_ADT_{n:02d}.pdf não encontrado.")
            if docs.get(pub_tok) is None:
                raise ValueError(f"Documento {municipio}_PUB_ADT_{n:02d}.pdf não encontrado.")
            # RAS opcional: não precisa de PUB, mas se existir RAS_ADT então PUB já é obrigatório acima.

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
        empresa_title = empresa.title()

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
        if self.auto_preview_text_widget is None:
            return
        self.auto_preview_text_widget.config(state=tk.NORMAL)
        self.auto_preview_text_widget.delete("1.0", tk.END)
        self.auto_preview_text_widget.insert(tk.END, text)
        self.auto_preview_text_widget.config(state=tk.DISABLED)

    def _auto_generate_anexos(self) -> None:
        from pypdf import PdfWriter

        workdir = Path(self.selected_path.get())
        municipios, municipio, adt_nums, adt_has_ras, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
        empresa = self.auto_selected_empresa.get().strip().upper()

        docs = locate_docs_for_municipio(workdir, municipio)
        assets = self._auto_get_empresa_assets(empresa)
        contrato_path = Path(assets["CONTRATO_SOCIAL"])
        rep_path = Path(assets["REPRESENTANTE"])

        out_dir = workdir / "documentaiser_export"
        out_dir.mkdir(parents=True, exist_ok=True)

        def _safe_concat_token_paths(tokens: list[tuple[str, Path]] , out_name: str) -> Path:
            out_path = out_dir / out_name
            writer = PdfWriter()
            for _tok, p in tokens:
                reader = pypdf.PdfReader(str(p))
                for page in reader.pages:
                    writer.add_page(page)
            with open(out_path, "wb") as f:
                writer.write(f)
            return out_path

        # helper local: evita depender de pypdf import no escopo (usei direto)
        import pypdf

        # ANEXO I
        annex1_parts: list[tuple[str, Path]] = []
        annex1_parts.append(("PROC", Path(docs["PROC"].path)))
        if has_ras_proc:
            annex1_parts.append(("RAS_PROC", Path(docs["RAS_PROC"].path)))
        annex1_parts.append(("KIT", Path(docs["KIT"].path)))
        annex1_parts.append(("CONTRATO_SOCIAL", contrato_path))
        annex1_parts.append(("REPRESENTANTE", rep_path))

        anexo1_path = out_dir / "ANEXO_I.pdf"
        concat_pdfs([p for _, p in annex1_parts], anexo1_path)

        # ANEXO II
        annex2_parts: list[tuple[str, Path]] = []
        annex2_parts.append(("CTR", Path(docs["CTR"].path)))
        if has_ras_ctr:
            annex2_parts.append(("RAS_CTR", Path(docs["RAS_CTR"].path)))
        annex2_parts.append(("PUB_CTR", Path(docs["PUB_CTR"].path)))
        anexo2_path = out_dir / "ANEXO_II.pdf"
        concat_pdfs([p for _, p in annex2_parts], anexo2_path)

        # ANEXOS de aditivos
        for idx, n in enumerate(adt_nums, start=3):
            tok_adt = f"ADT_{n:02d}"
            tok_ras = f"RAS_ADT_{n:02d}"
            tok_pub = f"PUB_ADT_{n:02d}"

            parts: list[Path] = [Path(docs[tok_adt].path)]
            if docs.get(tok_ras) is not None:
                parts.append(Path(docs[tok_ras].path))
            parts.append(Path(docs[tok_pub].path))

            anexo_path = out_dir / f"ANEXO_{idx}.pdf"
            concat_pdfs(parts, anexo_path)

        messagebox.showinfo("Anexos", f"Anexos gerados em: {out_dir}")

    def _auto_generate_sumario(self) -> None:
        # Implementação completa do sumário (LaTeX/pdflatex) depende do ambiente LaTeX instalado.
        # Aqui valida pré-requisitos e gera sumário_temp.tex com base em sumario.tex.
        workdir = Path(self.selected_path.get())
        municipios, municipio, adt_nums, adt_has_ras, has_ras_proc, has_ras_ctr = self._auto_validate_and_prepare()
        empresa = self.auto_selected_empresa.get().strip().upper()

        export_dir = workdir / "documentaiser_export"
        anexos = [export_dir / "ANEXO_I.pdf", export_dir / "ANEXO_II.pdf"]
        for idx, _n in enumerate(adt_nums, start=3):
            anexos.append(export_dir / f"ANEXO_{idx}.pdf")

        if not all(p.exists() for p in anexos):
            raise ValueError("Gere os anexos antes de gerar o sumário.")

        # conta páginas de cada item (aproximação usando contagem total de cada PDF gerado como bloco)
        pages_per_anexo = [count_pages(p) for p in anexos]

        # preencher sumario.tex (simples: substitui \\tipoLogo e \\dotfill do nível 1)
        tex_base = Path(__file__).resolve().parent / "Sumario.tex"
        tex_content = tex_base.read_text(encoding="utf-8")

        tipo_logo = empresa
        tex_content = re.sub(r"\\newcommand\{\\tipoLogo\}\{[^\}]*\}", f"\\newcommand{{\\tipoLogo}}{{{tipo_logo}}}", tex_content)

        # gera um sumario_temp.tex simplesmente mantendo estrutura e ajustando apenas páginas iniciais dos anexos
        # (linhas internas de item devem ser refinadas quando tivermos a divisão por documento)
        page_cursor = 1
        # substitui as ocorrências no primeiro nível (Anexo I e II) e ignora aditivos já comentados no template
        def _replace_dotfill(item_text: str, page: int) -> None:
            nonlocal tex_content
            tex_content = tex_content.replace(item_text, item_text[:-len(str(int(re.findall(r"\\dotfill (\\d+)$", item_text.strip()) or [0])[0]))] )

        # Ajuste bruto: troca os números do \\dotfill após cada "Anexo X" no template
        tex_content = re.sub(r"(Anexo I[^\n]*\\dotfill )\d+", r"\\1" + str(page_cursor), tex_content)
        page_cursor += pages_per_anexo[0]
        tex_content = re.sub(r"(Anexo II[^\n]*\\dotfill )\d+", r"\\1" + str(page_cursor), tex_content)

        out_tex = export_dir / "sumario_temp.tex"
        out_tex.write_text(tex_content, encoding="utf-8")

        # compilar com pdflatex (se disponível)
        cmd = ["pdflatex", "-interaction=nonstopmode", "sumario_temp.tex"]
        p = subprocess.run(cmd, cwd=str(export_dir), capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError("Falha ao compilar SUMARIO.pdf via pdflatex.\n" + p.stdout + p.stderr)

        messagebox.showinfo("Sumário", "SUMARIO.pdf gerado com sucesso.")


    def _auto_generate_all(self) -> None:
        self._auto_validate_documents()
        self._auto_visualize_structure()
        self._auto_generate_anexos()
        self._auto_generate_sumario()

if __name__ == "__main__":

    root = tk.Tk()
    app = Documentaiser(root)
    root.mainloop()


