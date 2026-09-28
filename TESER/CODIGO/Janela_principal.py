from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QComboBox,
    QLabel,
    QGridLayout,
    QLineEdit,
    QSpinBox
)
from datetime import datetime


class ContadorCodigo(QSpinBox):
    def textFromValue(self, value):
        return f"{value:03d}"

    def valueFromText(self, texto):
        return int(texto or "0")


class JanelaPrincipal(QMainWindow):

    def __init__(
            self,
            serie_municipios,
            serie_empresas,
            serie_concessionarias,
            serie_ucs,
            teses,
            lista_rec,
            lista_req,
            lista_ofi
        ):
        super().__init__()

        self.serie_empresas         = serie_empresas
        self.serie_municipios       = serie_municipios
        self.serie_concessionarias  = serie_concessionarias
        self.serie_ucs              = serie_ucs

        self.setWindowTitle("TESER")
        self.resize(1280, 600)

        self.box_municipios         = QComboBox()
        self.box_tese_tipo          = QComboBox()
        self.box_tese_subtipo       = QComboBox()
        self.label_empresa          = QLabel()
        self.label_concessionaria   = QLabel()
        self.box_uc                 = QLineEdit()
        self.contador_codigo        = ContadorCodigo()
        self.contador_codigo.setRange(1, 2147483647)
        self.contador_codigo.setValue(1)
        self.box_ano                = QComboBox()
        ano_atual = datetime.now().year
        self.box_ano.addItems([str(ano_atual - deslocamento) for deslocamento in range(3)])

        self.listas_teses = [lista_rec, lista_req, lista_ofi]

        # Carrega os itens da série no QComboBox
        for item in serie_municipios:
            self.box_municipios.addItem(str(item))
        # Carrega os itens da série no QComboBox
        for item in teses:
            self.box_tese_tipo.addItem(str(item))

        self.box_tese_subtipo.addItems(self.listas_teses[0])
        self.box_municipios.currentTextChanged.connect(self.atualizar_Empresa)
        self.box_tese_tipo.currentIndexChanged.connect(self.atualizar_Teses)


        # Organização da janela
        central = QWidget()
        layout = QGridLayout()
        cabecalhos = ["Município", "Empresa", "Concessionária", "UC", "Tipo de tese", "Nº", "Ano", "Tese"]
        componentes = [
            self.box_municipios,
            self.label_empresa,
            self.label_concessionaria,
            self.box_uc,
            self.box_tese_tipo,
            self.contador_codigo,
            self.box_ano,
            self.box_tese_subtipo,
        ]
        for coluna, (cabecalho, componente) in enumerate(zip(cabecalhos, componentes)):
            layout.addWidget(QLabel(cabecalho), 0, coluna)
            layout.addWidget(componente, 1, coluna)

        central.setLayout(layout)
        self.setCentralWidget(central)
        self.atualizar_Empresa(self.box_municipios.currentText())


    def atualizar_Teses(self, indice):
        if 0 <= indice < len(self.listas_teses):
            self.box_tese_subtipo.clear()
            self.box_tese_subtipo.addItems(self.listas_teses[indice])


    def atualizar_Empresa(self, texto):
        indices = self.serie_municipios[self.serie_municipios == texto].index
        if len(indices) == 0:
            return
        indice = indices[0]
        empresa         = self.serie_empresas[indice]
        concessionaria  = self.serie_concessionarias[indice]
        self.label_empresa.setText(empresa)
        self.label_concessionaria.setText(concessionaria)
        self.box_uc.setText(str(self.serie_ucs[indice]))
