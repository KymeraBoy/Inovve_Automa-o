"""
renomear_pastas.py
Renomeia pastas de reclamações para o padrão:
  REC-NNN_AAAA-CIDADE-ENQUADRAMENTO_TIPO-UC  ou  REC-NNN_AAAA-CIDADE-ASSUNTO

Uso:
  python renomear_pastas.py                   # usa a pasta onde o script está
  python renomear_pastas.py "C:\\outro\\caminho"
  python renomear_pastas.py --previa          # mostra o que seria feito, sem renomear
"""

import os
import re
import sys
import unicodedata
import argparse


def normalizar(texto: str) -> str:
    """Remove acentos, converte para maiúsculas e substitui espaços por underscore."""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.upper().strip()
    texto = re.sub(r"\s+", "_", texto)
    texto = re.sub(r"[^\w\-_.]", "", texto)
    return texto


def converter_nome(nome: str):
    """
    Retorna o novo nome no padrão REC-... ou None se não reconhecer.
    """
    # Padrão com Enquadramento + UC
    m = re.match(
        r"^RECLAMAÇÃO\s+(\d+)_(\d{4})\s*-+\s*(.+?)\s*-+\s*Enquadramento\s+(\w+)\s+UC\s*([\d\-]*)\s*$",
        nome,
        re.IGNORECASE,
    )
    if m:
        num    = m.group(1).zfill(3)
        ano    = m.group(2)
        cidade = normalizar(m.group(3))
        tipo   = normalizar(m.group(4))
        uc     = m.group(5).strip()
        return f"REC-{num}_{ano}-{cidade}-ENQUADRAMENTO_{tipo}-{uc}"

    # Padrão com assunto livre
    m = re.match(
        r"^RECLAMAÇÃO\s+(\d+)_(\d{4})\s*-+\s*(.+?)\s*-+\s*(.+)$",
        nome,
        re.IGNORECASE,
    )
    if m:
        num     = m.group(1).zfill(3)
        ano     = m.group(2)
        cidade  = normalizar(m.group(3))
        assunto = normalizar(m.group(4))
        return f"REC-{num}_{ano}-{cidade}-{assunto}"

    return None


def main():
    parser = argparse.ArgumentParser(description="Renomeia pastas de reclamações.")
    parser.add_argument(
        "pasta",
        nargs="?",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Caminho da pasta com as reclamações (padrão: mesma pasta do script)",
    )
    parser.add_argument(
        "--previa",
        action="store_true",
        help="Apenas exibe as mudanças sem renomear",
    )
    args = parser.parse_args()

    pasta = args.pasta

    if not os.path.isdir(pasta):
        print(f"ERRO: Pasta não encontrada: {pasta}")
        sys.exit(1)

    dirs = sorted(
        [d for d in os.listdir(pasta) if os.path.isdir(os.path.join(pasta, d))]
    )

    if not dirs:
        print(f"Nenhuma pasta encontrada em: {pasta}")
        sys.exit(0)

    mudancas = []
    for nome in dirs:
        novo = converter_nome(nome)
        if novo and novo != nome:
            mudancas.append((nome, novo))
        else:
            print(f"  IGNORADO: {nome}")

    if not mudancas:
        print("\nNenhuma pasta precisa ser renomeada.")
        sys.exit(0)

    print("\n===== PRÉVIA DAS MUDANÇAS =====")
    for atual, novo in mudancas:
        print(f"  DE:   {atual}")
        print(f"  PARA: {novo}\n")

    if args.previa:
        print("Modo prévia: nenhuma pasta foi renomeada.")
        sys.exit(0)

    resposta = input(f"Deseja renomear as {len(mudancas)} pasta(s) acima? (S/N): ").strip().upper()
    if resposta != "S":
        print("Operação cancelada.")
        sys.exit(0)

    ok = 0
    erros = 0
    for atual, novo in mudancas:
        try:
            os.rename(os.path.join(pasta, atual), os.path.join(pasta, novo))
            print(f"  OK: {novo}")
            ok += 1
        except Exception as e:
            print(f"  ERRO ao renomear '{atual}': {e}")
            erros += 1

    print(f"\n===== CONCLUÍDO: {ok} renomeadas, {erros} erros =====")


if __name__ == "__main__":
    main()
