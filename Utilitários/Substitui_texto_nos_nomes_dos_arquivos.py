from pathlib import Path


def coletar_itens(base_dir: Path) -> list[Path]:
	"""Retorna apenas arquivos e pastas diretos de base_dir, sem entrar em subpastas."""
	return list(base_dir.iterdir())


def substituir_nomes(base_dir: Path, texto_antigo: str, texto_novo: str) -> None:
	itens = coletar_itens(base_dir)
	alterados = 0
	ignorados = 0

	for caminho in itens:
		nome_atual = caminho.name
		if texto_antigo not in nome_atual:
			continue

		novo_nome = nome_atual.replace(texto_antigo, texto_novo)
		if novo_nome == "":
			ignorados += 1
			print(f"[IGNORADO] Nome vazio nao e permitido: {caminho}")
			continue

		destino = caminho.with_name(novo_nome)

		if destino.exists():
			ignorados += 1
			print(f"[IGNORADO] Ja existe: {destino}")
			continue

		try:
			caminho.rename(destino)
			alterados += 1
			print(f"[OK] {caminho.name} -> {destino.name}")
		except OSError as erro:
			ignorados += 1
			print(f"[ERRO] Nao foi possivel renomear '{caminho}': {erro}")

	print("\nResumo:")
	print(f"- Itens renomeados: {alterados}")
	print(f"- Itens ignorados/com erro: {ignorados}")


def main() -> None:
	pasta_script = Path(__file__).resolve().parent

	print("Renomeador por substituicao de texto")
	print(f"Pasta de trabalho: {pasta_script}\n")

	texto_antigo = input("Qual texto sera substituido? ")
	if texto_antigo == "":
		print("Texto a substituir nao pode ser vazio (apenas Enter).")
		return

	texto_novo = input("Por qual texto substituir? (Enter = apagar o texto) ")
	if texto_novo == "":
		print("Modo ativo: o texto informado sera removido dos nomes.")

	confirmar = input(
		"\nConfirmar renomeacao de arquivos e pastas nesta pasta? (s/n): "
	).strip().lower()
	if confirmar != "s":
		print("Operacao cancelada.")
		return

	substituir_nomes(pasta_script, texto_antigo, texto_novo)


if __name__ == "__main__":
	main()
