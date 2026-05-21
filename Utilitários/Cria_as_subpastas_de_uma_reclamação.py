import json
import os


PASTAS_PADRAO = [
	"ANEEL",
	"DOCUMENTOS_RECEBIDOS",
	"PAGAMENTO",
	"E-MAILS",
	"RECLAMACAO_FORMAL",
]


def criar_pastas_no_nivel_do_script() -> dict:
	diretorio_script = os.path.dirname(os.path.abspath(__file__))
	criadas = []
	ja_existentes = []
	erros = []

	for nome_pasta in PASTAS_PADRAO:
		caminho_pasta = os.path.join(diretorio_script, nome_pasta)
		if os.path.isdir(caminho_pasta):
			ja_existentes.append(nome_pasta)
			continue

		try:
			os.makedirs(caminho_pasta, exist_ok=True)
			criadas.append(nome_pasta)
		except Exception as e:
			erros.append(f"Erro ao criar '{nome_pasta}': {str(e)}")

	return {
		"diretorio": diretorio_script,
		"criadas": criadas,
		"ja_existentes": ja_existentes,
		"erros": erros,
	}


def main() -> None:
	resultado = criar_pastas_no_nivel_do_script()
	print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()
