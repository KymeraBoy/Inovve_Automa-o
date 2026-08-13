from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from configuracao.config import CONFIG
from interface.formularios import PainelDetalhesDocumento
from interface.tabela_documentos import TabelaDocumentos
from modelos.documento import (
    Documento,
    STATUS_AGUARDANDO,
    STATUS_ERRO,
    STATUS_VALIDO,
)
from servicos.empresas import inferir_empresa_por_municipio, listar_empresas
from servicos.fila import FilaDocumentos
from servicos.gerador_adapter import GeradorAdapter
from servicos.municipios import mapa_municipios
from servicos.validacao import validar_documento


class JanelaPrincipal(QMainWindow):
    """Janela principal da operacao em fila."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Operacional - Gerador de Documentos")
        self.resize(1400, 780)

        self._municipios_meta = mapa_municipios()
        self._empresas = listar_empresas()
        self._subtipos_por_tipo = self._carregar_subtipos()

        self._fila = FilaDocumentos()
        self._adapter = GeradorAdapter()

        self._montar_ui()
        self._carregar_fila_inicial()

    def _montar_ui(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)

        barra = QHBoxLayout()
        self.btn_adicionar = QPushButton("Novo Documento")
        self.btn_remover = QPushButton("Remover Selecionado")
        self.btn_validar = QPushButton("Validar Fila")
        self.btn_salvar = QPushButton("Salvar Fila")
        self.btn_carregar = QPushButton("Carregar Fila")
        self.btn_gerar = QPushButton("GERAR DOCUMENTOS")

        barra.addWidget(self.btn_adicionar)
        barra.addWidget(self.btn_remover)
        barra.addWidget(self.btn_validar)
        barra.addWidget(self.btn_salvar)
        barra.addWidget(self.btn_carregar)
        barra.addStretch(1)
        barra.addWidget(self.btn_gerar)

        layout.addLayout(barra)

        self.lbl_info = QLabel("Fila operacional pronta.")
        layout.addWidget(self.lbl_info)

        splitter = QSplitter()

        self.tabela = TabelaDocumentos(
            municipios=sorted(self._municipios_meta.keys()),
            empresas=self._empresas,
            subtipos_por_tipo=self._subtipos_por_tipo,
        )
        splitter.addWidget(self.tabela)

        self.painel = PainelDetalhesDocumento()
        splitter.addWidget(self.painel)
        splitter.setSizes([1000, 400])

        layout.addWidget(splitter)
        self.setCentralWidget(central)

        self.btn_adicionar.clicked.connect(self._adicionar_documento)
        self.btn_remover.clicked.connect(self._remover_documento)
        self.btn_validar.clicked.connect(self._validar_fila)
        self.btn_salvar.clicked.connect(self._salvar_fila)
        self.btn_carregar.clicked.connect(self._carregar_fila_manual)
        self.btn_gerar.clicked.connect(self._processar_fila)

        self.tabela.campoEditado.connect(self._atualizar_campo_tabela)
        self.tabela.linhaSelecionada.connect(self._selecionar_linha)
        self.painel.campoEditado.connect(self._atualizar_campo_detalhes)

    def _carregar_subtipos(self) -> dict[str, list[str]]:
        def label(stem: str) -> str:
            return stem.replace("_", " ").replace("-", " ")

        subtipos_rec = [label(f.stem) for f in sorted(CONFIG.rec_dir.glob("*.tex")) if f.is_file()]
        subtipos_ofi = [label(f.stem) for f in sorted(CONFIG.ofi_dir.glob("*.tex")) if f.is_file()]

        subtipos_req: list[str] = []
        for f in sorted(CONFIG.req_dir.glob("*.tex")):
            if f.is_file():
                subtipos_req.append(label(f.stem))

        for empresa_dir in sorted(CONFIG.req_dir.iterdir()):
            if not empresa_dir.is_dir():
                continue
            empresa = empresa_dir.name.upper()
            for f in sorted(empresa_dir.glob("*.tex")):
                if f.is_file():
                    subtipos_req.append(f"[{empresa}] {label(f.stem)}")

        return {
            "REC": subtipos_rec,
            "REQ": subtipos_req,
            "OFI": subtipos_ofi,
        }

    def _carregar_fila_inicial(self) -> None:
        try:
            self._fila.carregar(CONFIG.fila_arquivo)
        except Exception as exc:
            QMessageBox.warning(self, "Aviso", f"Nao foi possivel carregar fila inicial: {exc}")

        if not self._fila.documentos:
            self._fila.adicionar(self._novo_documento_padrao())

        self._renderizar_fila(selected_row=0)

    def _novo_documento_padrao(self) -> Documento:
        subtipo_padrao = self._subtipos_por_tipo.get("REC", [""])
        return Documento(
            doc_id=0,
            tipo="REC",
            subtipo=subtipo_padrao[0] if subtipo_padrao else "",
            status=STATUS_AGUARDANDO,
        )

    def _renderizar_fila(self, selected_row: int | None = None) -> None:
        self.tabela.atualizar_opcoes(
            municipios=sorted(self._municipios_meta.keys()),
            empresas=self._empresas,
            subtipos_por_tipo=self._subtipos_por_tipo,
        )
        self.tabela.set_documentos(self._fila.documentos, selected_row=selected_row)

        self._atualizar_resumo_fila()

    def _atualizar_resumo_fila(self) -> None:
        total = len(self._fila.documentos)
        validos = len([d for d in self._fila.documentos if d.status == STATUS_VALIDO])
        erros = len([d for d in self._fila.documentos if d.status == STATUS_ERRO])
        self.lbl_info.setText(f"Fila: {total} documento(s) | Validos: {validos} | Erros: {erros}")

    def _marcar_aguardando(self, row: int) -> None:
        if not (0 <= row < len(self._fila.documentos)):
            return

        documento = self._fila.documentos[row]
        documento.status = STATUS_AGUARDANDO
        documento.erros = []

        item_status = self.tabela.item(row, self.tabela.COL_STATUS)
        if item_status is not None:
            item_status.setText(documento.status)

        self._atualizar_resumo_fila()

    def _adicionar_documento(self) -> None:
        doc = self._novo_documento_padrao()
        self._fila.adicionar(doc)
        row = len(self._fila.documentos) - 1
        self._renderizar_fila(selected_row=row)

    def _remover_documento(self) -> None:
        row = self.tabela.currentRow()
        if row < 0:
            return
        self._fila.remover_por_indice(row)
        if not self._fila.documentos:
            self._fila.adicionar(self._novo_documento_padrao())
        self._renderizar_fila(selected_row=max(0, row - 1))

    def _selecionar_linha(self, row: int) -> None:
        if 0 <= row < len(self._fila.documentos):
            documento = self._fila.documentos[row]
            self.painel.carregar_documento(documento)

    def _atualizar_campo_tabela(self, row: int, campo: str, valor: object) -> None:
        if not (0 <= row < len(self._fila.documentos)):
            return

        documento = self._fila.documentos[row]
        precisa_renderizar = False

        if campo == "municipio":
            documento.municipio = str(valor)
            meta = self._municipios_meta.get(documento.municipio)
            if meta:
                empresa_inferida = inferir_empresa_por_municipio(meta)
                if empresa_inferida:
                    documento.empresa = empresa_inferida
                    if not documento.uc and meta.get("ip_estimada"):
                        documento.uc = meta["ip_estimada"]
            precisa_renderizar = True

        elif campo == "empresa":
            documento.empresa = str(valor).strip().upper()
        elif campo == "tipo":
            documento.tipo = str(valor)
            opcoes = self._subtipos_por_tipo.get(documento.tipo, [])
            if documento.subtipo not in opcoes:
                documento.subtipo = opcoes[0] if opcoes else ""
            self.painel.atualizar_contexto_tipo_subtipo(documento.tipo, documento.subtipo)
            precisa_renderizar = True
        elif campo == "subtipo":
            documento.subtipo = str(valor)
            self.painel.atualizar_contexto_tipo_subtipo(documento.tipo, documento.subtipo)
            precisa_renderizar = True
        elif campo == "uc":
            documento.uc = str(valor)
        elif campo == "numero":
            documento.numero = str(valor)

        self._marcar_aguardando(row)
        if precisa_renderizar:
            self._renderizar_fila(selected_row=row)

    def _atualizar_campo_detalhes(self, campo: str, valor: object) -> None:
        row = self.tabela.currentRow()
        if not (0 <= row < len(self._fila.documentos)):
            return

        documento = self._fila.documentos[row]

        if campo.startswith("imagem:"):
            chave = campo.split(":", 1)[1]
            documento.imagens[chave] = str(valor)
        elif campo == "origem_tipo":
            documento.origem_tipo = str(valor)
        elif campo == "origem_codigo":
            documento.origem_codigo = str(valor).strip().upper()
        elif campo == "valor_faturamento":
            documento.valor_faturamento = str(valor)
        elif campo == "periodo_qip":
            documento.periodo_qip = str(valor)
        elif campo == "numero_comprovante":
            documento.numero_comprovante = str(valor)
        elif campo == "valor_pago":
            documento.valor_pago = str(valor)
        elif campo == "data_pagamento":
            documento.data_pagamento = str(valor)
        elif campo == "info_adicional":
            documento.info_adicional = str(valor)
        elif campo.startswith("ofi_flag:"):
            chave = campo.split(":", 1)[1]
            documento.ofi_item_flags[chave] = bool(valor)

        self._marcar_aguardando(row)

    def _validar_fila(self) -> tuple[list[Documento], list[str]]:
        validos: list[Documento] = []
        relatorio: list[str] = []

        for idx, documento in enumerate(self._fila.documentos, start=1):
            erros = validar_documento(documento)
            documento.erros = erros
            if erros:
                documento.status = STATUS_ERRO
                relatorio.append(f"Documento {idx} (ID {documento.doc_id}) - ERRO")
                for erro in erros:
                    relatorio.append(f"  - {erro}")
            else:
                documento.status = STATUS_VALIDO
                validos.append(documento)
                relatorio.append(f"Documento {idx} (ID {documento.doc_id}) - OK")

        self._renderizar_fila(selected_row=self.tabela.currentRow())
        return validos, relatorio

    def _salvar_fila(self) -> None:
        arquivo, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar fila de documentos",
            str(CONFIG.fila_arquivo),
            "JSON (*.json)",
        )
        if not arquivo:
            return

        try:
            self._fila.salvar(Path(arquivo))
            QMessageBox.information(self, "Fila salva", f"Fila salva em:\n{arquivo}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar fila:\n{exc}")

    def _carregar_fila_manual(self) -> None:
        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Carregar fila de documentos",
            str(CONFIG.fila_arquivo.parent),
            "JSON (*.json)",
        )
        if not arquivo:
            return

        try:
            self._fila.carregar(Path(arquivo))
            if not self._fila.documentos:
                self._fila.adicionar(self._novo_documento_padrao())
            self._renderizar_fila(selected_row=0)
            QMessageBox.information(self, "Fila carregada", f"Fila carregada de:\n{arquivo}")
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar fila:\n{exc}")

    def _processar_fila(self) -> None:
        validos, relatorio = self._validar_fila()

        if not validos:
            QMessageBox.warning(
                self,
                "Validacao",
                "Nenhum documento valido para processamento.\n\n" + "\n".join(relatorio),
            )
            return

        mensagens_adapter = self._adapter.processar(validos)

        self._renderizar_fila(selected_row=self.tabela.currentRow())

        resumo = []
        resumo.append("Validacao concluida.\n")
        resumo.extend(relatorio)
        resumo.append("\nResultado da geracao:")
        resumo.extend(mensagens_adapter)

        QMessageBox.information(self, "Processamento em lote", "\n".join(resumo))

    def closeEvent(self, event) -> None:  # noqa: N802 - assinatura do Qt
        try:
            self._fila.salvar(CONFIG.fila_arquivo)
        except Exception:
            pass
        super().closeEvent(event)
