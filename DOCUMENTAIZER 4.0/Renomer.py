import os
import re
import unicodedata
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

TIPOS_DOCUMENTO = [
    "Contrato",
    "Procuração",
    "Aditivo",
    "Relatório de Assinaturas",
    "Kit Prefeito",
    "Publicação",
]

OPCOES_ADITIVO = [
    "1",
    "2",
    "3",
    "4",
    "5",
]

OPCOES_RELATORIO = [
    "Contrato",
    "Procuração",
    "Aditivo",
]

OPCOES_PUBLICACAO = [
    "Contrato",
    "Aditivo",
]

OPCOES_TERCEIRA_CAIXA = [
    "1",
    "2",
    "3",
    "4",
    "5",
]


class Renomer(QWidget):
    """
    Primeira etapa do Documentaizer: Renomeação.
    """

    arquivo_renomeado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.nome_municipio = ""
        self.pasta_municipio = ""

        self.criar_interface()
        self.atualizar_segunda_caixa()
        self.atualizar_preview()

    def criar_interface(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(10, 10, 10, 10)
        self.layout_principal.setSpacing(8)

        # TÍTULO
        self.titulo = QLabel("ETAPA 1 - RENOMEAÇÃO")
        self.titulo.setAlignment(Qt.AlignCenter)
        self.titulo.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            """
        )
        self.layout_principal.addWidget(self.titulo)

        # LISTA DE DOCUMENTOS
        self.lista_documentos = QListWidget()
        self.lista_documentos.setSelectionMode(QListWidget.SingleSelection)
        self.lista_documentos.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.lista_documentos.setMinimumHeight(100)

        # Atualiza a prévia sempre que a seleção de arquivo mudar
        self.lista_documentos.itemSelectionChanged.connect(self.atualizar_preview)

        self.layout_principal.addWidget(self.lista_documentos, 1)

        # ÁREA DE MONTAGEM
        self.area_montagem = QFrame()
        self.area_montagem.setFrameShape(QFrame.StyledPanel)
        self.layout_montagem = QVBoxLayout(self.area_montagem)
        self.layout_montagem.setContentsMargins(5, 5, 5, 5)
        self.layout_montagem.setSpacing(5)

        # PREVIEW
        self.label_preview_titulo = QLabel("Prévia do novo nome:")
        self.label_preview_titulo.setAlignment(Qt.AlignCenter)
        self.layout_montagem.addWidget(self.label_preview_titulo)

        self.label_preview = QLabel("---")
        self.label_preview.setAlignment(Qt.AlignCenter)
        self.label_preview.setWordWrap(True)
        self.label_preview.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                padding: 6px;
                border: 1px solid #999999;
                background-color: #f5f5f5;
                color: #222222;
            }
            """
        )
        self.layout_montagem.addWidget(self.label_preview)

        # COMBOS DE SELEÇÃO
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(TIPOS_DOCUMENTO)
        self.combo_tipo.currentIndexChanged.connect(self.tipo_documento_alterado)
        self.layout_montagem.addWidget(self.combo_tipo)

        self.combo_segunda = QComboBox()
        self.combo_segunda.currentIndexChanged.connect(self.segunda_caixa_alterada)
        self.layout_montagem.addWidget(self.combo_segunda)

        self.combo_terceira = QComboBox()
        self.combo_terceira.currentIndexChanged.connect(self.terceira_caixa_alterada)
        self.layout_montagem.addWidget(self.combo_terceira)
        self.combo_terceira.hide()

        self.layout_principal.addWidget(self.area_montagem)

        # BOTÃO DE RENOMEAÇÃO (VERDE ESCURO)
        self.botao_renomear = QPushButton("APLICAR RENOMEAÇÃO")
        self.botao_renomear.setMinimumHeight(40)
        self.botao_renomear.setStyleSheet(
            """
            QPushButton {
                background-color: #1e7e34;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #155724;
            }
            QPushButton:pressed {
                background-color: #0b2e13;
            }
            """
        )
        self.botao_renomear.clicked.connect(self.renomear_documento)

        self.layout_principal.addWidget(self.botao_renomear)

    def set_nome_municipio(self, nome):
        self.nome_municipio = nome.strip()
        self.atualizar_preview()

    def set_pasta_municipio(self, pasta):
        self.pasta_municipio = pasta
        self.carregar_documentos()

    def carregar_documentos(self):
        self.lista_documentos.clear()

        if not self.pasta_municipio:
            self.atualizar_preview()
            return

        pasta = Path(self.pasta_municipio)

        if not pasta.exists() or not pasta.is_dir():
            self.atualizar_preview()
            return

        try:
            arquivos = sorted(
                [arquivo for arquivo in pasta.iterdir() if arquivo.is_file()],
                key=lambda arquivo: arquivo.name.lower(),
            )
        except OSError:
            self.atualizar_preview()
            return

        for arquivo in arquivos:
            item = QListWidgetItem(arquivo.name)
            item.setData(Qt.UserRole, str(arquivo))
            self.lista_documentos.addItem(item)

        self.atualizar_preview()

    def tipo_documento_alterado(self):
        self.atualizar_segunda_caixa()
        self.atualizar_terceira_caixa()
        self.atualizar_preview()

    def atualizar_segunda_caixa(self):
        tipo = self.combo_tipo.currentText()
        self.combo_segunda.blockSignals(True)
        self.combo_segunda.clear()

        if tipo in ["Contrato", "Procuração", "Kit Prefeito"]:
            self.combo_segunda.setEnabled(False)
        elif tipo == "Aditivo":
            self.combo_segunda.setEnabled(True)
            self.combo_segunda.addItems(OPCOES_ADITIVO)
        elif tipo == "Relatório de Assinaturas":
            self.combo_segunda.setEnabled(True)
            self.combo_segunda.addItems(OPCOES_RELATORIO)
        elif tipo == "Publicação":
            self.combo_segunda.setEnabled(True)
            self.combo_segunda.addItems(OPCOES_PUBLICACAO)

        self.combo_segunda.blockSignals(False)

    def atualizar_terceira_caixa(self):
        tipo = self.combo_tipo.currentText()
        segunda = self.combo_segunda.currentText()

        mostrar = segunda == "Aditivo" and tipo in [
            "Relatório de Assinaturas",
            "Publicação",
        ]

        self.combo_terceira.blockSignals(True)
        self.combo_terceira.clear()

        if mostrar:
            self.combo_terceira.addItems(OPCOES_TERCEIRA_CAIXA)
            self.combo_terceira.show()
        else:
            self.combo_terceira.hide()

        self.combo_terceira.blockSignals(False)

    def segunda_caixa_alterada(self):
        self.atualizar_terceira_caixa()
        self.atualizar_preview()

    def terceira_caixa_alterada(self):
        self.atualizar_preview()

    @staticmethod
    def limpar_texto(texto):
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(
            caractere for caractere in texto if not unicodedata.combining(caractere)
        )
        texto = texto.upper()
        texto = re.sub(r'[<>:"/\\|?*]', "", texto)
        texto = re.sub(r"[^A-Z0-9 ]", "", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    def montar_nome(self):
        partes = []

        municipio = self.limpar_texto(self.nome_municipio)
        if municipio:
            partes.append(municipio)

        tipo = self.limpar_texto(self.combo_tipo.currentText())
        if tipo:
            partes.append(tipo)

        if self.combo_segunda.isEnabled():
            segunda = self.combo_segunda.currentText()
            if segunda:
                partes.append(self.limpar_texto(segunda))

        if self.combo_terceira.isVisible():
            terceira = self.combo_terceira.currentText()
            if terceira:
                partes.append(self.limpar_texto(terceira))

        return "_".join(partes)

    def atualizar_preview(self):
        nome = self.montar_nome()
        item = self.lista_documentos.currentItem()

        if item is not None:
            caminho = Path(item.data(Qt.UserRole))
            extensao = caminho.suffix
            nome_preview = (nome + extensao) if nome else "---"
        else:
            nome_preview = nome if nome else "---"

        self.label_preview.setText(nome_preview)

    def obter_documento_selecionado(self):
        item = self.lista_documentos.currentItem()
        if item is None:
            return None
        return Path(item.data(Qt.UserRole))

    def verificar_nome_disponivel(self, caminho_origem, caminho_destino):
        if caminho_origem.resolve() == caminho_destino.resolve():
            return False, "O novo nome é igual ao nome atual."

        if caminho_destino.exists():
            return False, "Já existe um arquivo com esse nome na pasta."

        return True, ""

    def renomear_documento(self):
        arquivo_atual = self.obter_documento_selecionado()

        if arquivo_atual is None:
            self.label_preview.setText("SELECIONE UM DOCUMENTO")
            return

        if not self.nome_municipio.strip():
            self.label_preview.setText("INFORME O MUNICÍPIO NA ÁREA INICIAL")
            return

        novo_nome_base = self.montar_nome()

        if not novo_nome_base:
            self.label_preview.setText("NÃO FOI POSSÍVEL MONTAR O NOME")
            return

        novo_nome = novo_nome_base + arquivo_atual.suffix
        novo_caminho = arquivo_atual.parent / novo_nome

        disponivel, mensagem = self.verificar_nome_disponivel(
            arquivo_atual, novo_caminho
        )

        if not disponivel:
            self.label_preview.setText(mensagem)
            return

        try:
            arquivo_atual.rename(novo_caminho)
        except OSError as erro:
            self.label_preview.setText(f"ERRO AO RENOMEAR: {erro}")
            return

        self.carregar_documentos()

        itens = self.lista_documentos.findItems(novo_nome, Qt.MatchExactly)

        if itens:
            self.lista_documentos.setCurrentItem(itens[0])

        self.atualizar_preview()
        self.arquivo_renomeado.emit()