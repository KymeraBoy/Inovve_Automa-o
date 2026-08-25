from __future__ import annotations

import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from decimal import Decimal

from configuracao.config import AppConfig, CONFIG
from modelos.documento import Documento
from servicos.municipios import parse_municipio_file
from servicos.validacao import parse_monetario_br


_CMD_RE = re.compile(r"\\(?:new|provide|renew)command\s*\{\\(\w+)\}\s*\{([^}]*)\}")
_IP_ESTIMADA_COMMENT_RE = re.compile(
    r"^\s*%\s*DEDICADA\s+A\s+IP\s+ESTIMADA\b",
    re.IGNORECASE | re.MULTILINE,
)
_EMPRESA_DOC_KEYS = {"intro", "legitimidade", "anexos", "final"}
_EMPRESA_DOC_ALIASES = {
    "INTRO": "intro",
    "INTRODUCAO": "intro",
    "LEGITIMIDADE": "legitimidade",
    "ANEXO": "anexos",
    "ANEXOS": "anexos",
    "FINAL": "final",
}

MESES_CONTADOR_BASE = 115
MESES_CONTADOR_DATA_BASE = date(2026, 7, 1)
MESES_CONTADOR_MAXIMO = 120
MESES_CONTADOR_PLACEHOLDER = "<<CONTADOR_MESES>>"


@dataclass
class ResultadoGeracao:
    documento_id: int
    sucesso: bool
    mensagem: str
    tex_path: str = ""
    pdf_path: str = ""


def _parse_latex_commands(content: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in _CMD_RE.finditer(content)}


