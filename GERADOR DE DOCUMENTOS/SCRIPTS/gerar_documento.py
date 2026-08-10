#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Documentos — Inovve Automação
=========================================
Gera documentos LaTeX (REC ou REQ) para municípios parceiros,
montando automaticamente os componentes a partir da pasta
Gerador_de_Documentos.

Uso:
    python gerar_documento.py
"""

import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path
from decimal import Decimal, InvalidOperation

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
except ImportError:
    print("Erro: biblioteca 'rich' não encontrada.")
    print("Instale com:  pip install rich")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Caminhos base
# ---------------------------------------------------------------------------
SCRIPTS_DIR  = Path(__file__).resolve().parent
BASE_DIR     = SCRIPTS_DIR.parent          # Gerador_de_Documentos/
MUNICIPIOS_DIR = BASE_DIR / "MUNICIPIOS"
EMPRESAS_DIR   = BASE_DIR / "EMPRESAS"
OFI_DIR        = BASE_DIR / "OFI"
REC_DIR        = BASE_DIR / "REC"
REQ_DIR        = BASE_DIR / "REQ"
SAIDA_DIR      = BASE_DIR / "SAÍDA"

console = Console()

# ---------------------------------------------------------------------------
# Leitura de dados LaTeX
# ---------------------------------------------------------------------------
_CMD_RE = re.compile(
    r'\\(?:new|provide|renew)command\s*\{\\(\w+)\}\s*\{([^}]*)\}'
)
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


def parse_latex_commands(content: str) -> dict:
    """Extrai \\[new|provide|renew]command{\\key}{value} como dicionário."""
    return {m.group(1): m.group(2).strip() for m in _CMD_RE.finditer(content)}


def parse_municipio_file(path: Path) -> dict:
    try:
        return parse_latex_commands(path.read_text(encoding="utf-8"))
    except Exception as exc:
        console.print(f"[yellow]Aviso: não foi possível ler {path.name}: {exc}[/yellow]")
        return {}


def get_titulo_from_subtype(path: Path) -> str:
    """Lê o título principal do subtipo (fallback entre macros conhecidas)."""
    try:
        data = parse_latex_commands(path.read_text(encoding="utf-8"))
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
    except Exception as exc:
        console.print(f"[yellow]Aviso: não foi possível ler {path.name}: {exc}[/yellow]")
        return ""


def get_tese_from_subtype(path: Path) -> str:
    """Lê o conteúdo de \\tese definido no subtipo, quando existir."""
    try:
        data = parse_latex_commands(path.read_text(encoding="utf-8"))
        return data.get("tese", "").strip()
    except Exception as exc:
        console.print(f"[yellow]Aviso: não foi possível ler {path.name}: {exc}[/yellow]")
        return ""


def get_empresa_docs_from_subtype(path: Path) -> set[str]:
    """
    Lê configuração opcional da tese via macro LaTeX:
      \newcommand{\empresaDocumentos}{intro,legitimidade,anexos,final}

    Regras:
    - Se ausente/inválida: inclui todos os tipos.
    - Aceita exclusão por prefixo '-' ou '!': ex. "-anexos,-legitimidade".
    - Aceita sinônimos simples (introducao, anexo/anexos).
    """
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        console.print(f"[yellow]Aviso: não foi possível ler {path.name}: {exc}[/yellow]")
        return set(_EMPRESA_DOC_KEYS)

    data = parse_latex_commands(content)
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


def _is_truthy_flag(value: str) -> bool:
    """Interpreta valores textuais simples como flag booleana."""
    return value.strip().lower() in {"1", "true", "sim", "s", "yes", "y"}


def subtype_uses_ip_estimada(path: Path) -> bool:
    """Indica se a tese deve usar automaticamente a UC de IP estimada do município."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        console.print(f"[yellow]Aviso: não foi possível ler {path.name}: {exc}[/yellow]")
        return False

    data = parse_latex_commands(content)
    if _is_truthy_flag(data.get("usaIPEstimada", "")):
        return True

    # Compatibilidade com a anotação textual já usada em algumas teses.
    return _IP_ESTIMADA_COMMENT_RE.search(content) is not None


def get_ip_estimada_from_municipio(mun_dados: dict) -> str:
    """Lê a UC de IP estimada do município (novo nome + fallback legado)."""
    return (
        mun_dados.get("IPestimada", "").strip()
        or mun_dados.get("IP_estimada", "").strip()
    )


def list_municipios() -> list:
    """Retorna lista de (nome_display, path, dados_dict)."""
    result = []
    for f in sorted(MUNICIPIOS_DIR.glob("Dados_*.tex")):
        dados = parse_municipio_file(f)
        nome  = dados.get("nomeMunicipio") or f.stem.replace("Dados_", "").replace("_", " ")
        result.append((nome, f, dados))
    return result


# ---------------------------------------------------------------------------
# Listagem de subtipos
# ---------------------------------------------------------------------------
def _label(stem: str) -> str:
    """Converte nome de arquivo em rótulo legível."""
    return stem.replace("_", " ").replace("-", " ")


def is_fragment(path: Path) -> bool:
    """
    True  → fragmento (seção) — pode ser \\input{} dentro de um documento.
    False → documento autônomo (possui \\documentclass ou \\begin{document}).
    """
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        return (r"\documentclass"   not in content and
                r"\begin{document}" not in content)
    except Exception:
        return False


def _fmt_br(valor: float) -> str:
    """Auxiliary function to format numbers in PT-BR standard (1.234,56)."""
    return f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def _ask_yes_no(prompt: str) -> bool:
    """Solicita uma resposta sim/não e retorna True para sim."""
    while True:
        resposta = Prompt.ask(f"  {prompt} [dim](s/n)[/dim]", default="n").strip().lower()
        if resposta in {"s", "sim"}:
            return True
        if resposta in {"n", "nao", "não"}:
            return False
        console.print("[red]  Resposta inválida. Digite 's' ou 'n'.[/red]")


