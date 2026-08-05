from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


STATUS_AGUARDANDO = "Aguardando"
STATUS_VALIDO = "Valido"
STATUS_ERRO = "Erro"
STATUS_PENDENTE_GERACAO = "Pendente geracao"


@dataclass
class Documento:
    """Representa um chamado/documento na fila operacional."""

    doc_id: int
    municipio: str = ""
    empresa: str = ""
    tipo: str = "REC"
    subtipo: str = ""
    numero: str = ""
    uc: str = ""
    origem_tipo: str = ""
    origem_codigo: str = ""
    valor_faturamento: str = ""
    periodo_qip: str = ""
    imagens: dict[str, str] = field(default_factory=dict)
    info_adicional: str = ""
    status: str = STATUS_AGUARDANDO
    erros: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "municipio": self.municipio,
            "empresa": self.empresa,
            "tipo": self.tipo,
            "subtipo": self.subtipo,
            "numero": self.numero,
            "uc": self.uc,
            "origem_tipo": self.origem_tipo,
            "origem_codigo": self.origem_codigo,
            "valor_faturamento": self.valor_faturamento,
            "periodo_qip": self.periodo_qip,
            "imagens": dict(self.imagens),
            "info_adicional": self.info_adicional,
            "status": self.status,
            "erros": list(self.erros),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Documento":
        return cls(
            doc_id=int(data.get("doc_id", 0)),
            municipio=str(data.get("municipio", "")),
            empresa=str(data.get("empresa", "")),
            tipo=str(data.get("tipo", "REC")) or "REC",
            subtipo=str(data.get("subtipo", "")),
            numero=str(data.get("numero", "")),
            uc=str(data.get("uc", "")),
            origem_tipo=str(data.get("origem_tipo", "")),
            origem_codigo=str(data.get("origem_codigo", "")),
            valor_faturamento=str(data.get("valor_faturamento", "")),
            periodo_qip=str(data.get("periodo_qip", "")),
            imagens=dict(data.get("imagens", {}) or {}),
            info_adicional=str(data.get("info_adicional", "")),
            status=str(data.get("status", STATUS_AGUARDANDO)) or STATUS_AGUARDANDO,
            erros=list(data.get("erros", []) or []),
        )
