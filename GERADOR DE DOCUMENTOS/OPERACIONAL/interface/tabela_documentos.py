from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QHeaderView, QTableWidget, QTableWidgetItem

from modelos.documento import Documento


class TabelaDocumentos(QTableWidget):
    """Tabela principal da fila operacional."""

    campoEditado = Signal(int, str, object)
    linhaSelecionada = Signal(int)

    COL_ID = 0
    COL_MUNICIPIO = 1
    COL_EMPRESA = 2
    COL_TIPO = 3
    COL_SUBTIPO = 4
    COL_UC = 5
    COL_NUMERO = 6
    COL_STATUS = 7

    def __init__(
        self,
        municipios: list[str],
        empresas: list[str],
        subtipos_por_tipo: dict[str, list[str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._municipios = municipios
        self._empresas = empresas
        self._subtipos_por_tipo = subtipos_por_tipo
        self._rebuild = False

        self.setColumnCount(8)
        self.setHorizontalHeaderLabels(
            ["No", "Municipio", "Empresa", "Tipo", "Subtipo", "UC", "Numero", "Status"]
        )

        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_ID, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_MUNICIPIO, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_EMPRESA, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_TIPO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_SUBTIPO, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_UC, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_NUMERO, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)

        self.itemChanged.connect(self._on_item_changed)
        self.itemSelectionChanged.connect(self._on_selection_changed)

    def atualizar_opcoes(
        self,
        municipios: list[str],
        empresas: list[str],
        subtipos_por_tipo: dict[str, list[str]],
    ) -> None:
        self._municipios = municipios
        self._empresas = empresas
        self._subtipos_por_tipo = subtipos_por_tipo

    def set_documentos(self, documentos: list[Documento], selected_row: int | None = None) -> None:
        self._rebuild = True
        atual = self.currentRow() if selected_row is None else selected_row

        self.setRowCount(0)
        for row, documento in enumerate(documentos):
            self.insertRow(row)
            self._preencher_linha(row, documento)

        self._rebuild = False

        if self.rowCount() > 0:
            if atual is None or atual < 0:
                atual = 0
            atual = min(atual, self.rowCount() - 1)
            self.selectRow(atual)

    def _preencher_linha(self, row: int, documento: Documento) -> None:
        item_id = QTableWidgetItem(str(documento.doc_id))
        item_id.setFlags(item_id.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_ID, item_id)

        combo_municipio = self._criar_combo([""] + self._municipios, documento.municipio)
        combo_municipio.currentTextChanged.connect(
            lambda texto, r=row: self.campoEditado.emit(r, "municipio", texto)
        )
        self.setCellWidget(row, self.COL_MUNICIPIO, combo_municipio)

        combo_empresa = self._criar_combo([""] + self._empresas, documento.empresa, editable=True)
        combo_empresa.currentTextChanged.connect(
            lambda texto, r=row: self.campoEditado.emit(r, "empresa", texto.strip().upper())
        )
        self.setCellWidget(row, self.COL_EMPRESA, combo_empresa)

        combo_tipo = self._criar_combo(["REC", "REQ", "OFI"], documento.tipo or "REC")
        combo_tipo.currentTextChanged.connect(
            lambda texto, r=row: self.campoEditado.emit(r, "tipo", texto)
        )
        self.setCellWidget(row, self.COL_TIPO, combo_tipo)

        subtipos = self._subtipos_por_tipo.get(documento.tipo, [])
        combo_subtipo = self._criar_combo([""] + subtipos, documento.subtipo, editable=False)
        combo_subtipo.currentTextChanged.connect(
            lambda texto, r=row: self.campoEditado.emit(r, "subtipo", texto)
        )
        self.setCellWidget(row, self.COL_SUBTIPO, combo_subtipo)

        self.setItem(row, self.COL_UC, QTableWidgetItem(documento.uc))
        self.setItem(row, self.COL_NUMERO, QTableWidgetItem(documento.numero))

        item_status = QTableWidgetItem(documento.status)
        item_status.setFlags(item_status.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.setItem(row, self.COL_STATUS, item_status)

    def _criar_combo(self, opcoes: list[str], valor: str, editable: bool = False) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(editable)
        combo.addItems(opcoes)

        if valor in opcoes:
            combo.setCurrentText(valor)
        elif editable and valor:
            combo.setCurrentText(valor)
        elif opcoes:
            combo.setCurrentIndex(0)

        return combo

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if self._rebuild:
            return
        row = item.row()
        col = item.column()
        if col == self.COL_UC:
            self.campoEditado.emit(row, "uc", item.text().strip())
        elif col == self.COL_NUMERO:
            self.campoEditado.emit(row, "numero", item.text().strip())

    def _on_selection_changed(self) -> None:
        row = self.currentRow()
        if row >= 0:
            self.linhaSelecionada.emit(row)
