from pathlib import Path
import win32com.client as win32


# ============================================================
# CONFIGURAÇÕES
# ============================================================

# Pasta onde este script está localizado
PASTA = Path(__file__).resolve().parent

# Extensões de Excel que serão convertidas
EXTENSOES = {".xlsx", ".xls", ".xlsm"}


# ============================================================
# INICIALIZAÇÃO DO EXCEL
# ============================================================

excel = win32.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.ScreenUpdating = False

# Impede que o Excel mostre mensagens de confirmação
excel.AskToUpdateLinks = False


try:
    # Pega apenas arquivos Excel da pasta
    arquivos = sorted(
        arquivo
        for arquivo in PASTA.iterdir()
        if arquivo.is_file()
        and arquivo.suffix.lower() in EXTENSOES
        and not arquivo.name.startswith("~$")
    )

    if not arquivos:
        print("Nenhum arquivo Excel encontrado.")
    
    for arquivo in arquivos:
        pdf = arquivo.with_suffix(".pdf")

        print(f"\nConvertendo: {arquivo.name}")

        wb = None

        try:
            # Abre a planilha somente para leitura
            wb = excel.Workbooks.Open(
                str(arquivo),
                UpdateLinks=0,
                ReadOnly=True,
                IgnoreReadOnlyRecommended=True,
                AddToMru=False
            )

            # Exporta a planilha inteira para PDF
            wb.ExportAsFixedFormat(
                Type=0,                    # 0 = PDF
                Filename=str(pdf),
                Quality=0,                 # 0 = qualidade padrão
                IncludeDocProperties=True,
                IgnorePrintAreas=False,
                OpenAfterPublish=False
            )

            print(f"PDF criado: {pdf.name}")

        except Exception as e:
            print(f"ERRO ao converter {arquivo.name}: {e}")

        finally:
            # Garante que a pasta de trabalho seja fechada
            if wb is not None:
                try:
                    wb.Close(SaveChanges=False)
                except Exception:
                    pass


finally:
    # Garante que o Excel seja encerrado
    try:
        excel.ScreenUpdating = True
        excel.DisplayAlerts = True
        excel.Quit()
    except Exception:
        pass


print("\nConversão concluída.")