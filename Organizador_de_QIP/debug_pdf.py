from pathlib import Path
import pdfplumber

TESTES_DIR = Path(__file__).resolve().parent / "Testes"

# Inspeciona o primeiro PDF
pdf_files = sorted(TESTES_DIR.glob("*.pdf"))
if pdf_files:
    pdf_file = pdf_files[0]
    print(f"Inspecionando: {pdf_file.name}\n")
    
    with pdfplumber.open(pdf_file) as pdf:
        if pdf.pages:
            text = pdf.pages[0].extract_text()
            print("Primeiras 1000 caracteres do texto:\n")
            print(text[:1000] if text else "Nenhum texto encontrado")
            print("\n\nTodas as linhas da primeira página:")
            if text:
                for i, line in enumerate(text.splitlines()[:30]):
                    print(f"{i}: {line}")
