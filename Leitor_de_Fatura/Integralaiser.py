# ============================================================== #
# LAUNCHER DO INTEGRALAISER
# ============================================================== #

# Importa as bibliotecas
import sys
from pathlib import Path
import os
import tkinter as tk
from tkinter import messagebox, filedialog 
from tkinter import ttk 
import threading

# --- 1. LOCALIZAÇÃO E IMPORTAÇÃO DOS SCRIPTS (ESTRITAMENTE LOCAL) ---
if getattr(sys, "frozen", False):
    DIRETORIO_INSTALACAO = Path(sys.executable).resolve().parent 
else:
    DIRETORIO_INSTALACAO = Path(__file__).resolve().parent 

SCRIPTS_DIR = DIRETORIO_INSTALACAO / "Scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Importa as funções orquestradoras e os módulos para atualizar seus caminhos
try:
    import Cropper
    import Texter
    from Cropper import cropper_orchestrator
    from Texter import texter_orchestrator
except ModuleNotFoundError:
    root_erro = tk.Tk()
    root_erro.withdraw()
    messagebox.showerror("Erro de Dependência", f"Não foi possível encontrar a pasta 'Scripts' ou seus módulos em:\n{SCRIPTS_DIR}")
    sys.exit()


# --- 2. SELEÇÃO DO DIRETÓRIO DE TRABALHO DE DADOS PELO USUÁRIO ---
root_init = tk.Tk()
root_init.withdraw()

print("Aguardando usuário selecionar o Diretório de Trabalho (Dados)...")
pasta_selecionada = filedialog.askdirectory(
    title="Selecione a pasta master de Trabalho (Onde as pastas de Faturas serão lidas/criadas)"
)

if not pasta_selecionada:
    messagebox.showerror("Erro", "É necessário selecionar um Diretório de Trabalho para prosseguir. O programa será encerrado.")
    sys.exit()

# Define o Diretório base escolhido pelo usuário para os Dados
DIRETORIO_BASE = Path(pasta_selecionada).resolve()
root_init.destroy() 


# ============================================================== #
# CONFIGURAÇÕES DE CAMINHOS DINÂMICOS (Injeta nos módulos)
# ============================================================== #
PATH_FATURAS = DIRETORIO_BASE / "Faturas"
PATH_POPPLER = DIRETORIO_BASE / "Faturas_Poppler"

# Atualiza dinamicamente as configurações globais internas do Cropper.py
Cropper.PATH_FATURAS     = DIRETORIO_BASE / "Faturas"
Cropper.PATH_CROPPED     = DIRETORIO_BASE / "Faturas_Cropped"
Cropper.PATH_POPPLER     = DIRETORIO_BASE / "Faturas_Poppler"
Cropper.PATH_POPPLER_EXE = DIRETORIO_BASE / "poppler" / "Library" / "bin" / "pdftotext.exe"

# Atualiza dinamicamente as configurações globais internas do Texter.py
Texter.PATH_INPUT        = DIRETORIO_BASE / "Faturas_Poppler"
Texter.PATH_OUTPUT       = DIRETORIO_BASE / "Faturas_Texter"
Texter.PATH_ANALISE      = DIRETORIO_BASE / "Faturas_Analaiser"


# ============================================================== #
# FUNÇÕES
# ============================================================== #
def integralaiser_main(municipio_name: str, concessionaria_name: str):
    print(f"Iniciando o processo Integralaiser para {municipio_name} ({concessionaria_name})...")   
    cropper_orchestrator(municipio_name, concessionaria_name) 
    texter_orchestrator(municipio_name, concessionaria_name)  
    print("Processo Integralaiser concluído.")

# ============================================================== #
# INTERFACE GRÁFICA (GUI)
# ============================================================== #

class IntegralaiserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Integralaiser")
        self.root.geometry("550x520") 
        self.root.resizable(False, False)

        main_frame = tk.Frame(root, padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Integralaiser", font=("Arial", 16, "bold")).pack(pady=(0, 5))
        
        # Feedback visual para o usuário saber qual pasta de faturas está manipulando
        lbl_dir = tk.Label(main_frame, text=f"Diretório de Dados: {DIRETORIO_BASE}", font=("Arial", 8), fg="#666", wraplength=480)
        lbl_dir.pack(pady=(0, 15))
        
        # --- Seleção de Município ---
        tk.Label(main_frame, text="1. Selecione o Município:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.selected_municipio = tk.StringVar()
        self.municipio_combobox = ttk.Combobox(main_frame, textvariable=self.selected_municipio, state="readonly")
        self.municipio_combobox.pack(fill=tk.X, pady=5)
        self._populate_municipios()
        self.municipio_combobox.bind("<<ComboboxSelected>>", self._update_status_display)

        # --- Seleção de Concessionária ---
        tk.Label(main_frame, text="2. Selecione a Concessionária:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.selected_concessionaria = tk.StringVar()
        self.concessionaria_combobox = ttk.Combobox(main_frame, textvariable=self.selected_concessionaria, state="readonly")
        self.concessionaria_combobox.pack(fill=tk.X, pady=5)
        self._populate_concessionarias()
        self.concessionaria_combobox.bind("<<ComboboxSelected>>", self._update_status_display)

        # --- Seleção de Fluxo ---
        tk.Label(main_frame, text="3. Selecione o Fluxo Desejado:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(10, 0))
        self.opcao_fluxo = tk.StringVar(value="completo")
        
        tk.Radiobutton(main_frame, text="Apenas Cropper (Recorte de faturas)", 
                       variable=self.opcao_fluxo, value="cropper", command=self._update_status_display).pack(anchor=tk.W, pady=2)
        tk.Radiobutton(main_frame, text="Apenas Texter (Extração de dados)", 
                       variable=self.opcao_fluxo, value="texter", command=self._update_status_display).pack(anchor=tk.W, pady=2)
        tk.Radiobutton(main_frame, text="Fluxo Completo (Cropper + Texter)", 
                       variable=self.opcao_fluxo, value="completo", command=self._update_status_display).pack(anchor=tk.W, pady=2)

        # --- Barra de Progresso ---
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(15, 0))

        self.btn_executar = tk.Button(main_frame, text="EXECUTAR PROCESSO", bg="#28a745", fg="white", 
                                     font=("Arial", 11, "bold"), height=2, command=self.disparar_execucao)
        self.btn_executar.pack(fill=tk.X, pady=20)

        # --- Display de Status ---
        self.status_var = tk.StringVar(value="Aguardando seleção...")
        self.status_lbl = tk.Label(main_frame, textvariable=self.status_var, font=("Arial", 10, "italic"), fg="#555", wraplength=480, justify=tk.LEFT)
        self.status_lbl.pack(anchor=tk.W, pady=(5,0))
        
        self._update_status_display()

    def _populate_municipios(self):
        municipios = set()
        
        if PATH_FATURAS.exists():
            for item in PATH_FATURAS.iterdir():
                if item.is_dir():
                    municipios.add(item.name)
        
        if PATH_POPPLER.exists():
            for item in PATH_POPPLER.iterdir():
                if item.is_dir():
                    name = item.name.replace("_Poppler", "")
                    municipios.add(name)

        municipios_list = sorted(list(municipios))
        if not municipios_list:
            self.municipio_combobox['values'] = ["Nenhum município encontrado"]
            self.municipio_combobox.set("Nenhum município encontrado")
            self.municipio_combobox.config(state="disabled")
            messagebox.showwarning("Aviso", "Nenhum diretório de município encontrado nas pastas 'Faturas' ou 'Faturas_Poppler' do diretório selecionado.")
        else:
            self.municipio_combobox.config(state="readonly")
            self.municipio_combobox['values'] = municipios_list
            self.municipio_combobox.set(municipios_list[0])

    def _populate_concessionarias(self):
        concessionarias = ["NEOENERGIA", "ENEL", "ENERGISA"]
        self.concessionaria_combobox['values'] = sorted(concessionarias)
        self.concessionaria_combobox.set(concessionarias[0])

    def atualizar_status(self, msg):
        self.status_var.set(f"Status: {msg}")
        self.root.update_idletasks()

    def _update_status_display(self, event=None):
        municipio = self.selected_municipio.get()
        concessionaria = self.selected_concessionaria.get()
        fluxo = self.opcao_fluxo.get()

        fluxo_map = {
            "cropper": "Apenas Cropper",
            "texter": "Apenas Texter",
            "completo": "Fluxo Completo"
        }
        fluxo_display = fluxo_map.get(fluxo, "Desconhecido")

        status_msg = (
            f"Município: {municipio}\n"
            f"Concessionária: {concessionaria}\n"
            f"Fluxo: {fluxo_display}\n"
            f"Status: Pronto para iniciar."
        )
        self.status_var.set(status_msg)

    def disparar_execucao(self):
        self.btn_executar.config(state=tk.DISABLED)
        self.atualizar_status("Validando seleções...")

        municipio_selecionado = self.selected_municipio.get()
        concessionaria_selecionada = self.selected_concessionaria.get()

        if not municipio_selecionado or municipio_selecionado == "Nenhum município encontrado":
            messagebox.showwarning("Erro de Seleção", "Por favor, selecione um município válido.")
            self.btn_executar.config(state=tk.NORMAL)
            self.atualizar_status("Seleção de município pendente.")
            return
        
        if not concessionaria_selecionada:
            messagebox.showwarning("Erro de Seleção", "Por favor, selecione uma concessionária.")
            self.btn_executar.config(state=tk.NORMAL)
            self.atualizar_status("Seleção de concessionária pendente.")
            return

        threading.Thread(target=self.thread_processamento, 
                         args=(municipio_selecionado, concessionaria_selecionada), 
                         daemon=True).start()

    def _update_progress_callback(self, current, total, message=None):
        self.root.after(0, lambda: self.progress.config(maximum=total if total > 0 else 1))
        self.root.after(0, lambda: self.progress.config(value=current))
        if message:
            self.root.after(0, lambda: self.atualizar_status(message))

    def thread_processamento(self, municipio_name: str, concessionaria_name: str):
        escolha = self.opcao_fluxo.get()
        import time 
        start_total = time.time()
        
        try:
            resumo_tempos = ""
            if escolha == "cropper":
                self.atualizar_status(f"Executando Cropper para {municipio_name} ({concessionaria_name})...")
                start_p = time.time()
                cropper_orchestrator(municipio_name, concessionaria_name, progress_callback=self._update_progress_callback)
                dur = time.time() - start_p
                resumo_tempos = f"Tempo Cropper: {dur:.2f}s"
            elif escolha == "texter":
                self.atualizar_status(f"Executando Texter para {municipio_name} ({concessionaria_name})...")
                start_p = time.time()
                texter_orchestrator(municipio_name, concessionaria_name, progress_callback=self._update_progress_callback)
                dur = time.time() - start_p
                resumo_tempos = f"Tempo Texter: {dur:.2f}s"
            else:
                self.atualizar_status(f"Executando Fluxo Completo para {municipio_name} ({concessionaria_name})...")
                
                self._update_progress_callback(0, 100, "Executando Etapa 1/2: Cropper...") 
                start_c = time.time()
                cropper_orchestrator(municipio_name, concessionaria_name, progress_callback=self._update_progress_callback)
                dur_c = time.time() - start_c
                
                self._update_progress_callback(0, 100, "Executando Etapa 2/2: Texter...") 
                start_t = time.time()
                texter_orchestrator(municipio_name, concessionaria_name, progress_callback=self._update_progress_callback)
                dur_t = time.time() - start_t
                resumo_tempos = f"Cropper: {dur_c:.2f}s | Texter: {dur_t:.2f}s"
            
            total_dur = time.time() - start_total
            self.atualizar_status(f"Concluído! Total: {total_dur:.2f}s\n{resumo_tempos}")
            messagebox.showinfo("Sucesso", f"O processamento foi finalizado com sucesso.\n\n{resumo_tempos}\nTempo Total Acumulado: {total_dur:.2f}s")
        except Exception as e:
            self.atualizar_status(f"Erro na execução: {e}")
            messagebox.showerror("Erro", f"Ocorreu uma falha durante o processo:\n{e}")            
        finally:
            self.root.after(0, lambda: self.progress.config(value=0, maximum=100)) 
            self.root.after(0, lambda: self.btn_executar.config(state=tk.NORMAL))

if __name__ == "__main__":
    root = tk.Tk()
    app = IntegralaiserGUI(root)
    root.mainloop()