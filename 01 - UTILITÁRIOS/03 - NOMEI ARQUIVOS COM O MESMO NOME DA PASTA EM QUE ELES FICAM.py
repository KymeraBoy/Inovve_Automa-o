import tkinter as tk
from tkinter import messagebox
from pathlib import Path

def listar_arquivos(base_dir: Path) -> list[Path]:
	"""Lista arquivos na pasta ignorando o próprio script."""
	return [
		caminho
		for caminho in sorted(base_dir.iterdir(), key=lambda item: item.name.lower())
		if caminho.is_file() and caminho.name != Path(__file__).name
	]

class RenomeadorGUI:
	def __init__(self, root):
		self.root = root
		self.root.title("Renomeador Visual")
		self.root.geometry("600x500")
		self.base_dir = Path(__file__).resolve().parent
		self.arquivos_selecionados = set()
		self.botoes_arquivos = []

		# Título e Instrução
		tk.Label(root, text=f"Pasta: {self.base_dir.name}", font=("Arial", 10, "italic")).pack(pady=5)
		tk.Label(root, text="Selecione os arquivos para renomear:", font=("Arial", 12, "bold")).pack(pady=10)

		# Área de arquivos com rolagem
		container = tk.Frame(root)
		container.pack(fill=tk.BOTH, expand=True, padx=20)

		self.canvas = tk.Canvas(container)
		scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
		self.scrollable_frame = tk.Frame(self.canvas)

		self.scrollable_frame.bind(
			"<Configure>",
			lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
		)

		self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
		self.canvas.configure(yscrollcommand=scrollbar.set)
		self.canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		self.carregar_arquivos()

		# Frame para Botões de Ação
		frame_botoes = tk.Frame(root)
		frame_botoes.pack(pady=20, fill=tk.X, padx=50)

		self.btn_confirmar = tk.Button(
			frame_botoes, text="RENOMEAR: PADRÃO PASTA", font=("Arial", 10, "bold"),
			bg="#28a745", fg="white", height=2, state=tk.DISABLED,
			command=lambda: self.executar_renomeacao(memorial=False)
		)
		self.btn_confirmar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

		self.btn_memorial = tk.Button(
			frame_botoes, text="RENOMEAR: MEMORIAL", font=("Arial", 10, "bold"),
			bg="#17a2b8", fg="white", height=2, state=tk.DISABLED,
			command=lambda: self.executar_renomeacao(memorial=True)
		)
		self.btn_memorial.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

	def carregar_arquivos(self):
		arquivos = listar_arquivos(self.base_dir)
		colunas = 3
		for i, arq in enumerate(arquivos):
			# Criar um "ícone" clicável (Botão com emoji)
			btn = tk.Button(
				self.scrollable_frame, text=f"📄\n{arq.name}", 
				width=15, height=4, wraplength=100
			)
			btn.config(command=lambda a=arq, b=btn: self.selecionar_arquivo(a, b))
			btn.grid(row=i // colunas, column=i % colunas, padx=10, pady=10)
			self.botoes_arquivos.append((btn, arq))

	def selecionar_arquivo(self, arquivo, botao):
		if arquivo in self.arquivos_selecionados:
			self.arquivos_selecionados.remove(arquivo)
			botao.config(bg="SystemButtonFace", fg="black")
		else:
			self.arquivos_selecionados.add(arquivo)
			botao.config(bg="#007bff", fg="white") # Destaque azul
		
		if self.arquivos_selecionados:
			self.btn_confirmar.config(state=tk.NORMAL)
			self.btn_memorial.config(state=tk.NORMAL)
		else:
			self.btn_confirmar.config(state=tk.DISABLED)
			self.btn_memorial.config(state=tk.DISABLED)

	def executar_renomeacao(self, memorial=False):
		sucessos = 0
		erros = []
		pasta_nome = self.base_dir.name
		
		# Ordena para garantir que a numeração siga a ordem alfabética original
		lista_arquivos = sorted(list(self.arquivos_selecionados), key=lambda x: x.name.lower())

		for arquivo in lista_arquivos:
			contador = 1
			while True:
				# Define o nome: Pasta.ext, Pasta_2.ext, Pasta_3.ext...
				sufixo = f"_{contador}" if contador > 1 else ""
				prefixo = "MEMORIAL DE CÁLCULO - " if memorial else ""
				pasta_nome = pasta_nome.split('-')
				novo_nome = f"{prefixo}{pasta_nome[2]} - {pasta_nome[0] + "  " + pasta_nome[1]}{sufixo}{arquivo.suffix}"
				destino = arquivo.with_name(novo_nome)
				
				if destino == arquivo: # Já está renomeado corretamente
					sucessos += 1
					break
				
				if not destino.exists():
					try:
						arquivo.rename(destino)
						sucessos += 1
						break
					except Exception as e:
						erros.append(f"{arquivo.name}: {e}")
						break
				contador += 1

		if erros:
			messagebox.showwarning("Processo Concluído", f"Arquivos renomeados: {sucessos}\nErros encontrados:\n" + "\n".join(erros))
		else:
			messagebox.showinfo("Sucesso", f"{sucessos} arquivos foram renomeados com sucesso!")
		
		self.root.destroy()

if __name__ == "__main__":
	root = tk.Tk()
	app = RenomeadorGUI(root)
	root.mainloop()
