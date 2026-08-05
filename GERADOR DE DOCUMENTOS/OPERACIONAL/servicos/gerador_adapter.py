from __future__ import annotations

from modelos.documento import Documento, STATUS_ERRO
from servicos.gerador_operacional import GeradorOperacional


class GeradorAdapter:
    """
    Camada de adaptacao entre a fila operacional e o motor dedicado de geracao.
    """

    def __init__(self) -> None:
        self._gerador = GeradorOperacional()

    def processar(self, documentos_validos: list[Documento]) -> list[str]:
        mensagens: list[str] = []
        resultados = self._gerador.processar_lote(documentos_validos)
        for documento, resultado in zip(documentos_validos, resultados):
            if resultado.sucesso:
                documento.status = "Gerado"
                mensagens.append(
                    f"Documento {documento.doc_id}: gerado com sucesso. PDF: {resultado.pdf_path}"
                )
            else:
                documento.status = STATUS_ERRO
                documento.erros = [resultado.mensagem]
                mensagens.append(
                    f"Documento {documento.doc_id}: falha na geracao. Motivo: {resultado.mensagem}"
                )
        return mensagens
