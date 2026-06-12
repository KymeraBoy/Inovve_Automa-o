from pathlib import Path
import re
import shutil

# Mapeia abreviações de mês (pt-BR) para número.
MESES = {
    "JAN": 1,
    "FEV": 2,
    "MAR": 3,
    "ABR": 4,
    "MAI": 5,
    "JUN": 6,
    "JUL": 7,
    "AGO": 8,
    "SET": 9,
    "OUT": 10,
    "NOV": 11,
    "DEZ": 12,
}


def extrair_ano_mes(nome_arquivo: str):
    """Extrai (ano, mes) usando siglas como JAN, FEV, MAR, etc."""
    nome = nome_arquivo.upper()

    # Ex.: JAN-2025, JAN_2025, CATOLE_JAN-2020, JAN2025
    m1 = re.search(r"(?<![A-Z])([A-Z]{3})[._ -]?(20\d{2})(?!\d)", nome)
    if m1 and m1.group(1) in MESES:
        return int(m1.group(2)), MESES[m1.group(1)]

    # Ex.: 2025-JAN, 2025_JAN, 2025JAN
    m2 = re.search(r"(?<!\d)(20\d{2})[._ -]?([A-Z]{3})(?![A-Z])", nome)
    if m2 and m2.group(2) in MESES:
        return int(m2.group(1)), MESES[m2.group(2)]

    return None


def pasta_destino(base: Path, ano: int, mes: int) -> Path:
    return base / f"{ano}.{mes:02d}"


def nome_disponivel(caminho: Path) -> Path:
    """Evita sobrescrever arquivos existentes na pasta destino."""
    if not caminho.exists():
        return caminho

    contador = 1
    while True:
        candidato = caminho.with_name(f"{caminho.stem}_{contador}{caminho.suffix}")
        if not candidato.exists():
            return candidato
        contador += 1


def organizar_pdfs_por_mes():
    base = Path(__file__).resolve().parent
    pdfs = sorted(base.glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado na pasta do script.")
        return

    movidos = 0
    ignorados = 0

    for pdf in pdfs:
        resultado = extrair_ano_mes(pdf.stem)
        if not resultado:
            ignorados += 1
            print(f"[IGNORADO] Sem mês/ano identificável: {pdf.name}")
            continue

        ano, mes = resultado
        destino_pasta = pasta_destino(base, ano, mes)
        destino_pasta.mkdir(exist_ok=True)

        destino_arquivo = nome_disponivel(destino_pasta / pdf.name)
        shutil.move(str(pdf), str(destino_arquivo))

        movidos += 1
        print(f"[OK] {pdf.name} -> {destino_pasta.name}/{destino_arquivo.name}")

    print(f"\nConcluído. Movidos: {movidos} | Ignorados: {ignorados}")


if __name__ == "__main__":
    organizar_pdfs_por_mes()
