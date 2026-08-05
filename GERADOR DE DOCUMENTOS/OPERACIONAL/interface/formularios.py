from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from modelos.documento import Documento
from servicos.validacao import formatar_monetario_br


class PainelDetalhesDocumento(QWidget):
    """Painel lateral com campos dinamicos por tipo/subtipo."""

    campoEditado = Signal(str, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._loading = False

        layout = QVBoxLayout(self)

        self.lbl_titulo = QLabel("Detalhes do documento selecionado")
        layout.addWidget(self.lbl_titulo)

        self.grp_ofi = QGroupBox("Campos de OFI")
        form_ofi = QFormLayout(self.grp_ofi)
        self.cmb_origem_tipo = QComboBox()
        self.cmb_origem_tipo.addItems(["", "REC", "REQ"])
        self.txt_origem_codigo = QLineEdit()
        self.txt_origem_codigo.setPlaceholderText("XXX_XXXX")
        form_ofi.addRow("Documento origem", self.cmb_origem_tipo)
        form_ofi.addRow("Codigo origem", self.txt_origem_codigo)
        layout.addWidget(self.grp_ofi)

        self.grp_reatores = QGroupBox("Campos de Perda nos Reatores")
        form_reatores = QFormLayout(self.grp_reatores)
        self.txt_valor_faturamento = QLineEdit()
        self.txt_valor_faturamento.setPlaceholderText("R$ 0,00")
        self.txt_periodo_qip = QLineEdit()
        self.txt_periodo_qip.setPlaceholderText("Ex: Janeiro de 2024")
        form_reatores.addRow("Valor faturamento", self.txt_valor_faturamento)
        form_reatores.addRow("Periodo/QIP", self.txt_periodo_qip)
        self._img_vapor = self._criar_campo_imagem("vapor")
        self._img_fluorescente = self._criar_campo_imagem("fluorescente")
        form_reatores.addRow("Imagem vapor", self._img_vapor["container"])
        form_reatores.addRow("Imagem fluorescente", self._img_fluorescente["container"])
        layout.addWidget(self.grp_reatores)

        self.grp_transformacao = QGroupBox("Campos de Perda por Transformacao")
        form_transf = QFormLayout(self.grp_transformacao)
        self._img_identificacao = self._criar_campo_imagem("identificacao")
        self._img_comprovacao = self._criar_campo_imagem("comprovacao")
        self._img_consumo = self._criar_campo_imagem("consumo")
        self._img_faturamento = self._criar_campo_imagem("faturamento")
        form_transf.addRow("Imagem identificacao", self._img_identificacao["container"])
        form_transf.addRow("Imagem comprovacao", self._img_comprovacao["container"])
        form_transf.addRow("Imagem consumo", self._img_consumo["container"])
        form_transf.addRow("Imagem faturamento", self._img_faturamento["container"])
        layout.addWidget(self.grp_transformacao)

        self.grp_adicional = QGroupBox("Informacoes adicionais")
        form_adicional = QFormLayout(self.grp_adicional)
        self.txt_info_adicional = QTextEdit()
        self.txt_info_adicional.setPlaceholderText("Observacoes ou dados extras")
        form_adicional.addRow(self.txt_info_adicional)
        layout.addWidget(self.grp_adicional)

        layout.addStretch(1)

        self.cmb_origem_tipo.currentTextChanged.connect(
            lambda valor: self._emitir("origem_tipo", valor)
        )
        self.txt_origem_codigo.editingFinished.connect(
            lambda: self._emitir("origem_codigo", self.txt_origem_codigo.text().strip().upper())
        )
        self.txt_valor_faturamento.editingFinished.connect(self._formatar_e_emitir_valor)
        self.txt_periodo_qip.editingFinished.connect(
            lambda: self._emitir("periodo_qip", self.txt_periodo_qip.text().strip())
        )
        self.txt_info_adicional.textChanged.connect(
            lambda: self._emitir("info_adicional", self.txt_info_adicional.toPlainText().strip())
        )

        self._set_visibility("REC", "")

    def _criar_campo_imagem(self, chave: str) -> dict[str, object]:
        container = QWidget()
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)

        txt = QLineEdit()
        txt.setPlaceholderText("Selecione um arquivo")
        btn = QPushButton("Selecionar")

        btn.clicked.connect(lambda: self._selecionar_imagem(chave, txt))
        txt.editingFinished.connect(lambda: self._emitir(f"imagem:{chave}", txt.text().strip()))

        h.addWidget(txt)
        h.addWidget(btn)
        return {"container": container, "line": txt, "button": btn}

    def _selecionar_imagem(self, chave: str, line_edit: QLineEdit) -> None:
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.bmp *.webp);;Todos os arquivos (*.*)",
        )
        if not arquivo:
            return
        line_edit.setText(str(Path(arquivo)))
        self._emitir(f"imagem:{chave}", line_edit.text().strip())

    def carregar_documento(self, documento: Documento | None) -> None:
        self._loading = True
        if documento is None:
            self.lbl_titulo.setText("Nenhum documento selecionado")
            self.cmb_origem_tipo.setCurrentText("")
            self.txt_origem_codigo.setText("")
            self.txt_valor_faturamento.setText("")
            self.txt_periodo_qip.setText("")
            self.txt_info_adicional.setPlainText("")
            self._set_imagem("vapor", "")
            self._set_imagem("fluorescente", "")
            self._set_imagem("identificacao", "")
            self._set_imagem("comprovacao", "")
            self._set_imagem("consumo", "")
            self._set_imagem("faturamento", "")
            self._set_visibility("REC", "")
            self._loading = False
            return

        self.lbl_titulo.setText(f"Detalhes do documento #{documento.doc_id}")
        self.cmb_origem_tipo.setCurrentText(documento.origem_tipo)
        self.txt_origem_codigo.setText(documento.origem_codigo)
        self.txt_valor_faturamento.setText(documento.valor_faturamento)
        self.txt_periodo_qip.setText(documento.periodo_qip)
        self.txt_info_adicional.setPlainText(documento.info_adicional)
        self._set_imagem("vapor", documento.imagens.get("vapor", ""))
        self._set_imagem("fluorescente", documento.imagens.get("fluorescente", ""))
        self._set_imagem("identificacao", documento.imagens.get("identificacao", ""))
        self._set_imagem("comprovacao", documento.imagens.get("comprovacao", ""))
        self._set_imagem("consumo", documento.imagens.get("consumo", ""))
        self._set_imagem("faturamento", documento.imagens.get("faturamento", ""))
        self._set_visibility(documento.tipo, documento.subtipo)
        self._loading = False

    def atualizar_contexto_tipo_subtipo(self, tipo: str, subtipo: str) -> None:
        self._set_visibility(tipo, subtipo)

    def _set_imagem(self, chave: str, valor: str) -> None:
        mapa = {
            "vapor": self._img_vapor,
            "fluorescente": self._img_fluorescente,
            "identificacao": self._img_identificacao,
            "comprovacao": self._img_comprovacao,
            "consumo": self._img_consumo,
            "faturamento": self._img_faturamento,
        }
        mapa[chave]["line"].setText(valor)

    def _formatar_e_emitir_valor(self) -> None:
        if self._loading:
            return

        valor = self.txt_valor_faturamento.text().strip()
        if not valor:
            self._emitir("valor_faturamento", "")
            return

        try:
            formatado = formatar_monetario_br(valor)
            self.txt_valor_faturamento.setText(formatado)
            self._emitir("valor_faturamento", formatado)
        except ValueError:
            self._emitir("valor_faturamento", valor)

    def _emitir(self, campo: str, valor: object) -> None:
        if self._loading:
            return
        self.campoEditado.emit(campo, valor)

    def _set_visibility(self, tipo: str, subtipo: str) -> None:
        normalizado = subtipo.upper().replace("-", "_").replace(" ", "_")
        self.grp_ofi.setVisible(tipo == "OFI")
        self.grp_reatores.setVisible("PERDA_NOS_REATORES" in normalizado)
        self.grp_transformacao.setVisible("PERDA_POR_TRANSFORMACAO" in normalizado)
