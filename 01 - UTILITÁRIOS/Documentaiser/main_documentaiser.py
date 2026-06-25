"""Script principal do Documentaiser (UI + orchestration).

Este arquivo cria a classe principal que combina os mixins separados:
- Renomeação inteligente
- Geração de anexos e sumário

O objetivo é reduzir o tamanho do antigo `Documentaiser.py`.
"""


from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import re
from typing import Optional

# Garantir import do utils.py e dos módulos locais (fica em ../utils.py e no mesmo diretório dos mixins)
import sys
UTILS_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = Path(__file__).resolve().parent
if str(UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(UTILS_DIR))
if str(DOCS_DIR) not in sys.path:
    sys.path.insert(0, str(DOCS_DIR))

from renomeacao_inteligente import RenomeacaoInteligenteMixin
from geracao_anexos_sumario import GeracaoAnexosSumarioMixin



class DocumentaiserApp(RenomeacaoInteligenteMixin, GeracaoAnexosSumarioMixin):
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Documentaiser v3.0")
        self.root.geometry("1100x720")

        # Estado base UI
        self.selected_path = tk.StringVar(value="Nenhuma pasta selecionada")

        # --- Estado do módulo de renomeação inteligente (usado pelo mixin) ---
        self.ri_dir: Optional[Path] = None
        self.ri_pdf_files: list[Path] = []
        self.ri_idx: int = -1

        self.ri_selected_t1: Optional[str] = None
        self.ri_selected_ras_or_pub_kind: Optional[str] = None
        self.ri_selected_adt_number: Optional[int] = None

        self.ri_current_municipio: Optional[str] = None

        self.ri_undo_stack: list[tuple[Path, Path]] = []
        self.ri_used_names_in_session: set[str] = set()

        self.ri_last_confirmed_token: Optional[str] = None

        # --- Estado automação anexos/sumário ---
        self.auto_selected_empresa = tk.StringVar(value="RUDA")
        self.auto_municipios_cache: list[str] = []
        self.auto_preview_text_widget = None

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

        tk.Entry(path_frame, textvariable=self.selected_path, state="readonly").pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8)
        )
        tk.Button(path_frame, text="Navegar...", command=self.browse_folder).pack(side=tk.LEFT)

        # Separador
        tk.Frame(main_frame, height=2, bd=1, relief=tk.SUNKEN).pack(fill=tk.X, pady=14)

        # Grade 2 colunas
        canvas = tk.Canvas(main_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        grid = tk.Frame(canvas)
        grid_id = canvas.create_window((0, 0), window=grid, anchor="nw")

        def _on_frame_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        grid.bind("<Configure>", _on_frame_configure)

        def _on_canvas_resize(event):
            canvas.itemconfig(grid_id, width=event.width)

        canvas.bind("<Configure>", _on_canvas_resize)

        left = tk.Frame(grid)
        right = tk.Frame(grid)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # ====== “Acordeão” (seções recolhíveis) ======

        # Abre/fecha as duas seções sem usar abas (notebook). Como você pediu “retratéis”,
        # cada seção fica recolhível independentemente.
        acordeao_top = tk.Frame(right)
        acordeao_top.pack(fill=tk.BOTH, expand=True)

        # Containers que serão mostrados/escondidos
        self._accordion_frame_renomeacao = tk.Frame(acordeao_top)
        self._accordion_frame_auto = tk.Frame(acordeao_top)

        # Botões do acordeão
        self._accordion_btn_renomeacao = tk.Button(
            acordeao_top,
            text="▸ Renomeação Inteligente (Contratos)",
            anchor="w",
            command=self._toggle_accordion_renomeacao,
            relief=tk.GROOVE,
            padx=8,
            pady=6,
        )
        self._accordion_btn_renomeacao.pack(fill=tk.X)

        self._accordion_btn_auto = tk.Button(
            acordeao_top,
            text="▸ Geração de Anexos e Sumário",
            anchor="w",
            command=self._toggle_accordion_auto,
            relief=tk.GROOVE,
            padx=8,
            pady=6,
        )
        self._accordion_btn_auto.pack(fill=tk.X)

        # Estado inicial: Renomeação inteligente aberta, automação fechada
        self._accordion_show_renomeacao = True
        self._accordion_show_auto = False

        # ----- Renomeação Inteligente (conteúdo da seção) -----
        right_controls = tk.LabelFrame(self._accordion_frame_renomeacao, text="Renomeação Inteligente (Contratos)", padx=12, pady=12)
        right_controls.pack(fill=tk.BOTH, expand=True)


        module_top = tk.Frame(right_controls)
        module_top.pack(fill=tk.X)

        tk.Label(module_top, text="Pasta de PDFs (apenas nível da pasta):").pack(anchor=tk.W)

        module_dir_frame = tk.Frame(module_top)
        module_dir_frame.pack(fill=tk.X, pady=4)

        self.ri_dir_label = tk.Label(module_dir_frame, text="Nenhuma pasta escolhida", fg="#666")
        self.ri_dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(module_dir_frame, text="Selecionar...", command=self.ri_choose_dir).pack(side=tk.RIGHT)

        list_frame = tk.Frame(right_controls)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        tk.Label(list_frame, text="Arquivos .pdf disponíveis:").pack(anchor=tk.W)

        self.ri_listbox = tk.Listbox(list_frame, height=10)
        self.ri_listbox.pack(fill=tk.BOTH, expand=True, pady=6)
        self.ri_listbox.bind("<<ListboxSelect>>", self.ri_on_select_from_list)

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

        name_frame = tk.Frame(right_controls)
        name_frame.pack(fill=tk.X, pady=(8, 8))

        self.ri_lbl_original = tk.Label(name_frame, text="Nome Original: -", anchor="w")
        self.ri_lbl_original.pack(fill=tk.X)

        self.ri_lbl_new = tk.Label(name_frame, text="Novo Nome: -", anchor="w", font=("Arial", 10, "bold"))
        self.ri_lbl_new.pack(fill=tk.X, pady=(4, 0))

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

        t2_frame = tk.LabelFrame(right_controls, text="Etapas Complementares (T2)")
        t2_frame.pack(fill=tk.X, pady=(0, 8))

        self.ri_t2_container = tk.Frame(t2_frame)
        self.ri_t2_container.pack(fill=tk.X, padx=8, pady=8)

        self.ri_lbl_adt_suggestion = tk.Label(right_controls, text="", fg="#333")
        self.ri_lbl_adt_suggestion.pack(fill=tk.X)

        confirm_frame = tk.Frame(right_controls)
        confirm_frame.pack(fill=tk.X, pady=(10, 0))

        self.ri_btn_confirm = tk.Button(
            confirm_frame,
            text="✅ Confirmar Renomeação",
            height=2,
            bg="#28a745",
            fg="white",
            command=self.ri_confirm,
        )
        self.ri_btn_confirm.pack(side=tk.LEFT)

        self.ri_state_refresh()

        # ----- Automação anexos e sumário -----
        # (conteúdo da seção recolhível)
        auto_frame = tk.LabelFrame(self._accordion_frame_auto, text="GERAÇÃO DE ANEXOS E SUMÁRIO", padx=12, pady=10)


        auto_frame.pack(fill=tk.X, pady=(14, 0))

        empresa_box = tk.LabelFrame(auto_frame, text="EMPRESA RESPONSÁVEL", padx=10, pady=8)
        empresa_box.pack(fill=tk.X, pady=(0, 10))

        empresa_row = tk.Frame(empresa_box)
        empresa_row.pack(fill=tk.X)

        tk.Radiobutton(empresa_row, text="RUDA", variable=self.auto_selected_empresa, value="RUDA").pack(
            side=tk.LEFT, padx=10
        )
        tk.Radiobutton(empresa_row, text="HLA", variable=self.auto_selected_empresa, value="HLA").pack(
            side=tk.LEFT, padx=10
        )

        btns_frame = tk.Frame(auto_frame)
        btns_frame.pack(fill=tk.X)

        tk.Button(btns_frame, text="Validar Documentos", command=self._auto_validate_documents, height=2).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btns_frame, text="Visualizar Estrutura", command=self._auto_visualize_structure, height=2).pack(
            side=tk.LEFT, padx=5
        )

        btns_frame2 = tk.Frame(auto_frame)
        btns_frame2.pack(fill=tk.X, pady=(6, 0))

        tk.Button(btns_frame2, text="Gerar Anexos", command=self._auto_generate_anexos, height=2).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btns_frame2, text="Gerar Sumário", command=self._auto_generate_sumario, height=2).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(
            btns_frame2,
            text="Gerar Tudo",
            command=self._auto_generate_all,
            height=2,
            bg="#1e90ff",
            fg="white",
        ).pack(side=tk.LEFT, padx=5)

        tk.Label(auto_frame, text="Prévia textual (obrigatória):").pack(anchor=tk.W, pady=(10, 4))
        self.auto_preview_text_widget = tk.Text(auto_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.auto_preview_text_widget.pack(fill=tk.BOTH, expand=False)

        # aplica estado inicial do acordeão
        self._apply_accordion_state()

    def _toggle_accordion_renomeacao(self) -> None:
        self._accordion_show_renomeacao = not self._accordion_show_renomeacao
        self._apply_accordion_state()

    def _toggle_accordion_auto(self) -> None:
        self._accordion_show_auto = not self._accordion_show_auto
        self._apply_accordion_state()

    def _apply_accordion_state(self) -> None:
        # Renomeação
        if self._accordion_show_renomeacao:
            self._accordion_frame_renomeacao.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
            self._accordion_btn_renomeacao.config(text="▾ Renomeação Inteligente (Contratos)")
        else:
            self._accordion_frame_renomeacao.pack_forget()
            self._accordion_btn_renomeacao.config(text="▸ Renomeação Inteligente (Contratos)")

        # Automação
        if self._accordion_show_auto:
            self._accordion_frame_auto.pack(fill=tk.BOTH, expand=True, pady=(0, 12))
            self._accordion_btn_auto.config(text="▾ Geração de Anexos e Sumário")
        else:
            self._accordion_frame_auto.pack_forget()
            self._accordion_btn_auto.config(text="▸ Geração de Anexos e Sumário")

    # Utilitário existente (pode ficar no principal por enquanto)
    def browse_folder(self) -> None:

        directory = filedialog.askdirectory()
        if directory:
            self.selected_path.set(directory)

    # Métodos auxiliares que já existiam no Documentaiser.py (mantidos para não perder features)
    # Mantive apenas create_subfolder/organize_pdfs se você quiser depois podemos mover também.
    def create_subfolder(self) -> None:
        from tkinter import messagebox

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
        from tkinter import messagebox

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


if __name__ == "__main__":
    root = tk.Tk()
    app = DocumentaiserApp(root)
    root.mainloop()

