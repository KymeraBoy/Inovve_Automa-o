import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from Cropper import PATH_CROPPED, PATH_FATURAS, PATH_POPPLER, TEMPLATES, listar_pdfs_disponiveis, processar_cropper
from Texter import PATH_ANALISE, PATH_INPUT, PATH_OUTPUT, FORMATADORES, listar_txts_disponiveis, processar_texter


APP_TITLE = "Integralaiser"
APP_SUBTITLE = "Recorte, formatação e geração de planilhas com fluxo visual e sem terminal."

COLOR_BG = "#F4F7FB"
COLOR_PANEL = "#FFFFFF"
COLOR_PRIMARY = "#1F4E78"
COLOR_PRIMARY_DARK = "#173A5A"
COLOR_ACCENT = "#5B9BD5"
COLOR_TEXT = "#1F2937"
COLOR_MUTED = "#667085"
COLOR_SUCCESS = "#1F7A3D"
COLOR_WARNING = "#B54708"
COLOR_ERROR = "#B42318"


def _abrir_pasta(caminho):
    if not caminho:
        return
    os.startfile(str(caminho))


def _abrir_arquivo(caminho):
    if not caminho:
        return
    os.startfile(str(caminho))


class StagePanel(ttk.Frame):
    def __init__(self, master, app, *, titulo, descricao, origem_padrao, extensoes, modo):
        super().__init__(master, padding=16)
        self.app = app
        self.titulo = titulo
        self.descricao = descricao
        self.origem_padrao = Path(origem_padrao)
        self.extensoes = {ext.lower() for ext in extensoes}
        self.modo = modo

        self.source_dir = None
        self.loaded_files = []
        self.last_result = None
        self.worker_queue = queue.Queue()
        self.busy = False

        self.path_var = tk.StringVar(value="Nenhuma pasta selecionada")
        self.status_var = tk.StringVar(value="Pronto")
        self.percent_var = tk.StringVar(value="0%")
        self.detail_var = tk.StringVar(value="")
        self.progress_var = tk.IntVar(value=0)

        self._build_ui()
        self._poll_queue()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)

        fluxo = ttk.LabelFrame(self, text="Fluxo", padding=12)
        fluxo.grid(row=0, column=0, columnspan=2, sticky="ew")
        fluxo.columnconfigure(0, weight=1)
        fluxo.columnconfigure(1, weight=1)
        fluxo.columnconfigure(2, weight=1)
        fluxo.columnconfigure(3, weight=1)
        fluxo.columnconfigure(4, weight=1)

        etapas = [
            ("1", "Selecionar", "Escolha pasta ou arquivos."),
            ("2", "Validar", "Confere o que será processado."),
            ("3", "Processar", "Executa recorte e formatação."),
            ("4", "Gerar", "Cria os TXT e a planilha." if self.modo == "texter" else "Gera os PDFs e TXT."),
            ("5", "Exportar", "Abre saída e relatório final."),
        ]

        for coluna, (numero, titulo, texto) in enumerate(etapas):
            card = ttk.Frame(fluxo, padding=8, style="Card.TFrame")
            card.grid(row=0, column=coluna, padx=6, sticky="nsew")
            ttk.Label(card, text=numero, style="StepNumber.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Label(card, text=titulo, style="StepTitle.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
            ttk.Label(card, text=texto, style="StepText.TLabel", wraplength=150, justify="left").grid(row=2, column=0, sticky="w", pady=(2, 8))

        entrada = ttk.LabelFrame(self, text="Entrada de dados", padding=12)
        entrada.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(14, 0))
        entrada.columnconfigure(0, weight=1)

        topo = ttk.Frame(entrada)
        topo.grid(row=0, column=0, sticky="ew")
        topo.columnconfigure(0, weight=1)
        ttk.Label(topo, textvariable=self.path_var, style="Path.TLabel").grid(row=0, column=0, sticky="w")
        botoes_topo = ttk.Frame(topo)
        botoes_topo.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Button(botoes_topo, text="Escolher Pasta", command=self.choose_folder).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(botoes_topo, text="Escolher Arquivos", command=self.choose_files).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(botoes_topo, text="Remover da Lista", command=self.remove_selected_from_list).grid(row=0, column=2)

        lista_frame = ttk.Frame(entrada)
        lista_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        lista_frame.columnconfigure(0, weight=1)
        lista_frame.rowconfigure(0, weight=1)
        self.file_list = tk.Listbox(
            lista_frame,
            selectmode=tk.EXTENDED,
            height=14,
            activestyle="dotbox",
            bg="#FFFFFF",
            fg=COLOR_TEXT,
            highlightthickness=1,
            relief="flat",
            selectbackground=COLOR_ACCENT,
            selectforeground="#FFFFFF",
        )
        scroll = ttk.Scrollbar(lista_frame, orient="vertical", command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scroll.set)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        config = ttk.LabelFrame(self, text="Configurações", padding=12)
        config.grid(row=1, column=1, sticky="nsew", pady=(14, 0))
        config.columnconfigure(1, weight=1)

        ttk.Label(config, text="Origem padrão", style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(config, text=str(self.origem_padrao), style="Value.TLabel", wraplength=360).grid(row=0, column=1, sticky="w")

        ttk.Label(config, text="Status", style="FieldLabel.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.status_label = ttk.Label(config, textvariable=self.status_var, style="StatusReady.TLabel")
        self.status_label.grid(row=1, column=1, sticky="w", pady=(10, 0))

        if self.modo == "cropper":
            ttk.Label(config, text="Modelo", style="FieldLabel.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))
            self.template_var = tk.StringVar(value=next(iter(TEMPLATES.keys())))
            self.template_combo = ttk.Combobox(config, textvariable=self.template_var, values=list(TEMPLATES.keys()), state="readonly")
            self.template_combo.grid(row=2, column=1, sticky="ew", pady=(12, 0))
            self.convert_txt_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(config, text="Gerar TXT do Poppler", variable=self.convert_txt_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))
            self.clean_output_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(config, text="Manter saídas anteriores", variable=self.clean_output_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))
        else:
            ttk.Label(config, text="Formato", style="FieldLabel.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))
            self.format_var = tk.StringVar(value=next(iter(FORMATADORES.keys())))
            self.format_combo = ttk.Combobox(config, textvariable=self.format_var, values=list(FORMATADORES.keys()), state="readonly")
            self.format_combo.grid(row=2, column=1, sticky="ew", pady=(12, 0))
            self.clean_output_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(config, text="Limpar pasta de saída antes de gerar", variable=self.clean_output_var).grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 0))
            self.open_report_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(config, text="Abrir planilha ao concluir", variable=self.open_report_var).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        execucao = ttk.LabelFrame(self, text="Execução", padding=12)
        execucao.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        execucao.columnconfigure(0, weight=1)

        botoes = ttk.Frame(execucao)
        botoes.grid(row=0, column=0, sticky="w")
        ttk.Button(botoes, text="Validar", command=self.validate_selection).grid(row=0, column=0, padx=(0, 8))
        self.start_button = ttk.Button(botoes, text="Iniciar Processamento", command=self.start_processing)
        self.start_button.grid(row=0, column=1, padx=(0, 8))
        self.open_output_button = ttk.Button(botoes, text="Abrir Pasta de Saída", command=self.open_output_folder, state="disabled")
        self.open_output_button.grid(row=0, column=2, padx=(0, 8))
        self.open_report_button = ttk.Button(botoes, text="Visualizar Relatório", command=self.open_report, state="disabled")
        self.open_report_button.grid(row=0, column=3)

        progresso = ttk.Frame(execucao)
        progresso.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        progresso.columnconfigure(0, weight=1)
        self.progress = ttk.Progressbar(progresso, variable=self.progress_var, maximum=100)
        self.progress.grid(row=0, column=0, sticky="ew")
        ttk.Label(progresso, textvariable=self.percent_var, style="Percent.TLabel").grid(row=0, column=1, padx=(10, 0))

        self.detail_label = ttk.Label(execucao, textvariable=self.detail_var, style="Detail.TLabel")
        self.detail_label.grid(row=2, column=0, sticky="w", pady=(8, 0))

        log_frame = ttk.LabelFrame(self, text="Registro de atividades", padding=12)
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=10, wrap="word", bg="#FFFFFF", fg=COLOR_TEXT, relief="flat", state="disabled")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        result = ttk.LabelFrame(self, text="Resultados", padding=12)
        result.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        result.columnconfigure(1, weight=1)

        self.result_status_var = tk.StringVar(value="Aguardando execução.")
        self.result_summary_var = tk.StringVar(value="")
        self.result_output_var = tk.StringVar(value="")
        ttk.Label(result, text="Situação", style="FieldLabel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(result, textvariable=self.result_status_var, style="Value.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(result, text="Resumo", style="FieldLabel.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Label(result, textvariable=self.result_summary_var, style="Value.TLabel", wraplength=700).grid(row=1, column=1, sticky="w", pady=(8, 0))
        ttk.Label(result, text="Saída", style="FieldLabel.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Label(result, textvariable=self.result_output_var, style="Value.TLabel", wraplength=700).grid(row=2, column=1, sticky="w", pady=(8, 0))

    def _set_status(self, text, kind="ready"):
        self.status_var.set(text)
        styles = {
            "ready": "StatusReady.TLabel",
            "working": "StatusWorking.TLabel",
            "done": "StatusDone.TLabel",
            "error": "StatusError.TLabel",
        }
        self.status_label.configure(style=styles.get(kind, "StatusReady.TLabel"))
        self.app.set_global_status(text, kind)

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _refresh_listbox(self):
        self.file_list.delete(0, "end")
        for nome in self.loaded_files:
            self.file_list.insert("end", nome)

    def choose_folder(self):
        initial = str(self.origem_padrao if self.source_dir is None else self.source_dir)
        folder = filedialog.askdirectory(title="Escolher pasta", initialdir=initial)
        if not folder:
            return
        self.load_folder(Path(folder))

    def choose_files(self):
        initial = str(self.source_dir or self.origem_padrao)
        if self.modo == "cropper":
            files = filedialog.askopenfilenames(title="Escolher PDFs", initialdir=initial, filetypes=[("PDF", "*.pdf")])
        else:
            files = filedialog.askopenfilenames(title="Escolher TXT", initialdir=initial, filetypes=[("TXT", "*.txt")])
        if not files:
            return

        parents = {Path(file_name).parent.resolve() for file_name in files}
        if len(parents) != 1:
            messagebox.showerror("Arquivos inválidos", "Escolha arquivos da mesma pasta para processar em lote.")
            return

        self.load_folder(next(iter(parents)), list(files))

    def load_folder(self, folder, explicit_files=None):
        self.source_dir = Path(folder)
        if explicit_files is None:
            if self.modo == "cropper":
                self.loaded_files = listar_pdfs_disponiveis(self.source_dir)
            else:
                self.loaded_files = listar_txts_disponiveis(self.source_dir)
        else:
            self.loaded_files = [Path(file_name).name for file_name in explicit_files]

        self.path_var.set(str(self.source_dir))
        self._refresh_listbox()
        self.detail_var.set(f"{len(self.loaded_files)} arquivo(s) carregado(s).")
        self._set_status("Arquivos carregados", "ready")

    def remove_selected_from_list(self):
        selected = list(self.file_list.curselection())
        if not selected:
            return
        for index in reversed(selected):
            del self.loaded_files[index]
        self._refresh_listbox()
        self.detail_var.set(f"{len(self.loaded_files)} arquivo(s) permanecem na lista.")

    def validate_selection(self):
        if self.source_dir is None:
            messagebox.showwarning("Seleção ausente", "Escolha uma pasta ou arquivos antes de validar.")
            self._set_status("Aguardando seleção", "warning")
            return False
        if not self.loaded_files:
            messagebox.showwarning("Lista vazia", "A lista está vazia. Carregue arquivos para continuar.")
            self._set_status("Lista vazia", "warning")
            return False
        self._set_status("Dados validados", "ready")
        self._log("✓ Arquivos carregados e prontos para processamento")
        return True

    def start_processing(self):
        if self.busy:
            return
        if not self.validate_selection():
            return

        self.busy = True
        self.start_button.configure(state="disabled")
        self.open_output_button.configure(state="disabled")
        self.open_report_button.configure(state="disabled")
        self.progress_var.set(0)
        self.percent_var.set("0%")
        self.result_status_var.set("Processando...")
        self.result_summary_var.set("")
        self.result_output_var.set("")
        self._set_status("Processando", "working")
        self._log("⏳ Iniciando processamento")

        selected_files = list(self.loaded_files)
        source_dir = self.source_dir

        def progress_callback(current, total, file_name):
            self.worker_queue.put(("progress", current, total, file_name))

        def log_callback(message):
            self.worker_queue.put(("log", message))

        def worker():
            try:
                if self.modo == "cropper":
                    template_name = self.template_var.get()
                    resultado = processar_cropper(
                        source_dir,
                        template_name,
                        TEMPLATES[template_name],
                        selected_files=selected_files,
                        progress_callback=progress_callback,
                        log_callback=log_callback,
                        gerar_txt=self.convert_txt_var.get(),
                        limpar_saida=not self.clean_output_var.get(),
                    )
                else:
                    format_name = self.format_var.get()
                    resultado = processar_texter(
                        source_dir,
                        format_name,
                        selected_files=selected_files,
                        limpar_saida=self.clean_output_var.get(),
                        progress_callback=progress_callback,
                        log_callback=log_callback,
                    )
                self.worker_queue.put(("done", resultado))
            except Exception as exc:
                self.worker_queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self):
        try:
            while True:
                item = self.worker_queue.get_nowait()
                tipo = item[0]

                if tipo == "log":
                    self._log(item[1])

                elif tipo == "progress":
                    _, current, total, file_name = item
                    percent = int((current / total) * 100) if total else 0
                    self.progress_var.set(percent)
                    self.percent_var.set(f"{percent}%")
                    self.detail_var.set(f"{current}/{total} - {file_name}")

                elif tipo == "done":
                    self.last_result = item[1]
                    self.busy = False
                    self.start_button.configure(state="normal")
                    self.open_output_button.configure(state="normal")
                    self.open_report_button.configure(state="normal" if self.modo == "texter" else "normal")
                    self.progress_var.set(100)
                    self.percent_var.set("100%")
                    self._finish_success(item[1])

                elif tipo == "error":
                    self.busy = False
                    self.start_button.configure(state="normal")
                    self.open_output_button.configure(state="disabled")
                    self.open_report_button.configure(state="disabled")
                    self._finish_error(item[1])

        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _finish_success(self, resultado):
        self._set_status("Concluído", "done")
        if self.modo == "cropper":
            self.result_status_var.set("Processamento concluído com sucesso.")
            self.result_summary_var.set(
                f"{resultado.get('processados', 0)} arquivo(s) processado(s) | {resultado.get('sucesso', 0)} com saída gerada | {resultado.get('falhas', 0)} falha(s)."
            )
            self.result_output_var.set(f"PDFs: {resultado.get('cropped_dir')} | TXT: {resultado.get('poppler_dir')}")
            self.open_output_button.configure(state="normal")
            self.open_report_button.configure(state="normal")
        else:
            self.result_status_var.set("Planilha gerada com sucesso.")
            self.result_summary_var.set(f"{resultado.get('processados', 0)} arquivo(s) formatado(s).")
            self.result_output_var.set(f"Saída: {resultado.get('destino')} | Planilha: {resultado.get('planilha')}")
            self.open_output_button.configure(state="normal")
            self.open_report_button.configure(state="normal")

        self._log("✓ Processamento concluído")

    def _finish_error(self, mensagem):
        self._set_status("Erro", "error")
        self.result_status_var.set("Ocorreu um erro durante o processamento.")
        self.result_summary_var.set(mensagem)
        self.result_output_var.set("")
        self._log(f"✗ Erro: {mensagem}")
        messagebox.showerror("Erro", mensagem)

    def open_output_folder(self):
        if not self.last_result:
            return
        if self.modo == "cropper":
            _abrir_pasta(self.last_result.get("cropped_dir"))
        else:
            _abrir_pasta(self.last_result.get("destino"))

    def open_report(self):
        if not self.last_result:
            return
        if self.modo == "cropper":
            _abrir_pasta(self.last_result.get("poppler_dir"))
        else:
            _abrir_arquivo(self.last_result.get("planilha"))


class IntegralaiserApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1280x920")
        self.minsize(1120, 780)
        self.configure(bg=COLOR_BG)

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure("Card.TFrame", background="#F8FAFC", relief="flat")
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 24))
        style.configure("Subtitle.TLabel", background=COLOR_BG, foreground=COLOR_MUTED, font=("Segoe UI", 10))
        style.configure("StatusReady.TLabel", background="#E8F1FB", foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 10), padding=(10, 4))
        style.configure("StatusWorking.TLabel", background="#D6E9FB", foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 10), padding=(10, 4))
        style.configure("StatusDone.TLabel", background="#E7F6EC", foreground=COLOR_SUCCESS, font=("Segoe UI Semibold", 10), padding=(10, 4))
        style.configure("StatusError.TLabel", background="#FDECEC", foreground=COLOR_ERROR, font=("Segoe UI Semibold", 10), padding=(10, 4))
        style.configure("StepNumber.TLabel", background="#EAF1F8", foreground=COLOR_PRIMARY, font=("Segoe UI Semibold", 11), padding=(8, 4))
        style.configure("StepTitle.TLabel", background="#F8FAFC", foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 11))
        style.configure("StepText.TLabel", background="#F8FAFC", foreground=COLOR_MUTED, font=("Segoe UI", 9))
        style.configure("FieldLabel.TLabel", background=COLOR_PANEL, foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 10))
        style.configure("Value.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT, font=("Segoe UI", 10))
        style.configure("Path.TLabel", background=COLOR_PANEL, foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 10))
        style.configure("Percent.TLabel", background=COLOR_PANEL, foreground=COLOR_PRIMARY_DARK, font=("Segoe UI Semibold", 10))
        style.configure("Detail.TLabel", background=COLOR_PANEL, foreground=COLOR_MUTED, font=("Segoe UI", 9))
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 10), font=("Segoe UI Semibold", 10))
        style.configure("TButton", padding=(12, 8), font=("Segoe UI Semibold", 10))
        style.configure("TCheckbutton", background=COLOR_PANEL, font=("Segoe UI", 10))
        style.configure("TCombobox", padding=6)

    def _build_ui(self):
        header = ttk.Frame(self, padding=(24, 20), style="Panel.TFrame")
        header.pack(fill="x", padx=16, pady=16)
        header.columnconfigure(0, weight=1)

        left = ttk.Frame(header, style="Panel.TFrame")
        left.grid(row=0, column=0, sticky="w")
        ttk.Label(left, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(left, text=APP_SUBTITLE, style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))

        right = ttk.Frame(header, style="Panel.TFrame")
        right.grid(row=0, column=1, sticky="e")
        ttk.Label(right, text="Status", style="FieldLabel.TLabel").grid(row=0, column=0, sticky="e")
        self.global_status = ttk.Label(right, text="Pronto", style="StatusReady.TLabel")
        self.global_status.grid(row=1, column=0, sticky="e", pady=(6, 0))

        container = ttk.Frame(self, padding=(16, 0, 16, 16))
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(container)
        notebook.grid(row=0, column=0, sticky="nsew")

        self.cropper_panel = StagePanel(
            notebook,
            self,
            titulo="Cropper",
            descricao="Recorte e conversão dos PDFs originais.",
            origem_padrao=PATH_FATURAS,
            extensoes={".pdf"},
            modo="cropper",
        )
        self.texter_panel = StagePanel(
            notebook,
            self,
            titulo="Texter",
            descricao="Formatação dos TXT do Poppler e geração da planilha.",
            origem_padrao=PATH_INPUT,
            extensoes={".txt"},
            modo="texter",
        )

        notebook.add(self.cropper_panel, text="Cropper")
        notebook.add(self.texter_panel, text="Texter")

        footer = ttk.Frame(self, padding=(16, 0, 16, 12))
        footer.pack(fill="x")
        ttk.Label(
            footer,
            text=f"Saídas: {PATH_CROPPED} | {PATH_POPPLER} | {PATH_OUTPUT} | {PATH_ANALISE}",
            style="Subtitle.TLabel",
            wraplength=1200,
        ).pack(anchor="w")

    def set_global_status(self, text, kind):
        styles = {
            "ready": "StatusReady.TLabel",
            "working": "StatusWorking.TLabel",
            "done": "StatusDone.TLabel",
            "error": "StatusError.TLabel",
            "warning": "StatusReady.TLabel",
        }
        self.global_status.configure(text=text, style=styles.get(kind, "StatusReady.TLabel"))


def run_app():
    app = IntegralaiserApp()
    app.mainloop()
