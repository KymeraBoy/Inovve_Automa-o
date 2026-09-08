import CONFIG
from pathlib import Path
import pandas as pd
import sys
from PySide6.QtWidgets import QApplication
from Janela_principal import JanelaPrincipal


# Carregando as abas da planilha de dados dos municípios
ABA_MUNICIPIOS      = pd.read_excel(CONFIG.PLANILHA_DADOS_DOS_MUNICIPIOS, sheet_name="Municípios")
ABA_CONCESSIONARIAS = pd.read_excel(CONFIG.PLANILHA_DADOS_DOS_MUNICIPIOS, sheet_name="Concessionárias")
ABA_EMPRESAS        = pd.read_excel(CONFIG.PLANILHA_DADOS_DOS_MUNICIPIOS, sheet_name="Empresas")


def listar_arquivos(pasta):
    return [arquivo.stem for arquivo in Path(pasta).iterdir() if arquivo.is_file()]

LISTA_REC = listar_arquivos(CONFIG.PASTA_REC)
LISTA_REQ = listar_arquivos(CONFIG.PASTA_REQ)
LISTA_OFI = listar_arquivos(CONFIG.PASTA_OFI)

print(LISTA_REC)

TESES = ["RECLAMAÇÃO", "REQUERIMENTO", "OFÍCIO"]

serie_Municipios        = ABA_MUNICIPIOS.iloc[:, 0]
serie_Empresas          = ABA_MUNICIPIOS.iloc[:, 1]
serie_Concessionarias   = ABA_MUNICIPIOS.iloc[:, 2]

app = QApplication(sys.argv)

janela = JanelaPrincipal(
    serie_Municipios,
    serie_Empresas,
    serie_Concessionarias,
    TESES,
    LISTA_REC,
    LISTA_REQ,
    LISTA_OFI
)
janela.show()

sys.exit(app.exec())