import os
from pathlib import Path
import win32com.client as win32

# Pasta onde o script está localizado
PASTA = Path(__file__).parent.resolve()

# Inicializa o Excel
excel = win32.Dispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False

try:
    arquivos = (
        list(PASTA.glob("*.xlsx")) +
        list(PASTA.glob("*.xls")) +
        list(PASTA.glob("*.xlsm"))
    )

    for arquivo in arquivos:
        for arquivo in PASTA.glob("*.xlsx"):
            pdf = arquivo.with_suffix(".pdf")

            print(f"Convertendo: {arquivo.name}")

            try:
                wb = excel.Workbooks.Open(str(arquivo))

                # 0 = PDF
                wb.ExportAsFixedFormat(
                    Type=0,
                    Filename=str(pdf),
                    Quality=0,
                    IncludeDocProperties=True,
                    IgnorePrintAreas=False,
                    OpenAfterPublish=False
                )

                wb.Close(False)
                print(f"PDF criado: {pdf.name}")

            except Exception as e:
                print(f"Erro ao converter {arquivo.name}: {e}")

finally:
    excel.Quit()

print("\nConversão concluída.")