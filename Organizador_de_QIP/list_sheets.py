import openpyxl
from pathlib import Path

xlsx_path = Path(__file__).resolve().parent / "Testes" / "Output" / "QIP_consolidado.xlsx"

try:
    workbook = openpyxl.load_workbook(xlsx_path, data_only=False)
    print(f"Abas no arquivo consolidado:")
    for sheet_name in workbook.sheetnames:
        print(f"  - {sheet_name}")
except Exception as e:
    print(f"Erro: {e}")