def _ask_image_path(prompt: str) -> str:
    """Solicita um caminho de imagem existente e devolve em formato LaTeX-friendly."""
    while True:
        raw_path = Prompt.ask(f"  {prompt}").strip().strip('"')
        image_path = Path(raw_path)
        if image_path.is_file():
            return str(image_path.resolve()).replace('\\', '/')
        console.print("[red]  Arquivo não encontrado. Informe um caminho de imagem válido.[/red]")


MESES_CONTADOR_BASE = 115
MESES_CONTADOR_DATA_BASE = date(2026, 7, 1)
MESES_CONTADOR_MAXIMO = 120
MESES_CONTADOR_PLACEHOLDER = "<<CONTADOR_MESES>>"


def _meses_contador_atual(referencia: date | None = None) -> int:
    """Calcula o contador automático de meses com teto em 120."""
    referencia = referencia or date.today()
    meses_passados = (
        (referencia.year - MESES_CONTADOR_DATA_BASE.year) * 12
        + (referencia.month - MESES_CONTADOR_DATA_BASE.month)
    )
    meses_atual = MESES_CONTADOR_BASE + max(0, meses_passados)
    return min(MESES_CONTADOR_MAXIMO, meses_atual)


def _atualizar_contador_meses(conteudo: str) -> str:
    """Substitui o contador textual de meses pelo valor automático atual."""
    return conteudo.replace(MESES_CONTADOR_PLACEHOLDER, str(_meses_contador_atual()))


VAPOR_LAMP_TYPES = (
    ("sodio", "vapor de sódio"),
    ("mercurio", "vapor de mercúrio"),
    ("metalica", "vapor metálico"),
)


