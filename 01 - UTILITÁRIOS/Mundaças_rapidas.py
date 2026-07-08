from pathlib import Path

# Pasta onde o script está
PASTA = Path(__file__).parent

# Termo original -> Novo termo
SUBSTITUICOES = {
    "REQ ": "REQ-",
    "Inclusão na lista de e-mail": "INCLUSÃO_E-MAILS",
    "Faturamento IP": "FATURAMENTO_IP",
    "Levantamento Cadastral IP": "LEVANTAMENTO_CADASTRAL_IP",
    "Dados da CIP": "CIP",
    "Informações DIC, FIC, DMIC": "INDICADORES_DE_QUALIDADE",
    "Informações Demandas IP": "DEMANDA_IP",
    "Cópia QIP": "QIP",
}

renomeadas = 0

for pasta in PASTA.iterdir():
    if not pasta.is_dir():
        continue

    nome_antigo = pasta.name
    nome_novo = nome_antigo

    # Aplica todas as substituições encontradas no nome
    for antigo, novo in SUBSTITUICOES.items():
        nome_novo = nome_novo.replace(antigo, novo)

    # Se nada mudou, pula
    if nome_novo == nome_antigo:
        continue

    destino = pasta.parent / nome_novo

    if destino.exists():
        print(f"⚠ Não foi possível renomear:\n   {nome_antigo}\n   -> {nome_novo}\n   (já existe)\n")
        continue

    pasta.rename(destino)
    print(f"✔ {nome_antigo}\n  → {nome_novo}\n")
    renomeadas += 1

print(f"Concluído! {renomeadas} pasta(s) renomeada(s).")