import sys
from pathlib            import Path
from PySide6.QtCore     import Qt
from PySide6.QtWidgets  import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from Renomer    import Renomer
from Anexer     import Anexer
from Sumarier   import Sumarier

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.nome_municipio         = ""
        self.pasta_municipio        = ""
        self.empresa_selecionada    = ""

        # Identifica o diretório base (funciona tanto em .py quanto no executável do PyInstaller)
        if getattr(sys, 'frozen', False):
            self.diretorio_base = Path(sys.executable).resolve().parent
        else:
            self.diretorio_base = Path(__file__).resolve().parent

        # Caminho para o executável do LuaLaTeX dentro da pasta portátil
        self.caminho_miktex_bin = self.diretorio_base / "miktex" / "texmfs" / "install" / "miktex" / "bin" / "x64"
        self.caminho_lualatex = self.caminho_miktex_bin / "lualatex.exe"

        self.setWindowTitle("Documentaizer")
        self.resize(1400, 800)
        self.setWindowState(Qt.WindowMaximized)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout_principal = QVBoxLayout(self.central_widget)
        self.layout_principal.setContentsMargins(15, 15, 15, 15)
        self.layout_principal.setSpacing(15)

        self.criar_area_inicial()
        self.criar_area_etapas()

        # Conectar sinais para atualizar as etapas
        self.input_municipio.textChanged.connect(self.atualizar_dados_integracao)
        self.combo_uf.currentIndexChanged.connect(self.atualizar_dados_integracao)
        self.combo_empresa.currentIndexChanged.connect(self.atualizar_dados_integracao)

        # Carrega lista inicial de empresas
        self.carregar_empresas()

    def criar_area_inicial(self):
        self.area_inicial = QFrame()
        self.area_inicial.setFrameShape(QFrame.StyledPanel)
        self.area_inicial.setFrameShadow(QFrame.Raised)

        layout_area_inicial = QHBoxLayout(self.area_inicial)
        layout_area_inicial.setContentsMargins(10, 10, 10, 10)
        layout_area_inicial.setSpacing(10)

        # Município
        self.label_municipio = QLabel("Município:")
        self.input_municipio = QLineEdit()
        self.input_municipio.setPlaceholderText("Digite o nome do município")

        # UF (Estado)
        self.label_uf = QLabel("UF:")
        self.combo_uf = QComboBox()
        estados_br = [
            "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
            "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
            "RO", "RR", "RS", "SC", "SE", "SP", "TO"
        ]
        self.combo_uf.addItems(estados_br)

        # Empresa (Retrátil / ComboBox)
        self.label_empresa = QLabel("Empresa:")
        self.combo_empresa = QComboBox()

        # Pasta dos documentos
        self.label_pasta = QLabel("Pasta:")
        self.input_pasta = QLineEdit()
        self.input_pasta.setPlaceholderText("Selecione a pasta dos documentos")
        self.input_pasta.setReadOnly(True)

        self.botao_buscar_pasta = QPushButton("Buscar pasta")
        self.botao_buscar_pasta.clicked.connect(self.selecionar_pasta)

        # Adiciona no layout
        layout_area_inicial.addWidget(self.label_municipio)
        layout_area_inicial.addWidget(self.input_municipio, 1)

        layout_area_inicial.addWidget(self.label_uf)
        layout_area_inicial.addWidget(self.combo_uf)

        layout_area_inicial.addWidget(self.label_empresa)
        layout_area_inicial.addWidget(self.combo_empresa, 1)

        layout_area_inicial.addWidget(self.label_pasta)
        layout_area_inicial.addWidget(self.input_pasta, 2)

        layout_area_inicial.addWidget(self.botao_buscar_pasta)

        self.layout_principal.addWidget(self.area_inicial)

    def carregar_empresas(self):
        """
        Lê a pasta /Empresas junto do script e adiciona à combo_empresa.
        """
        self.combo_empresa.clear()
        pasta_empresas = self.diretorio_base / "EMPRESAS"

        if pasta_empresas.exists() and pasta_empresas.is_dir():
            empresas = [
                d.name for d in pasta_empresas.iterdir() if d.is_dir()
            ]
            empresas.sort()
            self.combo_empresa.addItems(empresas)

        self.atualizar_dados_integracao()

    def criar_area_etapas(self):
        self.layout_etapas = QHBoxLayout()
        self.layout_etapas.setSpacing(15)

        # Módulos das Etapas
        self.Renomer    = Renomer()
        self.Anexer     = Anexer()
        self.Sumarier   = Sumarier()

        # Conecta atualização do Etapa 1 para atualizar a Etapa 2
        self.Renomer.arquivo_renomeado.connect(self.Anexer.atualizar_estrutura)

        # Quando os anexos em PDF forem gerados na Etapa 2, re-sincroniza a Etapa 3
        self.Anexer.anexos_gerados.connect(self.atualizar_dados_integracao)

        # Dividir a largura em 3 partes iguais
        self.layout_etapas.addWidget(self.Renomer, 1)
        self.layout_etapas.addWidget(self.Anexer, 1)
        self.layout_etapas.addWidget(self.Sumarier, 1)

        self.layout_principal.addLayout(self.layout_etapas)

    def selecionar_pasta(self):
        pasta = QFileDialog.getExistingDirectory(
            self, "Selecionar pasta dos documentos"
        )
        if pasta:
            self.pasta_municipio = str(Path(pasta))
            self.input_pasta.setText(self.pasta_municipio)

            self.Renomer.set_pasta_municipio(self.pasta_municipio)
            self.Anexer.set_pasta_municipio(self.pasta_municipio)
            self.atualizar_dados_integracao()

    def atualizar_dados_integracao(self):
        self.nome_municipio = self.input_municipio.text().strip()
        self.empresa_selecionada = self.combo_empresa.currentText()
        uf_selecionada = self.combo_uf.currentText()

        # Atualiza a Etapa 1
        self.Renomer.set_nome_municipio(self.nome_municipio)

        pasta_empresa_path = None
        if self.empresa_selecionada:
            pasta_empresa_path = (
                self.diretorio_base / "EMPRESAS" / self.empresa_selecionada
            )

        # Atualiza a Etapa 2
        self.Anexer.set_dados(
            nome_municipio=self.nome_municipio,
            pasta_empresa=pasta_empresa_path
        )

        # Atualiza a Etapa 3 passando o caminho do executável do LuaLaTeX portátil
        self.Sumarier.set_dados(
            municipio=self.nome_municipio,
            uf=uf_selecionada,
            empresa=self.empresa_selecionada,
            pasta_municipio=self.pasta_municipio,
            pasta_empresa=pasta_empresa_path,
            caminho_lualatex=self.caminho_lualatex,
            caminho_miktex_bin=self.caminho_miktex_bin
        )

    def resizeEvent(self, event):
        altura_janela       = self.central_widget.height()
        altura_area_inicial = int(altura_janela * 0.10)
        self.area_inicial.setFixedHeight(altura_area_inicial)
        super().resizeEvent(event)


def main():
    app = QApplication(sys.argv)
    janela = MainWindow()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()