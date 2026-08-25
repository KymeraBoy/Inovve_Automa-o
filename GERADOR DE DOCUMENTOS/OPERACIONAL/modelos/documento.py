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
    numero_comprovante: str = ""
    valor_pago: str = ""
    data_pagamento: str = ""
    ajuste_reclamacao: str = ""
    ajuste_data_reclamacao: str = ""
    ajuste_data_primeiro_pagamento: str = ""
    ajuste_valor_primeiro_pagamento: str = ""
    ajuste_comprovante_primeiro_pagamento: str = ""
    ajuste_valor_pagamento_complementar: str = ""
    ajuste_data_pagamento_complementar: str = ""
    ajuste_comprovante_pagamento_complementar: str = ""
    ajuste_data_disponibilizacao: str = ""
    ajuste_data_efetivo_pagamento_complementar: str = ""
    ajuste_periodo_decorrido: str = ""
    ajuste_data_pagamento: str = ""
    ajuste_termo_inicial: str = ""
    ajuste_termo_final: str = ""
    ajuste_numero_processo_aneel: str = ""
    ajuste_explicacao_data_inicial: str = ""
    ajuste_explicacao_data_final: str = ""
    imagens: dict[str, str] = field(default_factory=dict)
    ofi_item_flags: dict[str, bool] = field(default_factory=dict)
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
            "numero_comprovante": self.numero_comprovante,
            "valor_pago": self.valor_pago,
            "data_pagamento": self.data_pagamento,
            "ajuste_reclamacao": self.ajuste_reclamacao,
            "ajuste_data_reclamacao": self.ajuste_data_reclamacao,
            "ajuste_data_primeiro_pagamento": self.ajuste_data_primeiro_pagamento,
            "ajuste_valor_primeiro_pagamento": self.ajuste_valor_primeiro_pagamento,
            "ajuste_comprovante_primeiro_pagamento": self.ajuste_comprovante_primeiro_pagamento,
            "ajuste_valor_pagamento_complementar": self.ajuste_valor_pagamento_complementar,
            "ajuste_data_pagamento_complementar": self.ajuste_data_pagamento_complementar,
            "ajuste_comprovante_pagamento_complementar": self.ajuste_comprovante_pagamento_complementar,
            "ajuste_data_disponibilizacao": self.ajuste_data_disponibilizacao,
            "ajuste_data_efetivo_pagamento_complementar": self.ajuste_data_efetivo_pagamento_complementar,
            "ajuste_periodo_decorrido": self.ajuste_periodo_decorrido,
            "ajuste_data_pagamento": self.ajuste_data_pagamento,
            "ajuste_termo_inicial": self.ajuste_termo_inicial,
            "ajuste_termo_final": self.ajuste_termo_final,
            "ajuste_numero_processo_aneel": self.ajuste_numero_processo_aneel,
            "ajuste_explicacao_data_inicial": self.ajuste_explicacao_data_inicial,
            "ajuste_explicacao_data_final": self.ajuste_explicacao_data_final,
            "imagens": dict(self.imagens),
            "ofi_item_flags": dict(self.ofi_item_flags),
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
            numero_comprovante=str(data.get("numero_comprovante", "")),
            valor_pago=str(data.get("valor_pago", "")),
            data_pagamento=str(data.get("data_pagamento", "")),
            ajuste_reclamacao=str(data.get("ajuste_reclamacao", "")),
            ajuste_data_reclamacao=str(data.get("ajuste_data_reclamacao", "")),
            ajuste_data_primeiro_pagamento=str(data.get("ajuste_data_primeiro_pagamento", "")),
            ajuste_valor_primeiro_pagamento=str(data.get("ajuste_valor_primeiro_pagamento", "")),
            ajuste_comprovante_primeiro_pagamento=str(data.get("ajuste_comprovante_primeiro_pagamento", "")),
            ajuste_valor_pagamento_complementar=str(data.get("ajuste_valor_pagamento_complementar", "")),
            ajuste_data_pagamento_complementar=str(data.get("ajuste_data_pagamento_complementar", "")),
            ajuste_comprovante_pagamento_complementar=str(data.get("ajuste_comprovante_pagamento_complementar", "")),
            ajuste_data_disponibilizacao=str(data.get("ajuste_data_disponibilizacao", "")),
            ajuste_data_efetivo_pagamento_complementar=str(data.get("ajuste_data_efetivo_pagamento_complementar", "")),
            ajuste_periodo_decorrido=str(data.get("ajuste_periodo_decorrido", "")),
            ajuste_data_pagamento=str(data.get("ajuste_data_pagamento", "")),
            ajuste_termo_inicial=str(data.get("ajuste_termo_inicial", "")),
            ajuste_termo_final=str(data.get("ajuste_termo_final", "")),
            ajuste_numero_processo_aneel=str(data.get("ajuste_numero_processo_aneel", "")),
            ajuste_explicacao_data_inicial=str(data.get("ajuste_explicacao_data_inicial", "")),
            ajuste_explicacao_data_final=str(data.get("ajuste_explicacao_data_final", "")),
            imagens=dict(data.get("imagens", {}) or {}),
            ofi_item_flags={str(chave): bool(valor) for chave, valor in dict(data.get("ofi_item_flags", {}) or {}).items()},
            info_adicional=str(data.get("info_adicional", "")),
            status=str(data.get("status", STATUS_AGUARDANDO)) or STATUS_AGUARDANDO,
            erros=list(data.get("erros", []) or []),
        )
