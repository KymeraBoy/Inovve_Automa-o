from pathlib import Path

base = Path(__file__).resolve().parent

for pdf in base.glob("*.pdf"):
    if "_ASSINADO" not in pdf.stem:
        novo_nome = pdf.with_stem(pdf.stem + "_ASSINADO")
        pdf.rename(novo_nome)
        print(f"[OK] {pdf.name}  →  {novo_nome.name}")

print("Concluído.")
