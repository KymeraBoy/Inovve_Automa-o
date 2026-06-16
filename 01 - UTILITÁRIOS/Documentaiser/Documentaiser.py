import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import re

class Documentaiser:
    def __init__(self, root):
        self.root = root
        self.root.title("Documentaiser v3.0")
        self.root.geometry("600x400")
        
        # Estado do programa
        self.selected_path = tk.StringVar(value="Nenhuma pasta selecionada")
        
        self._setup_ui()

    def _setup_ui(self):
        """Configura os elementos visuais da interface."""
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Seção de Seleção
        tk.Label(main_frame, text="Diretório de Trabalho:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        path_frame = tk.Frame(main_frame, pady=5)
        path_frame.pack(fill=tk.X)
        
        tk.Entry(path_frame, textvariable=self.selected_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        tk.Button(path_frame, text="Navegar...", command=self.browse_folder).pack(side=tk.RIGHT)

        tk.Separator = tk.Frame(main_frame, height=2, bd=1, relief=tk.SUNKEN)
        tk.Separator.pack(fill=tk.X, pady=20)

        # Seção de Ações
        tk.Label(main_frame, text="Ações Disponíveis:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        actions_frame = tk.Frame(main_frame, pady=10)
        actions_frame.pack(fill=tk.X)

        # Botão para criar pasta
        self.btn_create_folder = tk.Button(
            actions_frame, 
            text="📁 Criar Nova Pasta", 
            command=self.create_subfolder,
            height=2,
            width=20,
            bg="#e1e1e1"
        )
        self.btn_create_folder.pack(side=tk.LEFT)

    def browse_folder(self):
        """Abre o explorador para selecionar uma pasta."""
        directory = filedialog.askdirectory()
        if directory:
            self.selected_path.set(directory)

    def create_subfolder(self):
        """Cria as pastas padrão e renomeia versões similares usando regex."""
        current_dir = self.selected_path.get()

        if current_dir == "Nenhuma pasta selecionada":
            messagebox.showwarning("Aviso", "Por favor, selecione uma pasta primeiro!")
            return

        # nomes padrão
        standard_folders = [
            "ANEEL",
            "DOCUMENTOS RECEBIDOS",
            "PAGAMENTOS",
            "RECLAMAÇÃO FORMAL",
            "E-MAILS"
        ]

        # cria padrões regex para aceitar variações ( _, -, espaços, case-insensitive )
        def to_regex(name):
            pattern = re.sub(r"[\s_-]+", r"[\s_-]*", name.strip())
            return re.compile(f"^{pattern}$", re.IGNORECASE)

        try:
            existing_dirs = [p for p in Path(current_dir).iterdir() if p.is_dir()]

            for standard in standard_folders:
                regex = to_regex(standard)

                # verifica se já existe alguma variação do nome
                matched_folder = None

                for folder in existing_dirs:
                    if regex.match(folder.name):
                        matched_folder = folder
                        break

                target_path = Path(current_dir) / standard

                if matched_folder:
                    # renomeia se necessário (normaliza para padrão)
                    if matched_folder.name != standard:
                        matched_folder.rename(target_path)
                else:
                    # cria se não existir
                    target_path.mkdir(exist_ok=True)

            messagebox.showinfo(
                "Sucesso",
                "Pastas normalizadas e criadas com sucesso!"
            )

        except Exception as e:
            messagebox.showerror(
                "Erro",
                f"Erro ao processar pastas: {e}"
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = Documentaiser(root)
    root.mainloop()