def _join_pt_br(items: list[str]) -> str:
    """Une itens com vírgula e 'e', em formato legível."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} e {items[1]}"
    return f"{', '.join(items[:-1])} e {items[-1]}"


def _ask_vapor_lamp_types() -> list[str]:
    """Solicita os tipos de lâmpadas de vapor com perdas."""
    while True:
        selecionados = []
        for chave, rotulo in VAPOR_LAMP_TYPES:
            if _ask_yes_no(f"Houve perdas em lâmpadas de {rotulo}?"):
                selecionados.append(chave)
        if selecionados:
            return selecionados
        console.print("[red]  Se houve perdas para lâmpadas de vapor, selecione ao menos um tipo.[/red]")


def _build_vapor_types_text(selected_vapor_types: list[str], include_preposition: bool = True) -> str:
    """Monta o texto com os tipos de lâmpadas de vapor selecionados."""
    selected_set = set(selected_vapor_types)
    itens = []
    for chave, rotulo in VAPOR_LAMP_TYPES:
        if chave in selected_set:
            itens.append(f"de {rotulo}" if include_preposition else rotulo)
    return _join_pt_br(itens)


def _build_lamp_types_text(selected_vapor_types: list[str], include_fluorescente: bool) -> str:
    """Monta o texto dos tipos de lâmpadas selecionados."""
    tipos = []
    if selected_vapor_types:
        tipos.append(_build_vapor_types_text(selected_vapor_types, include_preposition=True))
    if include_fluorescente:
        tipos.append("fluorescentes")
    return _join_pt_br(tipos)


def _build_vapor_norms_text(selected_vapor_types: list[str]) -> str:
    """Monta o parágrafo regulatório para os tipos de vapor selecionados."""
    selected_set = set(selected_vapor_types)
    if selected_set == {"sodio"}:
        return (
            "Para os reatores de lâmpadas de vapor de sódio, os limites máximos "
            "admissíveis de perdas encontram-se expressamente definidos na NBR "
            "13593:2011, a qual possui caráter vinculante e de observância "
            "obrigatória pela Concessionária."
        )
    if selected_set == {"metalica"}:
        return (
            "Para os reatores de lâmpadas de vapor metálico, os limites máximos "
            "admissíveis de perdas encontram-se expressamente definidos na NBR "
            "14305:2015, a qual possui caráter vinculante e de observância "
            "obrigatória pela Concessionária."
        )
    if selected_set == {"sodio", "metalica"}:
        return (
            "Para os reatores de lâmpadas de vapor de sódio e de vapor metálico, "
            "os limites máximos admissíveis de perdas encontram-se expressamente "
            "definidos nas normas da ABNT, em especial a NBR 13593:2011 e a NBR "
            "14305:2015, respectivamente, as quais possuem caráter vinculante e de "
            "observância obrigatória pela Concessionária."
        )
    return (
        "Para os reatores de lâmpadas "
        f"{_build_vapor_types_text(selected_vapor_types, include_preposition=True)}, "
        "os limites máximos admissíveis de perdas devem observar as normas "
        "técnicas aplicáveis da ABNT, as quais possuem caráter vinculante e de "
        "observância obrigatória pela Concessionária."
    )


def _build_reator_figure_block(caminho_img: str) -> str:
    return (
        f"\\begin{{figure}}[H]\n"
        f"    \\centering\n"
        f"    \\includegraphics[width=\\textwidth]{{{caminho_img}}}\n"
        f"\\end{{figure}}"
    )


def _process_perda_reatores_content(conteudo_tex: str) -> str:
    """
    Solicita dados ao usuário e realiza as substituições para o
    template de Perda nos Reatores.
    """
    console.print("\n[bold blue]CONFIGURAÇÃO: PERDA NOS REATORES[/bold blue]")

    # 1. Coleta de dados
    data_qip = Prompt.ask("  Informe a data do QIP (ex: Janeiro de 2024)")

    while True:
        perda_vapor = _ask_yes_no("Houve perdas para lâmpadas de vapor?")
        vapor_types = _ask_vapor_lamp_types() if perda_vapor else []
        perda_fluorescente = _ask_yes_no("Houve perdas para lâmpadas fluorescentes?")
        if vapor_types or perda_fluorescente:
            break
        console.print("[red]  É necessário selecionar pelo menos um tipo de perda.[/red]")

    imagens = {}
    if perda_vapor:
        imagens["vapor"] = _ask_image_path(
            "Informe o endereço da imagem da tabela de vapor (ex: C:/caminho/para/imagem.png)"
        )
    if perda_fluorescente:
        imagens["fluorescente"] = _ask_image_path(
            "Informe o endereço da imagem da tabela de fluorescentes (ex: C:/caminho/para/imagem.png)"
        )

    while True:
        faturamento_mes_str = Prompt.ask("  Informe o valor do faturamento de um mês (kWh) [dim](use '.' como separador decimal)[/dim]")
        try:
            faturamento_mes = float(faturamento_mes_str.replace(',', '.'))
            break
        except ValueError:
            console.print("[red]  Erro: Valor inválido. Por favor, insira um número válido.[/red]")

    # 2. Cálculos (10 anos = 120 meses)
    fatur_10_anos = faturamento_mes * 120
    fatur_10_anos_dobro = fatur_10_anos * 2

    # 3. Dicionário de Substituições
    mapa_substituicao = {
        "<<DATA_QIP>>": data_qip,
        "<<TIPOS DE LÂMPADAS>>": _build_lamp_types_text(vapor_types, perda_fluorescente),
        "<<TIPOS DE VAPOR>>": _build_vapor_types_text(vapor_types, include_preposition=False),
        "<<PARAGRAFO_NORMAS_VAPOR>>": _build_vapor_norms_text(vapor_types),
        "<<FATURAMENTO_MÊS>>": _fmt_br(faturamento_mes),
        "<<FATURAMENTO_10ANOS>>": _fmt_br(fatur_10_anos),
        "<<FATURAMENTO_10ANOS_DOBRO>>": _fmt_br(fatur_10_anos_dobro)
    }

    # 4. Substituição dos placeholders de texto
    for placeholder, valor in mapa_substituicao.items():
        conteudo_tex = conteudo_tex.replace(placeholder, valor)

    conteudo_tex = _atualizar_contador_meses(conteudo_tex)

    conteudo_tex = conteudo_tex.replace(
        "\\perdaVaporfalse",
        "\\perdaVaportrue" if perda_vapor else "\\perdaVaporfalse",
    )
    conteudo_tex = conteudo_tex.replace(
        "\\perdaFluorescentefalse",
        "\\perdaFluorescentetrue" if perda_fluorescente else "\\perdaFluorescentefalse",
    )

    caption_index = 1
    tabela_vapor = ""
    if perda_vapor:
        tabela_vapor = _build_reator_figure_block(
            imagens["vapor"]            
        )
        caption_index += 1

    tabela_fluorescente = ""
    if perda_fluorescente:
        tabela_fluorescente = _build_reator_figure_block(
            imagens["fluorescente"]
        )

    conteudo_tex = conteudo_tex.replace("<<TABELA VAPOR>>", tabela_vapor)
    conteudo_tex = conteudo_tex.replace("<<TABELA FLUORESCENTE>>", tabela_fluorescente)

    # Compatibilidade com versões antigas do template.
    if "<<TABELA>>" in conteudo_tex:
        tabela_legada = tabela_vapor or tabela_fluorescente
        conteudo_tex = conteudo_tex.replace("<<TABELA>>", tabela_legada)

    return conteudo_tex


def _process_perda_transformacao_content(conteudo_tex: str) -> str:
    """
    Solicita os caminhos das imagens e realiza as substituições para o
    template de Perda por Transformação.
    """
    console.print("\n[bold blue]CONFIGURAÇÃO: PERDA POR TRANSFORMAÇÃO[/bold blue]")

    placeholders = [
        ("<<IDENTIFICAÇÃO>>", "Informe o endereço da imagem de identificação da UC"),
        ("<<COMPROVAÇÃO>>", "Informe o endereço da imagem de comprovação da perda de 2,5%"),
        ("<<CONSUMO>>", "Informe o endereço da imagem de consumo medido"),
        ("<<FATURAMENTO>>", "Informe o endereço da imagem de faturamento com acréscimo"),
    ]

    for placeholder, prompt in placeholders:
        caminho_img = _ask_image_path(f"{prompt} (ex: C:/caminho/para/imagem.png)")
        conteudo_tex = conteudo_tex.replace(placeholder, _build_reator_figure_block(caminho_img))

    return conteudo_tex

def _formatar_moeda(valor: str) -> str:
    """
    Converte diversas representações monetárias para o padrão:
        R$ 1.234,56

    Exemplos aceitos:
        1111
        1111,5
        1111.5
        1111,50
        1111.50
        1.111,50
        1,111.50
        R$1111
        R$ 1111
        $1111
    """

    if not valor or not valor.strip():
        raise ValueError("Valor vazio.")

    valor = valor.strip()

    # Remove qualquer símbolo monetário e espaços
    valor = re.sub(r"[^\d,.\-]", "", valor)

    if not valor:
        raise ValueError("Valor inválido.")

    # Descobre qual é o separador decimal
    if "," in valor and "." in valor:
        # O último separador encontrado é considerado decimal
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
    except InvalidOperation:
        raise ValueError("Valor inválido.")

    numero = numero.quantize(Decimal("0.01"))

    inteiro, decimal = f"{numero:.2f}".split(".")
    inteiro = f"{int(inteiro):,}".replace(",", ".")

    return f"R\$ {inteiro},{decimal}"

def _process_ofi_complementar_dobro_content(conteudo_tex: str) -> str:
    """
    Solicita o valor já pago e substitui o placeholder do
    template de Ofício Complementar do Dobro.
    """
    console.print("\n[bold blue]CONFIGURAÇÃO: OFÍCIO - COMPLEMENTAR DO DOBRO[/bold blue]")

    while True:
        entrada = Prompt.ask(
            "  Informe o valor já pago [dim](ex: R$ 12.345,67)[/dim]"
        ).strip()

        try:
            valor_pago = _formatar_moeda(entrada)
            break
        except ValueError:
            console.print(
                "[red]  Valor inválido. Tente novamente.[/red]"
            )

    conteudo_tex = conteudo_tex.replace("<<VALOR_PAGO>>", valor_pago)
    return _atualizar_contador_meses(conteudo_tex)


def _process_req_esclarecimento_pagamento_content(conteudo_tex: str) -> str:
    """
    Solicita dados do comprovante e substitui placeholders do
    template de REQ Esclarecimento de Pagamento.
    """
    console.print("\n[bold blue]CONFIGURAÇÃO: REQ - ESCLARECIMENTO DE PAGAMENTO[/bold blue]")

    numero_comprovante = Prompt.ask("  Informe o número do comprovante").strip()

    while True:
        entrada_valor = Prompt.ask(
            "  Informe o valor pago [dim](ex: R$ 12.345,67)[/dim]"
        ).strip()
        try:
            valor_pago_fmt = _formatar_moeda(entrada_valor)
            break
        except ValueError:
            console.print("[red]  Valor inválido. Tente novamente.[/red]")

    data_pagamento = Prompt.ask("  Informe a data do pagamento [dim](DD/MM/AAAA)[/dim]").strip()

    mapa_substituicao = {
        "<<NUMEROCOMPROVANTE>>": numero_comprovante,
        "<<VALORPAGO>>": valor_pago_fmt.replace("R\\$ ", ""),
        "<<DATAPAGAMENTO>>": data_pagamento,
    }
    for placeholder, valor in mapa_substituicao.items():
        conteudo_tex = conteudo_tex.replace(placeholder, valor)

    return _atualizar_contador_meses(conteudo_tex)


def list_subtypes_rec() -> list:
    """Fragmentos de subtipos para REC (arquivos .tex na raiz de REC/)."""
    return [
        (_label(f.stem), f)
        for f in sorted(REC_DIR.glob("*.tex"))
        if f.is_file()
    ]


def list_subtypes_req(empresa: str) -> list:
    """Fragmentos de subtipos para REQ: raiz + subpasta da empresa."""
    subtypes = []
    for f in sorted(REQ_DIR.glob("*.tex")):
        if f.is_file():
            subtypes.append((_label(f.stem), f))
    empresa_dir = REQ_DIR / empresa
    if empresa_dir.is_dir():
        for f in sorted(empresa_dir.glob("*.tex")):
            subtypes.append((f"[{empresa}] {_label(f.stem)}", f))
    return subtypes


def list_subtypes_req_all() -> list:
    """Subtipos REQ de uso geral e por empresa, para varredura multi-municípios."""
    subtypes = []
    for f in sorted(REQ_DIR.glob("*.tex")):
        if f.is_file():
            subtypes.append((_label(f.stem), f))

    for empresa_dir in sorted(REQ_DIR.iterdir()):
        if not empresa_dir.is_dir():
            continue
        empresa_nome = empresa_dir.name.upper()
        for f in sorted(empresa_dir.glob("*.tex")):
            if f.is_file():
                subtypes.append((f"[{empresa_nome}] {_label(f.stem)}", f))

    return subtypes

def list_subtypes_ofi() -> list:
    """Fragmentos de subtipos para OFI: arquivos .tex na raiz de OFI/."""
    return [
        (_label(f.stem), f)
        for f in sorted(OFI_DIR.glob("*.tex"))
        if f.is_file()
    ]


# ---------------------------------------------------------------------------
# Interface de seleção
# ---------------------------------------------------------------------------
def choose_from_list(title: str, items: list) -> int:
    """Exibe tabela numerada e retorna índice (0-based) da escolha do usuário."""
    table = Table(title=title, show_header=True, header_style="bold cyan",
                  show_lines=False)
    table.add_column("Nº", style="dim", width=4, justify="right")
    table.add_column("Opção")
    for i, item in enumerate(items, 1):
        table.add_row(str(i), str(item))
    console.print(table)
    total = len(items)
    while True:
        raw = Prompt.ask(f"  Escolha (1–{total})").strip()
        if raw.isdigit() and 1 <= int(raw) <= total:
            return int(raw) - 1
        console.print(f"[red]  Inválido. Digite um número de 1 a {total}.[/red]")


# ---------------------------------------------------------------------------
# Geração do documento
# ---------------------------------------------------------------------------
def _lpath(p: Path) -> str:
    """Caminho absoluto com barras /  — compatível com LaTeX no Windows."""
    return str(p.resolve()).replace("\\", "/")


def _tokenize_name(value: str) -> str:
    """Normaliza texto para token ASCII em CAIXA ALTA com underscores."""
    normalized = unicodedata.normalize("NFD", value)
    no_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    upper = no_accents.upper()
    underscored = re.sub(r"[^A-Z0-9]+", "_", upper)
    return re.sub(r"_+", "_", underscored).strip("_") or "SEM_NOME"


def build_output_name(
    doc_type: str,
    num_doc: str,
    municipio: str,
    subtype_stem: str,
    uc: str = "",
    origem_tipo: str = "",
    origem_cod: str = "",
    tese: str = "",
) -> str:
    """Monta nome de saída em ASCII e CAIXA ALTA."""
    if doc_type == "OFI":
        return "-".join([
            _tokenize_name(doc_type),
            _tokenize_name(num_doc),
            _tokenize_name(municipio),
            _tokenize_name(origem_tipo),
            _tokenize_name(origem_cod),
        ])

    parts = [
        _tokenize_name(doc_type),
        _tokenize_name(num_doc),
        _tokenize_name(municipio),
        _tokenize_name(subtype_stem),
    ]
    if uc.strip():
        parts.append(_tokenize_name(uc))
    return "-".join(parts)


def generate_assembled_doc(
    municipio_path: Path,
    empresa: str,
    doc_type: str,       # "REC" ou "REQ" ou "OFI"
    subtype_path: Path,
    num_doc: str,
    uc: str,
    titulo: str,
    origem_tipo: str = "",
    origem_cod: str = "",
    tese: str = "",
) -> Path:
    """
    Monta documento.tex em SAÍDA/{municipio}_{tipo}_{numero}/ com
    caminhos absolutos para todos os \\input{}.
    Retorna o caminho do arquivo gerado.
    """
    empresa_dir = EMPRESAS_DIR / empresa

    empresa_docs = get_empresa_docs_from_subtype(subtype_path)
    include_intro = "intro" in empresa_docs
    include_legitimidade = "legitimidade" in empresa_docs
    include_anexos = "anexos" in empresa_docs
    include_final = "final" in empresa_docs

    # Intro unificado por empresa (o próprio LaTeX escolhe REC/REQ)
    intro_path = empresa_dir / "intro.tex"
    if include_intro and not intro_path.exists():
        # Compatibilidade: empresas antigas podem manter o padrão intro_{tipo}.tex
        intro_variante = empresa_dir / f"intro_{doc_type}.tex"
        intro_path = intro_variante

    if include_intro and not intro_path.exists():
        raise FileNotFoundError(f"Arquivo de introdução não encontrado: {intro_path}")

    # Pasta de saída
    mun_dados = parse_municipio_file(municipio_path)
    mun_nome  = mun_dados.get("nomeMunicipio",
                              municipio_path.stem.replace("Dados_", ""))
    out_name = build_output_name(
        doc_type,
        num_doc,
        mun_nome,
        subtype_path.stem,
        uc,
        origem_tipo,
        origem_cod,
        tese,
    )
    out_dir  = SAIDA_DIR / out_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Read subtype content and apply specific processing if needed
    subtype_content = subtype_path.read_text(encoding="utf-8")
    subtype_key = _tokenize_name(subtype_path.stem)
    if subtype_key == "PERDA_NOS_REATORES":
        subtype_content = _process_perda_reatores_content(subtype_content)
    elif subtype_key == "PERDA_POR_TRANSFORMACAO":
        subtype_content = _process_perda_transformacao_content(subtype_content)
    elif doc_type == "OFI" and subtype_key == "COMPLEMENTAR_DO_DOBRO":
        subtype_content = _process_ofi_complementar_dobro_content(subtype_content)
    elif doc_type == "REQ" and subtype_key == "ESCLARECIMENTO_PAGAMENTO":
        subtype_content = _process_req_esclarecimento_pagamento_content(subtype_content)

    subtype_content = _atualizar_contador_meses(subtype_content)

    # Write the (potentially modified) subtype content to a temporary file
    # in the output directory. This ensures that the modifications are applied
    # before LaTeX processes it.
    processed_subtype_file = out_dir / f"{subtype_path.stem}_processed.tex"
    processed_subtype_file.write_text(subtype_content, encoding="utf-8")

    today = date.today().strftime("%d/%m/%Y")
    lines = [
        f"% === DOCUMENTO AUTO-GERADO — {today} ===",
        f"% Município : {mun_nome}",
        f"% Empresa   : {empresa}",
        f"% Tipo      : {doc_type}",
        f"% Subtipo   : {subtype_path.stem}",
        "",
        "% ── PREAMBULO DA EMPRESA ──────────────────────────────────────────",
        f"\\input{{{_lpath(empresa_dir / 'preambulo.tex')}}}",
        "\\usepackage{float} % Suporte para a opção [H] (posicionamento rígido)",
        "\\usepackage{enumitem} % Suporte para a opção [resume] das listas",
        "% Garante busca de imagens (headers/footers) na pasta da empresa",
        f"\\graphicspath{{{{{_lpath(empresa_dir)}/}}}}",
        "",
        "% ── DADOS DO MUNICÍPIO ────────────────────────────────────────────",
        f"\\input{{{_lpath(municipio_path)}}}",
        "",
        "% ── DADOS DO DOCUMENTO ────────────────────────────────────────────",
        f"\\newcommand{{\\tipoDocumento}}{{{doc_type}}}",
        f"\\newcommand{{\\isREC}}{{{'1' if doc_type == 'REC' else '0'}}}",
        f"\\newcommand{{\\isOFI}}{{{'1' if doc_type == 'OFI' else '0'}}}",
        f"\\newcommand{{\\hasUC}}{{{'1' if uc.strip() else '0'}}}",
        f"\\newcommand{{\\numReclamacao}}{{{num_doc}}}",
        f"\\newcommand{{\\unidadeConsumidora}}{{{uc}}}",
        f"\\newcommand{{\\tituloDocumento}}{{{titulo}}}",
        "",
        "\\begin{document}",
    ]

    if include_intro:
        lines.extend([
            "",
            "% ── INTRO ─────────────────────────────────────────────────────────",
            f"\\input{{{_lpath(intro_path)}}}",
            "",
        ])

    if include_legitimidade:
        lines.extend([
            "% ── LEGITIMIDADE ──────────────────────────────────────────────────",
            f"\\input{{{_lpath(empresa_dir / 'legitimidade.tex')}}}",
            "",
        ])

    if include_anexos:
        lines.extend([
            "% ── ANEXOS ────────────────────────────────────────────────────────",
            f"\\input{{{_lpath(empresa_dir / 'anexos.tex')}}}",
            "",
        ])

    lines.extend([
        f"% ── SUBTIPO ({doc_type}: {subtype_path.stem}) ─────────────────────",
        f"\\input{{{_lpath(processed_subtype_file)}}}", # Input the processed file
        "",
    ])

    if include_final:
        lines.extend([
            "% ── FINAL ─────────────────────────────────────────────────────────",
            f"\\input{{{_lpath(empresa_dir / 'final.tex')}}}",
            "",
        ])

    lines.append("\\end{document}")

    out_file = out_dir / f"{out_name}.tex"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    return out_file


def handle_standalone_doc(
    subtype_path: Path,
    doc_type: str,
    num_doc: str,
    municipio_nome: str,
    uc: str = "",
    origem_tipo: str = "",
    origem_cod: str = "",
    tese: str = "",
) -> Path:
    """
    Documentos autônomos (já possuem \\documentclass / \\begin{document})
    são copiados para SAÍDA/ sem modificação.
    """
    out_name = build_output_name(
        doc_type,
        num_doc,
        municipio_nome,
        subtype_path.stem,
        uc,
        origem_tipo,
        origem_cod,
        tese,
    )
    out_dir  = SAIDA_DIR / out_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{out_name}.tex"
    out_file.write_text(
        _atualizar_contador_meses(subtype_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    return out_file


def compile_tex_to_pdf(tex_path: Path) -> tuple[bool, Path | None, str]:
    """
    Compila um arquivo .tex para PDF na mesma pasta do arquivo,
    executando passagens extras para resolver referencias cruzadas.
    Se houver indice, roda makeindex entre as passagens.
    Retorna (sucesso, caminho_pdf_ou_none, mensagem).
    """
    engines = ["pdflatex", "xelatex"]
    available = [eng for eng in engines if shutil.which(eng)]
    has_makeindex = shutil.which("makeindex") is not None

    if not available:
        return (
            False,
            None,
            "Nenhum compilador LaTeX encontrado no PATH (pdflatex/xelatex).",
        )

    def _run_cmd(cmd: list[str]) -> tuple[bool, str]:
        try:
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
        except Exception as exc:
            return False, f"Falha ao executar {' '.join(cmd)}: {exc}"

        output = (proc.stdout or "") + "\n" + (proc.stderr or "")
        if proc.returncode == 0:
            return True, output

        tail = "\n".join(output.strip().splitlines()[-20:])
        return False, f"Comando {' '.join(cmd)} falhou.\n{tail}"

    last_error = ""
    for engine in available:
        base_cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]

        # 1a passada: gera .aux/.toc/.idx para referencias e indice.
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
                # Segue sem abortar: refs resolvem mesmo sem indice.
                msg += "\nmakeindex não encontrado; índice não será gerado."

        # 2a e 3a passadas: fixam \ref{}, TOC e referencias apos makeindex.
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

        last_error = f"{engine} concluiu as passagens sem erro, mas o PDF não foi encontrado."

    return False, None, last_error or "Falha desconhecida durante compilação do PDF."


def increment_code(code: str) -> str:
    """Incrementa a parte numérica de um código tipo '001/2026' ou '001'."""
    match = re.search(r'(\d+)', code)
    if not match:
        return code
    num_str = match.group(1)
    new_num = int(num_str) + 1
    # Mantém o padding de zeros (ex: 001 -> 002)
    new_num_str = str(new_num).zfill(len(num_str))
    return code[:match.start()] + new_num_str + code[match.end():]


def prompt_origem_cod(prompt_text: str) -> str:
    """Lê um código de origem no formato XXX_XXXX."""
    while True:
        origem_cod_input = Prompt.ask(prompt_text).strip().upper()
        if re.fullmatch(r"[A-Z0-9]{3}_[A-Z0-9]{4}", origem_cod_input):
            return origem_cod_input
        console.print("[red]  Código inválido. Use o formato XXX_XXXX.[/red]")


def _infer_empresa_from_municipio(nome_mun: str, mun_dados: dict) -> str:
    """Infere a empresa do município e solicita manualmente quando ausente."""
    empresa = mun_dados.get("empresaResponsavel", "").strip().upper()
    if empresa:
        return empresa
    console.print(
        f"[yellow]  Aviso: empresa não encontrada no arquivo do município ({nome_mun}).[/yellow]"
    )
    return Prompt.ask("  Informe a empresa (HLA ou RUDA)").strip().upper()


def _required_req_empresa(subtype_path: Path) -> str:
    """Retorna a empresa exigida por um subtipo REQ específico, quando aplicável."""
    if subtype_path.parent == REQ_DIR:
        return ""
    if subtype_path.parent.parent == REQ_DIR:
        return subtype_path.parent.name.upper()
    return ""


def _generate_for_case(
    nome_mun: str,
    mun_path: Path,
    empresa: str,
    doc_type: str,
    subtype_path: Path,
    n_doc: str,
    n_uc: str,
    titulo: str,
    origem_tipo: str,
    n_origem_cod: str,
    tese: str,
    standalone: bool,
) -> bool:
    """Gera e compila um documento para um caso específico."""
    extra_info = f" | Origem: {n_origem_cod}" if doc_type == "OFI" else ""
    console.print(
        f"\n  [bold]Processando: {nome_mun} | {n_doc} | UC: {n_uc or 'N/A'}{extra_info}[/bold]"
    )

    if standalone:
        out_file = handle_standalone_doc(
            subtype_path,
            doc_type,
            n_doc,
            nome_mun,
            n_uc,
            origem_tipo,
            n_origem_cod,
            tese,
        )
    else:
        out_file = generate_assembled_doc(
            mun_path,
            empresa,
            doc_type,
            subtype_path,
            n_doc,
            n_uc,
            titulo,
            origem_tipo,
            n_origem_cod,
            tese,
        )

    ok, pdf_path, compile_msg = compile_tex_to_pdf(out_file)

    if ok:
        console.print(Panel(
            f"[bold green]✓ Sucesso para {n_doc}![/bold green]\n\n"
            f"Arquivo .tex: [cyan]{out_file}[/cyan]\n"
            f"Arquivo PDF: [cyan]{pdf_path}[/cyan]\n\n"
            f"[dim]{compile_msg}[/dim]",
            title=f"Doc {n_doc}",
            border_style="green",
        ))
    else:
        if standalone:
            console.print(Panel(
                f"[yellow]⚠ O subtipo é autônomo. PDF não gerado automaticamente.[/yellow]\n\n"
                f"Arquivo .tex: [cyan]{out_file}[/cyan]\n\n"
                f"[dim]{compile_msg}[/dim]",
                title=f"Atenção {n_doc}",
                border_style="yellow",
            ))
        else:
            console.print(Panel(
                f"[red]✖ Falha na compilação do PDF.[/red]\n\n"
                f"Arquivo .tex: [cyan]{out_file}[/cyan]\n\n"
                f"[dim]{compile_msg}[/dim]",
                title=f"Erro {n_doc}",
                border_style="red",
            ))

    return ok


def _run_varredura_teses(municipios: list) -> bool:
    """Executa o modo Varredura de Teses para todos os municípios cadastrados."""
    console.print("\n[bold blue]MODO: VARREDURA DE TESES[/bold blue]")

    tipo_idx = choose_from_list(
        "Tipo de documento",
        [
            "REC  —  Reclamação",
            "REQ  —  Requerimento / Petição",
            "OFI  —  Ofício",
        ],
    )
    doc_type = ["REC", "REQ", "OFI"][tipo_idx]

    if doc_type == "REC":
        subtypes = list_subtypes_rec()
    elif doc_type == "REQ":
        subtypes = list_subtypes_req_all()
    else:
        subtypes = list_subtypes_ofi()

    if not subtypes:
        console.print(f"[red]  Nenhum subtipo encontrado para {doc_type}.[/red]")
        return False

    st_idx = choose_from_list(
        f"Subtipos disponíveis ({doc_type})",
        [label for label, _ in subtypes],
    )
    _, subtype_path = subtypes[st_idx]

    usa_ip_estimada = subtype_uses_ip_estimada(subtype_path)
    origem_tipo = ""
    tese = ""
    if doc_type == "OFI":
        origem_tipo_idx = choose_from_list(
            "Documento de origem do OFI",
            ["REC", "REQ"],
        )
        origem_tipo = ["REC", "REQ"][origem_tipo_idx]
        tese = get_tese_from_subtype(subtype_path) or subtype_path.stem

    titulo = get_titulo_from_subtype(subtype_path)
    if titulo:
        console.print(
            f"  Título/descrição [dim](lido do subtipo {subtype_path.name})[/dim]: {titulo}"
        )
    else:
        console.print(
            "  [yellow]Aviso:[/yellow] nenhuma macro de título conhecida foi encontrada no subtipo; "
            "seguindo com título vazio."
        )

    required_req_empresa = _required_req_empresa(subtype_path) if doc_type == "REQ" else ""
    standalone = not is_fragment(subtype_path)

    selecionados = 0
    gerados = 0
    total_docs = 0
    for nome_mun, mun_path, mun_dados in municipios:
        console.print(f"\n[bold]Município:[/bold] {nome_mun}")
        if not _ask_yes_no("Gerar esta tese para este município?"):
            continue

        selecionados += 1
        empresa = _infer_empresa_from_municipio(nome_mun, mun_dados)
        if not empresa or not (EMPRESAS_DIR / empresa).is_dir():
            console.print(f"[yellow]  Pulado: empresa inválida para {nome_mun} ({empresa or 'N/A'}).[/yellow]")
            continue

        if required_req_empresa and empresa != required_req_empresa:
            console.print(
                f"[yellow]  Pulado: este subtipo REQ exige empresa {required_req_empresa}, "
                f"mas o município usa {empresa}.[/yellow]"
            )
            continue

        num_doc = Prompt.ask("  Número do documento [dim](ex: 001/2026)[/dim]").strip()
        if usa_ip_estimada:
            uc = get_ip_estimada_from_municipio(mun_dados)
            if not uc:
                console.print(
                    "[yellow]  Pulado: tese marcada com IP estimada, mas o município não possui "
                    "\\IPestimada{} (nem \\IP_estimada{} legado).[/yellow]"
                )
                continue
            console.print(f"  [bold]UC automática (IP estimada):[/bold] {uc}")
        else:
            uc = Prompt.ask(
                "  Unidade consumidora [dim](deixe em branco se n/a)[/dim]",
                default="",
            ).strip()

        origem_cod = ""
        if doc_type == "OFI":
            origem_cod = prompt_origem_cod(
                "  Código do documento de origem [dim](formato: XXX_XXXX)[/dim]"
            )

        total_docs += 1
        ok = _generate_for_case(
            nome_mun,
            mun_path,
            empresa,
            doc_type,
            subtype_path,
            num_doc,
            uc,
            titulo,
            origem_tipo,
            origem_cod,
            tese,
            standalone,
        )
        if ok:
            gerados += 1

    console.print(
        f"\n[bold green]Varredura finalizada![/bold green] "
        f"Selecionados: {selecionados} | Processados: {total_docs} | Sucesso: {gerados}"
    )
    return True


# ---------------------------------------------------------------------------
# Fluxo principal
# ---------------------------------------------------------------------------
def _run_generation_cycle() -> bool:
    console.print(Panel(
        "[bold blue]GERADOR DE DOCUMENTOS[/bold blue]\n"
        "[dim]Inovve Automação — Montagem automática de LaTeX[/dim]",
        expand=False,
    ))

    # 1. Município ────────────────────────────────────────────────────────────
    municipios = list_municipios()
    if not municipios:
        console.print(f"[red]Nenhum arquivo encontrado em {MUNICIPIOS_DIR}[/red]")
        return False

    fluxo_idx = choose_from_list(
        "Modo de fluxo",
        [
            "Padrão  —  Município único",
            "Varredura de Teses  —  Mesma tese para vários municípios",
        ],
    )
    if fluxo_idx == 1:
        return _run_varredura_teses(municipios)

    idx = choose_from_list(
        "Municípios disponíveis",
        [f"{nome}  [dim]({f.name})[/dim]" for nome, f, _ in municipios],
    )
    nome_mun, mun_path, mun_dados = municipios[idx]
    console.print(f"\n  [bold]Município selecionado:[/bold] {nome_mun}")

    # 2. Empresa (inferida do arquivo do município) ───────────────────────────
    empresa = _infer_empresa_from_municipio(nome_mun, mun_dados)
    if empresa:
        console.print(f"  [bold]Empresa:[/bold] {empresa}  [dim](inferida do município)[/dim]")

    if not (EMPRESAS_DIR / empresa).is_dir():
        console.print(f"[red]  Erro: pasta EMPRESAS/{empresa} não encontrada![/red]")
        return False

    # 3. Tipo de documento ────────────────────────────────────────────────────
    tipo_idx = choose_from_list(
        "Tipo de documento",
        [
            "REC  —  Reclamação",
            "REQ  —  Requerimento / Petição",
            "OFI  —  Ofício",
        ],
    )
    doc_type = ["REC", "REQ", "OFI"][tipo_idx]

    # 4. Subtipo ──────────────────────────────────────────────────────────────
    if doc_type == "REC":
        subtypes = list_subtypes_rec()
    elif doc_type == "REQ":
        subtypes = list_subtypes_req(empresa)
    else:
        subtypes = list_subtypes_ofi()
    if not subtypes:
        console.print(f"[red]  Nenhum subtipo encontrado para {doc_type}.[/red]")
        return False

    st_idx = choose_from_list(
        f"Subtipos disponíveis ({doc_type})",
        [label for label, _ in subtypes],
    )
    _, subtype_path = subtypes[st_idx]
    usa_ip_estimada = subtype_uses_ip_estimada(subtype_path)
    uc_ip_estimada = ""
    if usa_ip_estimada:
        uc_ip_estimada = get_ip_estimada_from_municipio(mun_dados)
        if not uc_ip_estimada:
            console.print(
                "[red]  Erro: a tese selecionada exige a macro \\IPestimada{} "
                "(ou \\IP_estimada{} legado), mas o município não a informou.[/red]"
            )
            return False
        console.print(
            f"  [bold]UC automática (IP estimada):[/bold] {uc_ip_estimada}  "
            "[dim](lida do arquivo do município)[/dim]"
        )

    origem_tipo = ""
    origem_cod = ""
    tese = ""
    if doc_type == "OFI":
        origem_tipo_idx = choose_from_list(
            "Documento de origem do OFI",
            ["REC", "REQ"],
        )
        origem_tipo = ["REC", "REQ"][origem_tipo_idx]

        tese = get_tese_from_subtype(subtype_path)
        if tese:
            console.print(
                f"  TESE [dim](lida de {subtype_path.name})[/dim]: {tese}"
            )
        else:
            console.print(
                "[yellow]  Aviso:[/yellow] macro \\tese não encontrada no subtipo; "
                "será usado o nome do subtipo no nome do arquivo."
            )
            tese = subtype_path.stem

    # 5. Dados do documento ───────────────────────────────────────────────────
    console.print()
    ucs_to_process = []
    if usa_ip_estimada:
        console.print(
            "  [bold]Modo de operação:[/bold] Documento Único "
            "[dim](UC preenchida automaticamente pela macro \\IPestimada{})[/dim]"
        )
        num_doc = Prompt.ask("  Número do documento [dim](ex: 001/2026)[/dim]").strip()
        if doc_type == "OFI":
            origem_cod = prompt_origem_cod(
                "  Código do documento de origem [dim](formato: XXX_XXXX)[/dim]"
            )
        ucs_to_process.append((num_doc, uc_ip_estimada, origem_cod if doc_type == "OFI" else ""))
    else:
        modo_idx = choose_from_list(
            "Modo de operação",
            ["Documento Único", "Lote (Múltiplas UCs)"]
        )

        if modo_idx == 0:
            num_doc = Prompt.ask("  Número do documento [dim](ex: 001/2026)[/dim]").strip()
            uc = Prompt.ask("  Unidade consumidora [dim](deixe em branco se n/a)[/dim]", default="").strip()
            if doc_type == "OFI":
                origem_cod = prompt_origem_cod(
                    "  Código do documento de origem [dim](formato: XXX_XXXX)[/dim]"
                )
            ucs_to_process.append((num_doc, uc, origem_cod if doc_type == "OFI" else ""))
        else:
            num_ini = Prompt.ask("  Número inicial do documento [dim](ex: 001/2026)[/dim]").strip()
            ucs_raw = Prompt.ask("  Lista de UCs [dim](separe por espaço, vírgula ou nova linha)[/dim]").strip()
            ucs_list = [u.strip() for u in re.split(r'[,\s\n]+', ucs_raw) if u.strip()]

            origem_cod_modo = 0
            if doc_type == "OFI":
                origem_cod_modo = choose_from_list(
                    "Numeração do documento de origem",
                    ["Única para todos os documentos", "Em lote (sequencial)"],
                )
                origem_cod = prompt_origem_cod(
                    "  Código do documento de origem [dim](formato: XXX_XXXX)[/dim]"
                    if origem_cod_modo == 0
                    else "  Código inicial do documento de origem [dim](formato: XXX_XXXX)[/dim]"
                )

            curr_num = num_ini
            curr_origem_cod = origem_cod
            for u in ucs_list:
                ucs_to_process.append((curr_num, u, curr_origem_cod if doc_type == "OFI" else ""))
                if doc_type == "OFI" and origem_cod_modo == 1:
                    curr_origem_cod = increment_code(curr_origem_cod)
                curr_num = increment_code(curr_num)

    titulo = get_titulo_from_subtype(subtype_path)
    if titulo:
        console.print(
            f"  Título/descrição [dim](lido do subtipo {subtype_path.name})[/dim]: {titulo}"
        )
    else:
        console.print(
            "  [yellow]Aviso:[/yellow] nenhuma macro de título conhecida foi encontrada no subtipo; "
            "seguindo com título vazio."
        )

    # 6. Gerar ────────────────────────────────────────────────────────────────
    standalone = not is_fragment(subtype_path)

    for n_doc, n_uc, n_origem_cod in ucs_to_process:
        _generate_for_case(
            nome_mun,
            mun_path,
            empresa,
            doc_type,
            subtype_path,
            n_doc,
            n_uc,
            titulo,
            origem_tipo,
            n_origem_cod,
            tese,
            standalone,
        )

    console.print(f"\n[bold green]Finalizado! {len(ucs_to_process)} documento(s) processado(s).[/bold green]")
    return True


def main():
    while True:
        try:
            cycle_ok = _run_generation_cycle()
            if cycle_ok:
                console.print("\n[bold cyan]Reiniciando gerador para um novo documento...[/bold cyan]\n")
            else:
                console.print("\n[yellow]Ciclo encerrado por dados inválidos/incompletos. Reiniciando...[/yellow]\n")
        except KeyboardInterrupt:
            console.print("\n[yellow]Execução interrompida pelo usuário.[/yellow]")
            break


if __name__ == "__main__":
    main()
