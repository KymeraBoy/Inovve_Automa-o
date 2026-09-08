from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QComboBox,
    QLabel,
    QHBoxLayout
)


class JanelaPrincipal(QMainWindow):

    def __init__(
            self,
            serie_municipios,
            serie_empresas,
            serie_concessionarias,
            teses,
            lista_rec,
            lista_req,
            lista_ofi
        ):
        super().__init__()

        self.serie_empresas         = serie_empresas
        self.serie_municipios       = serie_municipios
        self.serie_concessionarias  = serie_concessionarias

        self.setWindowTitle("TESER")
        self.resize(800, 600)

        self.box_municipios         = QComboBox()
        self.box_tese_tipo          = QComboBox()
        self.box_tese_subtipo       = QComboBox()
        self.label_empresa          = QLabel()
        self.label_concessionaria   = QLabel()

        # Carrega os itens da série no QComboBox
        for item in serie_municipios:
            self.box_municipios.addItem(str(item))
        # Carrega os itens da série no QComboBox
        for item in teses:
            self.box_tese_tipo.addItem(str(item))

        # Quando a seleção mudar, chama atualizar_Empresa()
        self.box_municipios.currentTextChanged.connect(self.atualizar_Empresa)


        # Organização da janela
        central = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(self.box_municipios)
        layout.addWidget(self.label_empresa)
        layout.addWidget(self.label_concessionaria)
        layout.addWidget(self.box_tese_tipo)
        layout.addWidget(self.box_tese_subtipo)
        central.setLayout(layout)
        self.setCentralWidget(central)


    def atualizar_Empresa(self, texto):
        empresa         = self.serie_empresas[self.serie_municipios[self.serie_municipios == texto].index[0]]
        concessionaria  = self.serie_concessionarias[self.serie_municipios[self.serie_municipios == texto].index[0]]
        self.label_empresa.setText(empresa)
        self.label_concessionaria.setText(concessionaria)
