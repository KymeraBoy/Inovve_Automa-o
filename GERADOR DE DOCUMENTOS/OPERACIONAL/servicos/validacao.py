from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from modelos.documento import Documento


ORIGEM_COD_RE = re.compile(r"^[A-Z0-9]{3}_[A-Z0-9]{4}$")
DATA_BR_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def extrair_subtipo_normalizado(subtipo: str) -> str:
    return subtipo.upper().strip().replace("-", "_").replace(" ", "_")


def parse_monetario_br(entrada: str) -> Decimal:
    valor = (entrada or "").strip()
    if not valor:
        raise ValueError("Valor vazio")

    valor = re.sub(r"[^\d,.-]", "", valor)
    if not valor:
        raise ValueError("Valor invalido")

    if "," in valor and "." in valor:
        if valor.rfind(",") > valor.rfind("."):
            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")
        else:
            valor = valor.replace(",", "")
    elif "," in valor:
        partes = valor.split(",")
        if len(partes[-1]) <= 2:
            valor = valor.replace(".", "")
            valor = valor.replace(",", ".")
        else:
            valor = valor.replace(",", "")
    elif "." in valor:
        partes = valor.split(".")
        if len(partes[-1]) > 2:
            valor = valor.replace(".", "")

    try:
        numero = Decimal(valor)
    except InvalidOperation as exc:
        raise ValueError("Valor invalido") from exc

    return numero.quantize(Decimal("0.01"))


def formatar_monetario_br(entrada: str) -> str:
    numero = parse_monetario_br(entrada)
    inteiro, decimal = f"{numero:.2f}".split(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    return f"R$ {inteiro},{decimal}"


def _campo_imagem_preenchido(documento: Documento, chave: str) -> bool:
    return bool((documento.imagens.get(chave, "") or "").strip())


def validar_documento(documento: Documento) -> list[str]:
    erros: list[str] = []

    if not documento.municipio.strip():
        erros.append("Municipio nao informado.")
    if not documento.empresa.strip():
        erros.append("Empresa nao informada.")
    if documento.tipo not in {"REC", "REQ", "OFI"}:
        erros.append("Tipo invalido.")
    if not documento.subtipo.strip():
        erros.append("Subtipo nao informado.")
    if not documento.numero.strip():
        erros.append("Numero do documento nao informado.")

    if documento.tipo == "OFI":
        if documento.origem_tipo not in {"REC", "REQ"}:
            erros.append("Origem do OFI deve ser REC ou REQ.")
        if not ORIGEM_COD_RE.fullmatch(documento.origem_codigo.strip().upper()):
            erros.append("Codigo de origem do OFI invalido (use XXX_XXXX).")

    subtipo = extrair_subtipo_normalizado(documento.subtipo)

    if "PERDA_NOS_REATORES" in subtipo:
        if not documento.periodo_qip.strip():
            erros.append("Periodo/QIP nao informado para Perda nos Reatores.")
        if not documento.valor_faturamento.strip():
            erros.append("Valor de faturamento nao informado para Perda nos Reatores.")
        else:
            try:
                parse_monetario_br(documento.valor_faturamento)
            except ValueError:
                erros.append("Valor de faturamento invalido para Perda nos Reatores.")
        if not (_campo_imagem_preenchido(documento, "vapor") or _campo_imagem_preenchido(documento, "fluorescente")):
            erros.append("Informe ao menos uma imagem (vapor ou fluorescente) para Perda nos Reatores.")

    if "PERDA_POR_TRANSFORMACAO" in subtipo:
        obrigatorias = ["identificacao", "comprovacao", "consumo", "faturamento"]
        for chave in obrigatorias:
            if not _campo_imagem_preenchido(documento, chave):
                erros.append(f"Imagem obrigatoria nao informada: {chave}.")

    if "ESCLARECIMENTO_PAGAMENTO" in subtipo:
        if not documento.numero_comprovante.strip():
            erros.append("Numero do comprovante nao informado para Esclarecimento de Pagamento.")
        if not documento.valor_pago.strip():
            erros.append("Valor pago nao informado para Esclarecimento de Pagamento.")
        else:
            try:
                parse_monetario_br(documento.valor_pago)
            except ValueError:
                erros.append("Valor pago invalido para Esclarecimento de Pagamento.")
        if not documento.data_pagamento.strip():
            erros.append("Data do pagamento nao informada para Esclarecimento de Pagamento.")
        elif not DATA_BR_RE.fullmatch(documento.data_pagamento.strip()):
            erros.append("Data do pagamento invalida (use DD/MM/AAAA).")

    if documento.tipo == "OFI" and subtipo == "PAGAMENTO_DE_AJUSTE":
        campos_obrigatorios = {
            "ajuste_reclamacao": "Reclamacao",
            "ajuste_data_reclamacao": "Data da reclamacao",
            "ajuste_data_primeiro_pagamento": "Data do primeiro pagamento",
            "ajuste_valor_primeiro_pagamento": "Valor do primeiro pagamento",
            "ajuste_comprovante_primeiro_pagamento": "Comprovante do primeiro pagamento",
            "ajuste_valor_pagamento_complementar": "Valor do pagamento complementar",
            "ajuste_data_pagamento_complementar": "Data do pagamento complementar",
            "ajuste_comprovante_pagamento_complementar": "Comprovante do pagamento complementar",
            "ajuste_data_disponibilizacao": "Data de disponibilizacao",
            "ajuste_data_efetivo_pagamento_complementar": "Data do efetivo pagamento complementar",
            "ajuste_periodo_decorrido": "Periodo decorrido",
            "ajuste_data_pagamento": "Data do pagamento",
            "ajuste_termo_inicial": "Termo inicial",
            "ajuste_termo_final": "Termo final",
            "ajuste_numero_processo_aneel": "Numero do processo ANEEL",
            "ajuste_explicacao_data_inicial": "Explicacao da data inicial",
            "ajuste_explicacao_data_final": "Explicacao da data final",
        }
        for campo, rotulo in campos_obrigatorios.items():
            if not getattr(documento, campo).strip():
                erros.append(f"{rotulo} nao informado para Pagamento de Ajuste.")

        campos_monetarios = {
            "ajuste_valor_primeiro_pagamento": "Valor do primeiro pagamento",
            "ajuste_valor_pagamento_complementar": "Valor do pagamento complementar",
        }
        for campo, rotulo in campos_monetarios.items():
            if not getattr(documento, campo).strip():
                continue
            try:
                parse_monetario_br(getattr(documento, campo))
            except ValueError:
                erros.append(f"{rotulo} invalido para Pagamento de Ajuste.")

        campos_data = {
            "ajuste_data_reclamacao": "Data da reclamacao",
            "ajuste_data_primeiro_pagamento": "Data do primeiro pagamento",
            "ajuste_data_pagamento_complementar": "Data do pagamento complementar",
            "ajuste_data_disponibilizacao": "Data de disponibilizacao",
            "ajuste_data_efetivo_pagamento_complementar": "Data do efetivo pagamento complementar",
            "ajuste_data_pagamento": "Data do pagamento",
            "ajuste_termo_inicial": "Termo inicial",
            "ajuste_termo_final": "Termo final",
        }
        for campo, rotulo in campos_data.items():
            valor = getattr(documento, campo).strip()
            if valor and not DATA_BR_RE.fullmatch(valor):
                erros.append(f"{rotulo} invalida (use DD/MM/AAAA).")

    return erros
