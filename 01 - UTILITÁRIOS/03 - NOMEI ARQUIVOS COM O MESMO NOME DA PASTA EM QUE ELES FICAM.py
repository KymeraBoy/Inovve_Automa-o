import tkinter as tk
from tkinter import messagebox
from pathlib import Path


PASTAS_PADRAO = [
	"ANEEL",
	"DOCUMENTOS_RECEBIDOS",
	"PAGAMENTO",
	"E-MAILS",
	"RECLAMACAO_FORMAL",
]
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
		self.root.geometry("1000x500")
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

		self.btn_reclamacao = tk.Button(
			frame_botoes, text="RENOMEAR: PADRÃO RECLAMAÇÃO", font=("Arial", 10, "bold"),
			bg="#28a745", fg="white", height=2, state=tk.DISABLED,
			width=25, command=lambda: self.executar_renomeacao(memorial=False)
		)
		self.btn_reclamacao.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

		self.btn_memorial = tk.Button(
			frame_botoes, text="RENOMEAR: MEMORIAL", font=("Arial", 10, "bold"),
			bg="#17a2b8", fg="white", height=2, state=tk.DISABLED,
			width=25, command=lambda: self.executar_renomeacao(memorial=True)
		)
		self.btn_memorial.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

		self.btn_comprovante = tk.Button(
			frame_botoes, text="RENOMEAR: PAGAMENTO", font=("Arial", 10, "bold"),
			bg="#ff9900", fg="white", height=2, state=tk.DISABLED,
			width=25, command=lambda: self.executar_renomeacao(comprovante=True)
		)
		self.btn_comprovante.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

		self.btn_subpastas = tk.Button(
			frame_botoes, text="CRIAR: SUBPASTAS", font=("Arial", 10, "bold"),
			bg="#174489", fg="white", height=2, state=tk.NORMAL,
			width=25, command=self.criar_subpastas
		)
		self.btn_subpastas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

	def carregar_arquivos(self):
		# Limpa a visualização atual antes de carregar
		for widget in self.scrollable_frame.winfo_children():
			widget.destroy()
		self.botoes_arquivos = []

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
			self.btn_reclamacao.config(state=tk.NORMAL)
			self.btn_memorial.config(state=tk.NORMAL)
		else:
			self.btn_reclamacao.config(state=tk.DISABLED)
			self.btn_memorial.config(state=tk.DISABLED)
			self.btn_comprovante.config(state=tk.DISABLED)

	def executar_renomeacao(self, memorial=False, comprovante=False):
		sucessos = 0
		erros = []
		
		folder_full_name = self.base_dir.name
		
		# Ordena para garantir que a numeração siga a ordem alfabética original
		lista_arquivos = sorted(list(self.arquivos_selecionados), key=lambda x: x.name.lower())

		for arquivo in lista_arquivos:
			contador = 1
			while True:
				# Define o nome: Pasta.ext, Pasta_2.ext, Pasta_3.ext...
				sufixo = f"_{contador}" if contador > 1 else ""
				
				if not memorial and not comprovante:
					# Para btn_reclamacao (memorial=False), renomeia para o nome completo da pasta
					novo_nome_base = folder_full_name
				elif memorial and not comprovante:
					# Para btn_memorial (memorial=True), usa a lógica específica
					prefixo = "MEMORIAL DE CÁLCULO - "
					folder_name_parts = folder_full_name.split('-')
					
					if len(folder_name_parts) >= 3:
						part0 = folder_name_parts[0].strip()
						part1 = folder_name_parts[1].strip()
						part2 = folder_name_parts[2].strip()
						novo_nome_base = f"{prefixo}{part2} - {part0}  {part1}"
					else:
						messagebox.showwarning("Formato de Pasta Inválido", 
											   f"O nome da pasta '{folder_full_name}' não está no formato esperado para renomeação de memorial (ex: '01 - Nome - OutroNome'). Usando o nome completo da pasta com prefixo.")
						novo_nome_base = f"{prefixo}{folder_full_name}"
				elif comprovante and not memorial:
					prefixo = "COMPROVANTE DE PAGAMENTO - "
					folder_name_parts = folder_full_name.split('-')
					
					if len(folder_name_parts) >= 3:
						part0 = folder_name_parts[0].strip()
						part1 = folder_name_parts[1].strip()
						part2 = folder_name_parts[2].strip()
						novo_nome_base = f"{prefixo}{part2} - {part0}  {part1}"
					else:
						messagebox.showwarning("Formato de Pasta Inválido", 
											   f"O nome da pasta '{folder_full_name}' não está no formato esperado para renomeação de comprovante (ex: '01 - Nome - OutroNome'). Usando o nome completo da pasta com prefixo.")
						novo_nome_base = f"{prefixo}{folder_full_name}"
				novo_nome = f"{novo_nome_base}{sufixo}{arquivo.suffix}"
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
		
		# Em vez de fechar, limpa a seleção e recarrega a lista de arquivos
		self.arquivos_selecionados.clear()
		self.btn_reclamacao.config(state=tk.DISABLED)
		self.btn_memorial.config(state=tk.DISABLED)
		self.btn_comprovante.config(state=tk.DISABLED)
		self.carregar_arquivos()

	def criar_subpastas(self):
		subpastas_criadas = []
		subpastas_existentes = []
		erros = []

		for nome_pasta in PASTAS_PADRAO:
			caminho_pasta = self.base_dir / nome_pasta
			if caminho_pasta.exists() and caminho_pasta.is_dir():
				subpastas_existentes.append(nome_pasta)
			else:
				try:
					caminho_pasta.mkdir(exist_ok=True)
					subpastas_criadas.append(nome_pasta)
				except Exception as e:
					erros.append(f"Erro ao criar '{nome_pasta}': {str(e)}")

		mensagem = "Processo de criação de subpastas concluído:\n"
		if subpastas_criadas:
			mensagem += f"\nCriadas: {', '.join(subpastas_criadas)}"
		if subpastas_existentes:
			mensagem += f"\nJá existentes: {', '.join(subpastas_existentes)}"
		if erros:
			mensagem += f"\nErros: {', '.join(erros)}"
			messagebox.showerror("Erro na Criação de Subpastas", mensagem)
		else:
			messagebox.showinfo("Criação de Subpastas", mensagem)

if __name__ == "__main__":
	root = tk.Tk()
	app = RenomeadorGUI(root)
	root.mainloop()
