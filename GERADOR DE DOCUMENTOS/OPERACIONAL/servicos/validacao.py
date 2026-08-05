from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from modelos.documento import Documento


ORIGEM_COD_RE = re.compile(r"^[A-Z0-9]{3}_[A-Z0-9]{4}$")


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

    return erros