def _label(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ")


def _normalize_key(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value or "")
    no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", no_accents).strip().upper()


def _tokenize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    upper = no_accents.upper()
    underscored = re.sub(r"[^A-Z0-9]+", "_", upper)
    return re.sub(r"_+", "_", underscored).strip("_") or "SEM_NOME"


def _lpath(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/")


def _fmt_br(valor: Decimal) -> str:
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _meses_contador_atual(referencia: date | None = None) -> int:
    referencia = referencia or date.today()
    meses_passados = (
        (referencia.year - MESES_CONTADOR_DATA_BASE.year) * 12
        + (referencia.month - MESES_CONTADOR_DATA_BASE.month)
    )
    meses_atual = MESES_CONTADOR_BASE + max(0, meses_passados)
    return min(MESES_CONTADOR_MAXIMO, meses_atual)


def _atualizar_contador_meses(conteudo: str) -> str:
    return conteudo.replace(MESES_CONTADOR_PLACEHOLDER, str(_meses_contador_atual()))


def _is_truthy_flag(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "sim", "s", "yes", "y"}


def _subtype_uses_ip_estimada(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return False

    data = _parse_latex_commands(content)
    if _is_truthy_flag(data.get("usaIPEstimada", "")):
        return True
    return _IP_ESTIMADA_COMMENT_RE.search(content) is not None


def _get_ip_estimada_from_municipio(mun_dados: dict[str, str]) -> str:
    return mun_dados.get("IPestimada", "").strip() or mun_dados.get("IP_estimada", "").strip()


def _get_titulo_from_subtype(path: Path) -> str:
    data = _parse_latex_commands(path.read_text(encoding="utf-8"))
    for key in (
        "tipoRequerimento",
        "tipoReclamacao",
        "tituloDocumento",
        "assuntoDocumento",
        "tipoOficio",
    ):
        value = data.get(key, "").strip()
        if value:
            return value
    return ""


def _get_empresa_docs_from_subtype(path: Path) -> set[str]:
    """
    Le configuracao opcional da tese via macro LaTeX:
      \newcommand{\empresaDocumentos}{intro,legitimidade,anexos,final}

    Regras:
    - Se ausente/invalida: inclui todos os tipos.
    - Aceita exclusao por prefixo '-' ou '!': ex. "-anexos,-legitimidade".
    - Aceita sinonimos simples (introducao, anexo/anexos).
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return set(_EMPRESA_DOC_KEYS)

    data = _parse_latex_commands(content)
    raw = data.get("empresaDocumentos", "").strip()
    if not raw:
        return set(_EMPRESA_DOC_KEYS)

    tokens = [t for t in re.split(r"[,;|\s]+", raw) if t]
    included: set[str] = set()
    removed: set[str] = set()
    touched = False

    for token in tokens:
        excluded = token.startswith(("-", "!"))
        base = token[1:] if excluded else token
        alias = _EMPRESA_DOC_ALIASES.get(_tokenize_name(base))
        if not alias:
            continue
        touched = True
        if excluded:
            removed.add(alias)
        else:
            included.add(alias)

    if not touched:
        return set(_EMPRESA_DOC_KEYS)

    result = set(included) if included else set(_EMPRESA_DOC_KEYS)
    result.difference_update(removed)
    return result


def _build_output_name(
    documento: Documento,
    municipio_nome: str,
    subtype_stem: str,
) -> str:
    if documento.tipo == "OFI":
        return "-".join(
            [
                _tokenize_name(documento.tipo),
                _tokenize_name(documento.numero),
                _tokenize_name(municipio_nome),
                _tokenize_name(documento.origem_tipo),
                _tokenize_name(documento.origem_codigo),
            ]
        )

    parts = [
        _tokenize_name(documento.tipo),
        _tokenize_name(documento.numero),
        _tokenize_name(municipio_nome),
        _tokenize_name(subtype_stem),
    ]
    if documento.uc.strip():
        parts.append(_tokenize_name(documento.uc))
    return "-".join(parts)


def _is_fragment(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False
    return r"\documentclass" not in content and r"\begin{document}" not in content


def _build_figure_block(image_path: str) -> str:
    clean = str(Path(image_path).resolve()).replace("\\", "/")
    return (
        "\\begin{figure}[H]\n"
        "    \\centering\n"
        f"    \\includegraphics[width=\\textwidth]{{{clean}}}\n"
        "\\end{figure}"
    )


def _extract_vapor_types_from_info(info: str) -> list[str]:
    text = _normalize_key(info)
    mapping = [
        ("SODIO", "sodio"),
        ("MERCURIO", "mercurio"),
        ("METALICA", "metalica"),
    ]
    selected: list[str] = []
    for keyword, key in mapping:
        if keyword in text:
            selected.append(key)
    return selected


def _join_pt_br(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} e {items[1]}"
    return f"{', '.join(items[:-1])} e {items[-1]}"


def _build_vapor_types_text(selected_vapor_types: list[str], include_preposition: bool = True) -> str:
    options = {
        "sodio": "vapor de sodio",
        "mercurio": "vapor de mercurio",
        "metalica": "vapor metalico",
    }
    itens: list[str] = []
    for key in ("sodio", "mercurio", "metalica"):
        if key in set(selected_vapor_types):
            rotulo = options[key]
            itens.append(f"de {rotulo}" if include_preposition else rotulo)
    return _join_pt_br(itens)


def _build_lamp_types_text(selected_vapor_types: list[str], include_fluorescente: bool) -> str:
    tipos = []
    if selected_vapor_types:
        tipos.append(_build_vapor_types_text(selected_vapor_types, include_preposition=True))
    if include_fluorescente:
        tipos.append("fluorescentes")
    return _join_pt_br(tipos)


def _build_vapor_norms_text(selected_vapor_types: list[str]) -> str:
    selected_set = set(selected_vapor_types)
    if selected_set == {"sodio"}:
        return (
            "Para os reatores de lampadas de vapor de sodio, os limites maximos "
            "admissiveis de perdas encontram-se expressamente definidos na NBR "
            "13593:2011."
        )
    if selected_set == {"metalica"}:
        return (
            "Para os reatores de lampadas de vapor metalico, os limites maximos "
            "admissiveis de perdas encontram-se expressamente definidos na NBR "
            "14305:2015."
        )
    if selected_set == {"sodio", "metalica"}:
        return (
            "Para os reatores de lampadas de vapor de sodio e de vapor metalico, "
            "os limites maximos admissiveis de perdas observam a NBR 13593:2011 "
            "e a NBR 14305:2015."
        )
    if not selected_set:
        return "Para os reatores de lampadas de vapor, devem ser observadas as normas tecnicas aplicaveis da ABNT."
    return (
        "Para os reatores de lampadas "
        f"{_build_vapor_types_text(selected_vapor_types, include_preposition=True)}, "
        "devem ser observadas as normas tecnicas aplicaveis da ABNT."
    )


def _process_perda_reatores_content(conteudo_tex: str, documento: Documento) -> str:
    perda_vapor = bool((documento.imagens.get("vapor", "") or "").strip())
    perda_fluorescente = bool((documento.imagens.get("fluorescente", "") or "").strip())

    vapor_types = _extract_vapor_types_from_info(documento.info_adicional)
    if perda_vapor and not vapor_types:
        vapor_types = ["sodio"]

    faturamento_mes = parse_monetario_br(documento.valor_faturamento)
    fatur_10_anos = faturamento_mes * Decimal("120")
    fatur_10_anos_dobro = fatur_10_anos * Decimal("2")

    mapa_substituicao = {
        "<<DATA_QIP>>": documento.periodo_qip,
        "<<TIPOS DE LÂMPADAS>>": _build_lamp_types_text(vapor_types, perda_fluorescente) or "luminarias",
        "<<TIPOS DE VAPOR>>": _build_vapor_types_text(vapor_types, include_preposition=False) or "vapor",
        "<<PARAGRAFO_NORMAS_VAPOR>>": _build_vapor_norms_text(vapor_types),
        "<<FATURAMENTO_MÊS>>": _fmt_br(faturamento_mes),
        "<<FATURAMENTO_10ANOS>>": _fmt_br(fatur_10_anos),
        "<<FATURAMENTO_10ANOS_DOBRO>>": _fmt_br(fatur_10_anos_dobro),
    }

    for placeholder, value in mapa_substituicao.items():
        conteudo_tex = conteudo_tex.replace(placeholder, value)

    conteudo_tex = conteudo_tex.replace(
        "\\perdaVaporfalse",
        "\\perdaVaportrue" if perda_vapor else "\\perdaVaporfalse",
    )
    conteudo_tex = conteudo_tex.replace(
        "\\perdaFluorescentefalse",
        "\\perdaFluorescentetrue" if perda_fluorescente else "\\perdaFluorescentefalse",
    )

    tabela_vapor = ""
    if perda_vapor:
        tabela_vapor = _build_figure_block(documento.imagens.get("vapor", ""))

    tabela_fluorescente = ""
    if perda_fluorescente:
        tabela_fluorescente = _build_figure_block(documento.imagens.get("fluorescente", ""))

    conteudo_tex = conteudo_tex.replace("<<TABELA VAPOR>>", tabela_vapor)
    conteudo_tex = conteudo_tex.replace("<<TABELA FLUORESCENTE>>", tabela_fluorescente)
    if "<<TABELA>>" in conteudo_tex:
        conteudo_tex = conteudo_tex.replace("<<TABELA>>", tabela_vapor or tabela_fluorescente)

    return _atualizar_contador_meses(conteudo_tex)


def _process_perda_transformacao_content(conteudo_tex: str, documento: Documento) -> str:
    placeholders = {
        "<<IDENTIFICAÇÃO>>": "identificacao",
        "<<COMPROVAÇÃO>>": "comprovacao",
        "<<CONSUMO>>": "consumo",
        "<<FATURAMENTO>>": "faturamento",
    }
    for placeholder, key in placeholders.items():
        conteudo_tex = conteudo_tex.replace(placeholder, _build_figure_block(documento.imagens.get(key, "")))
    return _atualizar_contador_meses(conteudo_tex)


def _formatar_moeda(entrada: str) -> str:
    numero = parse_monetario_br(entrada)
    inteiro, decimal = f"{numero:.2f}".split(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")
    return f"R$ {inteiro},{decimal}"


def _process_ofi_complementar_dobro_content(conteudo_tex: str, documento: Documento) -> str:
    if not documento.valor_faturamento.strip():
        raise ValueError("valor_faturamento deve ser informado para o subtipo Complementar do dobro.")
    conteudo_tex = conteudo_tex.replace("<<VALOR_PAGO>>", _formatar_moeda(documento.valor_faturamento))
    return _atualizar_contador_meses(conteudo_tex)


_OFI_LEVANTAMENTO_CADASTRAL_CHECKLIST = [
    "ItemPenultimoBaseGeorreferenciada",
    "ItemPenultimoTOI",
    "ItemPenultimoMemorialCalculo",
    "ItemPenultimoDatasCenso",
    "ItemPenultimoCartaComunicacao",
    "ItemPenultimoCobrancaDevolucao",
    "ItemPenultimoComprovantes",
    "ItemUltimoBaseGeorreferenciada",
    "ItemUltimoTOI",
    "ItemUltimoMemorialCalculo",
    "ItemUltimoDatasCenso",
    "ItemUltimoCartaComunicacao",
    "ItemUltimoCobrancaDevolucao",
    "ItemUltimoComprovantes",
    "ItemTOIsVinculados",
]


def _set_latex_boolean(content: str, flag_name: str, enabled: bool) -> str:
    replacement = f"\\{flag_name}{'true' if enabled else 'false'}"
    pattern = rf"\\{re.escape(flag_name)}(?:true|false)"
    return re.sub(pattern, lambda _: replacement, content)


def _apply_ofi_levantamento_cadastral_checklist(conteudo_tex: str, documento: Documento) -> str:
    defaults = {
        "ItemUltimoBaseGeorreferenciada": True,
        "ItemTOIsVinculados": True,
    }
    for flag_name in _OFI_LEVANTAMENTO_CADASTRAL_CHECKLIST:
        enabled = documento.ofi_item_flags.get(flag_name, defaults.get(flag_name, False))
        conteudo_tex = _set_latex_boolean(conteudo_tex, flag_name, bool(enabled))
    return conteudo_tex


def _process_req_esclarecimento_pagamento_content(conteudo_tex: str, documento: Documento) -> str:
    numero_comprovante = documento.numero_comprovante.strip()
    valor_pago = documento.valor_pago.strip()
    data_pagamento = documento.data_pagamento.strip()

    if not numero_comprovante:
        raise ValueError("numero_comprovante deve ser informado para o subtipo Esclarecimento Pagamento.")
    if not valor_pago:
        raise ValueError("valor_pago deve ser informado para o subtipo Esclarecimento Pagamento.")
    if not data_pagamento:
        raise ValueError("data_pagamento deve ser informada para o subtipo Esclarecimento Pagamento.")

    valor_pago_fmt = _formatar_moeda(valor_pago)

    mapa_substituicao = {
        "<<NUMEROCOMPROVANTE>>": numero_comprovante,
        "<<VALORPAGO>>": valor_pago_fmt.replace("R$ ", ""),
        "<<DATAPAGAMENTO>>": data_pagamento,
    }
    for placeholder, value in mapa_substituicao.items():
        conteudo_tex = conteudo_tex.replace(placeholder, value)

    return _atualizar_contador_meses(conteudo_tex)


def _process_ofi_pagamento_ajuste_content(conteudo_tex: str, documento: Documento) -> str:
    campos = {
        "[RECLAMACAO]": documento.ajuste_reclamacao,
        "[DATA RECLAMACAO]": documento.ajuste_data_reclamacao,
        "[DATA PRIMEIRO PAGAMENTO]": documento.ajuste_data_primeiro_pagamento,
        "[COMPROVANTE PRIMEIRO PAGAMENTO]": documento.ajuste_comprovante_primeiro_pagamento,
        "[DATA PAGAMENTO COMPLEMENTAR]": documento.ajuste_data_pagamento_complementar,
        "[COMPROVANTE PAGAMENTO COMPLEMENTAR]": documento.ajuste_comprovante_pagamento_complementar,
        "[DATA DISPONIBILIZACAO]": documento.ajuste_data_disponibilizacao,
        "[DATA EFETIVO PAGAMENTO COMPLEMENTAR]": documento.ajuste_data_efetivo_pagamento_complementar,
        "[PERIODO DECORRIDO]": documento.ajuste_periodo_decorrido,
        "[DATA PAGAMENTO]": documento.ajuste_data_pagamento,
        "[DATA TERMO INICIAL]": documento.ajuste_termo_inicial,
        "[DATA TERMO FINAL]": documento.ajuste_termo_final,
        "[NUMERO PROCESSO ANEEL]": documento.ajuste_numero_processo_aneel,
        "[EXPLICACAO DATA INICIAL]": documento.ajuste_explicacao_data_inicial,
        "[EXPLICACAO DATA FINAL]": documento.ajuste_explicacao_data_final,
        "[VALOR PRIMEIRO PAGAMENTO]": _formatar_moeda(documento.ajuste_valor_primeiro_pagamento).replace("R$ ", ""),
        "[VALOR PAGAMENTO COMPLEMENTAR]": _formatar_moeda(documento.ajuste_valor_pagamento_complementar).replace("R$ ", ""),
    }
    for placeholder, value in campos.items():
        if not str(value).strip():
            raise ValueError(f"{placeholder} deve ser informado para o subtipo Pagamento de Ajuste.")
        conteudo_tex = conteudo_tex.replace(placeholder, str(value))
    return _atualizar_contador_meses(conteudo_tex)


def _compile_tex_to_pdf(tex_path: Path) -> tuple[bool, Path | None, str]:
    engines = ["pdflatex", "xelatex"]
    available = [eng for eng in engines if shutil.which(eng)]
    has_makeindex = shutil.which("makeindex") is not None

    if not available:
        return False, None, "Nenhum compilador LaTeX encontrado no PATH (pdflatex/xelatex)."

    def _run_cmd(cmd: list[str]) -> tuple[bool, str]:
        proc = subprocess.run(
            cmd,
            cwd=tex_path.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=180,
            check=False,
        )
        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode == 0:
            return True, output

        tail = "\n".join(output.strip().splitlines()[-20:])
        return False, f"Comando {' '.join(cmd)} falhou.\n{tail}"

    last_error = ""
    for engine in available:
        base_cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]

        ok, msg = _run_cmd(base_cmd)
        if not ok:
            last_error = msg
            continue

        idx_path = tex_path.with_suffix(".idx")
        ran_makeindex = False
        if idx_path.exists() and idx_path.stat().st_size > 0:
            if has_makeindex:
                ok_idx, msg_idx = _run_cmd(["makeindex", idx_path.name])
                if not ok_idx:
                    last_error = msg_idx
                    continue
                ran_makeindex = True
            else:
                msg += "\nmakeindex nao encontrado; indice nao sera gerado."

        ok2, msg2 = _run_cmd(base_cmd)
        if not ok2:
            last_error = msg2
            continue

        ok3, msg3 = _run_cmd(base_cmd)
        if not ok3:
            last_error = msg3
            continue

        pdf_path = tex_path.with_suffix(".pdf")
        if pdf_path.exists():
            detail = "Compilado com 3 passagens"
            if ran_makeindex:
                detail += " + makeindex"
            detail += f" usando {engine}."
            return True, pdf_path, detail

        last_error = f"{engine} concluiu as passagens sem erro, mas o PDF nao foi encontrado."

    return False, None, last_error or "Falha desconhecida durante compilacao do PDF."


class GeradorOperacional:
    def __init__(self, config: AppConfig = CONFIG) -> None:
        self._config = config
        self._municipio_map = self._build_municipio_map()
        self._subtipo_map = self._build_subtipo_map()

    def _build_municipio_map(self) -> dict[str, tuple[Path, dict[str, str], str]]:
        result: dict[str, tuple[Path, dict[str, str], str]] = {}
        for arquivo in sorted(self._config.municipios_dir.glob("Dados_*.tex")):
            dados = parse_municipio_file(arquivo)
            nome = dados.get("nomeMunicipio") or arquivo.stem.replace("Dados_", "").replace("_", " ")
            key = _normalize_key(nome)
            result[key] = (arquivo, dados, nome)
        return result

    def _build_subtipo_map(self) -> dict[str, Path]:
        resultado: dict[str, Path] = {}

        for f in sorted(self._config.rec_dir.glob("*.tex")):
            if f.is_file():
                resultado[f"REC::{_normalize_key(_label(f.stem))}"] = f
                resultado[f"REC::{_normalize_key(f.stem)}"] = f

        for f in sorted(self._config.ofi_dir.glob("*.tex")):
            if f.is_file():
                resultado[f"OFI::{_normalize_key(_label(f.stem))}"] = f
                resultado[f"OFI::{_normalize_key(f.stem)}"] = f

        for f in sorted(self._config.req_dir.glob("*.tex")):
            if f.is_file():
                resultado[f"REQ::{_normalize_key(_label(f.stem))}"] = f
                resultado[f"REQ::{_normalize_key(f.stem)}"] = f

        for empresa_dir in sorted(self._config.req_dir.iterdir()):
            if not empresa_dir.is_dir():
                continue
            empresa = empresa_dir.name.upper()
            for f in sorted(empresa_dir.glob("*.tex")):
                if f.is_file():
                    resultado[f"REQ::{_normalize_key(f'[{empresa}] {_label(f.stem)}')}"] = f
                    resultado[f"REQ::{_normalize_key(f.stem)}::{empresa}"] = f

        return resultado

    def _resolver_municipio(self, nome_municipio: str) -> tuple[Path, dict[str, str], str]:
        key = _normalize_key(nome_municipio)
        if key not in self._municipio_map:
            raise FileNotFoundError(f"Municipio nao encontrado: {nome_municipio}")
        return self._municipio_map[key]

    def _resolver_subtipo(self, documento: Documento) -> Path:
        tipo = documento.tipo.strip().upper()
        subtipo = documento.subtipo.strip()
        empresa = documento.empresa.strip().upper()

        keys = [
            f"{tipo}::{_normalize_key(subtipo)}",
            f"{tipo}::{_normalize_key(subtipo)}::{empresa}",
            f"{tipo}::{_normalize_key(_label(subtipo))}",
        ]

        for key in keys:
            path = self._subtipo_map.get(key)
            if path:
                return path

        raise FileNotFoundError(f"Subtipo nao encontrado para {tipo}: {subtipo}")

    def processar_lote(self, documentos_validos: list[Documento]) -> list[ResultadoGeracao]:
        resultados: list[ResultadoGeracao] = []
        for documento in documentos_validos:
            resultados.append(self.processar_documento(documento))
        return resultados

    def processar_documento(self, documento: Documento) -> ResultadoGeracao:
        try:
            tex_path, pdf_path, mensagem = self._gerar_documento(documento)
            return ResultadoGeracao(
                documento_id=documento.doc_id,
                sucesso=True,
                mensagem=mensagem,
                tex_path=str(tex_path),
                pdf_path=str(pdf_path) if pdf_path else "",
            )
        except Exception as exc:
            return ResultadoGeracao(
                documento_id=documento.doc_id,
                sucesso=False,
                mensagem=str(exc),
            )

    def _gerar_documento(self, documento: Documento) -> tuple[Path, Path | None, str]:
        municipio_path, municipio_dados, municipio_nome = self._resolver_municipio(documento.municipio)
        subtype_path = self._resolver_subtipo(documento)

        empresa = documento.empresa.strip().upper() or municipio_dados.get("empresaResponsavel", "").strip().upper()
        if not empresa:
            raise ValueError("Empresa nao informada e nao encontrada no municipio.")

        empresa_dir = self._config.empresas_dir / empresa
        if not empresa_dir.is_dir():
            raise FileNotFoundError(f"Pasta da empresa nao encontrada: {empresa_dir}")

        usa_ip_estimada = _subtype_uses_ip_estimada(subtype_path)
        if usa_ip_estimada and not documento.uc.strip():
            uc_auto = _get_ip_estimada_from_municipio(municipio_dados)
            if not uc_auto:
                raise ValueError("Subtipo exige IP estimada, mas o municipio nao possui macro IPestimada.")
            documento.uc = uc_auto

        out_name = _build_output_name(documento, municipio_nome, subtype_path.stem)
        out_dir = self._config.saida_dir / out_name
        out_dir.mkdir(parents=True, exist_ok=True)

        if _is_fragment(subtype_path):
            tex_file = self._generate_assembled_doc(
                documento,
                municipio_nome,
                municipio_path,
                municipio_dados,
                subtype_path,
                empresa,
                empresa_dir,
                out_dir,
            )
        else:
            tex_file = self._handle_standalone_doc(documento, subtype_path, out_dir, out_name)

        ok, pdf_path, compile_msg = _compile_tex_to_pdf(tex_file)
        if not ok:
            raise RuntimeError(f"Documento montado, mas falhou ao compilar PDF: {compile_msg}")

        return tex_file, pdf_path, compile_msg

    def _process_subtype_content(self, documento: Documento, subtype_path: Path) -> str:
        content = subtype_path.read_text(encoding="utf-8")
        subtype_key = _tokenize_name(subtype_path.stem)

        if subtype_key == "PERDA_NOS_REATORES":
            content = _process_perda_reatores_content(content, documento)
        elif subtype_key == "PERDA_POR_TRANSFORMACAO":
            content = _process_perda_transformacao_content(content, documento)
        elif documento.tipo == "OFI" and subtype_key == "COMPLEMENTAR_DO_DOBRO":
            content = _process_ofi_complementar_dobro_content(content, documento)
        elif documento.tipo == "OFI" and subtype_key == "CONTESTACAO_LEVANTAMENTO_CADASTRAL_IP":
            content = _apply_ofi_levantamento_cadastral_checklist(content, documento)
        elif documento.tipo == "OFI" and subtype_key == "PAGAMENTO_DE_AJUSTE":
            content = _process_ofi_pagamento_ajuste_content(content, documento)
        elif documento.tipo == "REQ" and subtype_key == "ESCLARECIMENTO_PAGAMENTO":
            content = _process_req_esclarecimento_pagamento_content(content, documento)

        return _atualizar_contador_meses(content)

    def _generate_assembled_doc(
        self,
        documento: Documento,
        municipio_nome: str,
        municipio_path: Path,
        municipio_dados: dict[str, str],
        subtype_path: Path,
        empresa: str,
        empresa_dir: Path,
        out_dir: Path,
    ) -> Path:
        empresa_docs = _get_empresa_docs_from_subtype(subtype_path)

        include_intro = "intro" in empresa_docs
        include_legitimidade = "legitimidade" in empresa_docs
        include_anexos = "anexos" in empresa_docs
        include_final = "final" in empresa_docs

        intro_path = empresa_dir / "intro.tex"
        if include_intro:
            if not intro_path.exists():
                intro_path = empresa_dir / f"intro_{documento.tipo}.tex"

            if not intro_path.exists():
                raise FileNotFoundError(f"Arquivo de introducao nao encontrado: {intro_path}")

        processed_content = self._process_subtype_content(documento, subtype_path)
        processed_subtype_file = out_dir / f"{subtype_path.stem}_processed.tex"
        processed_subtype_file.write_text(processed_content, encoding="utf-8")

        titulo = _get_titulo_from_subtype(subtype_path)
        today = date.today().strftime("%d/%m/%Y")

        lines = [
            f"% === DOCUMENTO AUTO-GERADO — {today} ===",
            f"% Municipio : {municipio_nome}",
            f"% Empresa   : {empresa}",
            f"% Tipo      : {documento.tipo}",
            f"% Subtipo   : {subtype_path.stem}",
            "",
            "% ── PREAMBULO DA EMPRESA ──────────────────────────────────────────",
            f"\\input{{{_lpath(empresa_dir / 'preambulo.tex')}}}",
            "\\usepackage{float}",
            "\\usepackage{enumitem}",
            f"\\graphicspath{{{{{_lpath(empresa_dir)}/}}}}",
            "",
            "% ── DADOS DO MUNICIPIO ────────────────────────────────────────────",
            f"\\input{{{_lpath(municipio_path)}}}",
            "",
            "% ── DADOS DO DOCUMENTO ────────────────────────────────────────────",
            f"\\newcommand{{\\tipoDocumento}}{{{documento.tipo}}}",
            f"\\newcommand{{\\isREC}}{{{'1' if documento.tipo == 'REC' else '0'}}}",
            f"\\newcommand{{\\isOFI}}{{{'1' if documento.tipo == 'OFI' else '0'}}}",
            f"\\newcommand{{\\hasUC}}{{{'1' if documento.uc.strip() else '0'}}}",
            f"\\newcommand{{\\numReclamacao}}{{{documento.numero}}}",
            f"\\newcommand{{\\unidadeConsumidora}}{{{documento.uc}}}",
            f"\\newcommand{{\\tituloDocumento}}{{{titulo}}}",
            "",
            "\\begin{document}",
        ]

        if include_intro:
            lines.extend(
                [
                    "",
                    "% ── INTRO ─────────────────────────────────────────────────────────",
                    f"\\input{{{_lpath(intro_path)}}}",
                    "",
                ]
            )

        if include_legitimidade:
            lines.extend(
                [
                    "% ── LEGITIMIDADE ──────────────────────────────────────────────────",
                    f"\\input{{{_lpath(empresa_dir / 'legitimidade.tex')}}}",
                    "",
                ]
            )

        if include_anexos:
            lines.extend(
                [
                    "% ── ANEXOS ────────────────────────────────────────────────────────",
                    f"\\input{{{_lpath(empresa_dir / 'anexos.tex')}}}",
                    "",
                ]
            )

        lines.extend(
            [
                f"% ── SUBTIPO ({documento.tipo}: {subtype_path.stem}) ─────────────────────",
                f"\\input{{{_lpath(processed_subtype_file)}}}",
                "",
            ]
        )

        if include_final:
            lines.extend(
                [
                    "% ── FINAL ─────────────────────────────────────────────────────────",
                    f"\\input{{{_lpath(empresa_dir / 'final.tex')}}}",
                    "",
                ]
            )

        lines.append("\\end{document}")

        out_name = _build_output_name(documento, municipio_nome, subtype_path.stem)
        out_file = out_dir / f"{out_name}.tex"
        out_file.write_text("\n".join(lines), encoding="utf-8")
        return out_file

    def _handle_standalone_doc(self, documento: Documento, subtype_path: Path, out_dir: Path, out_name: str) -> Path:
        content = self._process_subtype_content(documento, subtype_path)
        out_file = out_dir / f"{out_name}.tex"
        out_file.write_text(content, encoding="utf-8")
        return out_file
