from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from QIPer import _is_qip_antigo, _extract_mes_ano_municipio_from_qip_antigo, _extract_table_from_qip_antigo

pdf_path = Path(__file__).resolve().parent / "Testes" / "QIP-AGUIAR-2015_07.pdf"

print(f"Testando: {pdf_path.name}\n")
print(f"Arquivo existe: {pdf_path.exists()}")

is_antigo = _is_qip_antigo(pdf_path)
print(f"É QIP Antigo: {is_antigo}\n")

if is_antigo:
    info = _extract_mes_ano_municipio_from_qip_antigo(pdf_path)
    print(f"Extração de dados: {info}\n")
    
    table = _extract_table_from_qip_antigo(pdf_path)
    if table is not None:
        print(f"Tabela extraída com sucesso!")
        print(f"Forma: {table.shape}")
        print(f"Colunas: {list(table.columns)}")
        print(f"\nPrimeiras linhas:")
        print(table.head())
    else:
        print("Erro: Tabela não foi extraída")
else:
    print("Aviso: O arquivo não foi detectado como QIP Antigo")
