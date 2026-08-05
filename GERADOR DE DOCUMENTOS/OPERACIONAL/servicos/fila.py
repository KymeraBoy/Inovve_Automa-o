from __future__ import annotations

import json
from pathlib import Path

from modelos.documento import Documento, STATUS_AGUARDANDO


class FilaDocumentos:
    """Armazena e persiste a fila de documentos da interface operacional."""

    def __init__(self) -> None:
        self.documentos: list[Documento] = []
        self._next_id = 1

    def adicionar(self, documento: Documento | None = None) -> Documento:
        if documento is None:
            documento = Documento(doc_id=self._next_id)
        if documento.doc_id <= 0:
            documento.doc_id = self._next_id
        self._next_id = max(self._next_id, documento.doc_id + 1)
        documento.status = documento.status or STATUS_AGUARDANDO
        self.documentos.append(documento)
        return documento

    def remover_por_indice(self, indice: int) -> None:
        if 0 <= indice < len(self.documentos):
            self.documentos.pop(indice)

    def atualizar_campo(self, indice: int, campo: str, valor) -> None:
        if 0 <= indice < len(self.documentos):
            setattr(self.documentos[indice], campo, valor)

    def limpar_status(self) -> None:
        for documento in self.documentos:
            documento.status = STATUS_AGUARDANDO
            documento.erros = []

    def salvar(self, arquivo: Path) -> None:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        payload = [doc.to_dict() for doc in self.documentos]
        arquivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def carregar(self, arquivo: Path) -> None:
        if not arquivo.exists():
            self.documentos = []
            self._next_id = 1
            return

        raw = arquivo.read_text(encoding="utf-8").strip()
        if not raw:
            self.documentos = []
            self._next_id = 1
            return

        data = json.loads(raw)
        self.documentos = [Documento.from_dict(item) for item in data]
        maior_id = max((doc.doc_id for doc in self.documentos), default=0)
        self._next_id = maior_id + 1
