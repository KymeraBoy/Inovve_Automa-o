from pathlib import Path
import pdfplumber

pdf_path = Path(__file__).resolve().parent / "Testes" / "QIP Antigo.pdf"

print(f"Inspecionando: {pdf_path.name}\n")
print("=" * 80)

with pdfplumber.open(pdf_path) as pdf:
    print(f"Total de páginas: {len(pdf.pages)}\n")
    
    for page_idx, page in enumerate(pdf.pages):
        print(f"\n{'='*80}")
        print(f"PÁGINA {page_idx + 1}")
        print(f"{'='*80}\n")
        
        # Texto completo da página
        text = page.extract_text()
        if text:
            print("TEXTO EXTRAÍDO:")
            print("-" * 80)
            print(text[:2000])  # Primeiros 2000 caracteres
            print("\n\nPRIMEIRAS 50 LINHAS:")
            print("-" * 80)
            for i, line in enumerate(text.splitlines()[:50]):
                print(f"{i:2d}: {line}")
        
        # Tabelas
        tables = page.extract_tables()
        if tables:
            print(f"\n\nTABELAS ENCONTRADAS: {len(tables)}")
            print("-" * 80)
            for t_idx, table in enumerate(tables):
                print(f"\nTABELA {t_idx + 1}:")
                for row_idx, row in enumerate(table[:10]):  # Primeiras 10 linhas
                    print(f"  Linha {row_idx}: {row}")
                if len(table) > 10:
                    print(f"  ... ({len(table) - 10} linhas adicionais)")
        
        print("\n")
