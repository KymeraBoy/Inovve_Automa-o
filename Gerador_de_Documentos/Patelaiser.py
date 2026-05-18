import json
import os


PASTAS_PADRAO = ["Anexos", "QIP", "CIP", "Censo", "outros"]


def criar_pasta_anexos(pasta_mae: str) -> dict:
	"""
	Varre a estrutura: Pasta mãe > Município > Documentos
	Cria pasta 'Anexos' em cada pasta Documentos se não existir
	"""
	resultado = {
		"municipios_processados": {},
		"total_anexos_criadas": 0,
		"total_anexos_existentes": 0,
		"erros": []
	}

	try:
		with os.scandir(pasta_mae) as municipios_iter:
			for municipio_item in municipios_iter:
				if not municipio_item.is_dir():
					continue

				municipio_nome = municipio_item.name
				municipio_path = municipio_item.path

				# Procura pasta "Documentos" dentro do município
				pasta_documentos_path = None
				try:
					with os.scandir(municipio_path) as items:
						for item in items:
							if item.is_dir() and item.name.lower() == "documentos":
								pasta_documentos_path = item.path
								break
				except PermissionError:
					resultado["erros"].append(f"Sem permissão para acessar {municipio_path}")
					continue

				if not pasta_documentos_path:
					# Não encontrou pasta Documentos, pula para próximo município
					continue

				# Agora processa a pasta Documentos
				pasta_anexos_path = os.path.join(pasta_documentos_path, "Outros")

				# Verifica se já existe
				if os.path.exists(pasta_anexos_path):
					resultado["municipios_processados"][municipio_nome] = {
						"acao": "ja_existe",
						"caminho": pasta_anexos_path
					}
					resultado["total_anexos_existentes"] += 1
				else:
					# Cria a pasta
					try:
						os.makedirs(pasta_anexos_path, exist_ok=True)
						resultado["municipios_processados"][municipio_nome] = {
							"acao": "criada",
							"caminho": pasta_anexos_path
						}
						resultado["total_anexos_criadas"] += 1
					except Exception as e:
						resultado["erros"].append(f"Erro ao criar Anexos em {municipio_nome}: {str(e)}")

	except PermissionError:
		resultado["erros"].append(f"Sem permissão para acessar {pasta_mae}")

	return resultado


def main() -> None:
	print("Informe o endereço da pasta mãe:")
	pasta_mae = input("> ").strip().strip('"')

	if not pasta_mae:
		print("Erro: caminho vazio.")
		return

	if not os.path.isdir(pasta_mae):
		print(f"Erro: pasta inválida: {pasta_mae}")
		return

	print("\nProcessando municipios...")
	resultado = criar_pasta_anexos(pasta_mae)

	print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()
