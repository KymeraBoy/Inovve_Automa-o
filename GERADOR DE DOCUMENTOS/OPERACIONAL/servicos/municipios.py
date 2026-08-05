from __future__ import annotations

import re
from pathlib import Path

from configuracao.config import CONFIG

_CMD_RE = re.compile(r"\\(?:new|provide|renew)command\s*\{\\(\w+)\}\s*\{([^}]*)\}")


def parse_latex_commands(content: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in _CMD_RE.finditer(content)}


def parse_municipio_file(path: Path) -> dict[str, str]:
    try:
        return parse_latex_commands(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def listar_municipios() -> list[dict[str, str]]:
    """Lista municipios a partir dos arquivos Dados_*.tex."""
    resultado: list[dict[str, str]] = []
    for arquivo in sorted(CONFIG.municipios_dir.glob("Dados_*.tex")):
        dados = parse_municipio_file(arquivo)
        nome = dados.get("nomeMunicipio") or arquivo.stem.replace("Dados_", "").replace("_", " ")
        resultado.append(
            {
                "nome": nome,
                "arquivo": arquivo.name,
                "caminho": str(arquivo),
                "empresa": dados.get("empresaResponsavel", "").strip().upper(),
                "ip_estimada": dados.get("IPestimada", "").strip() or dados.get("IP_estimada", "").strip(),
            }
        )
    return resultado


def mapa_municipios() -> dict[str, dict[str, str]]:
    """Retorna mapa nome -> metadados para uso rapido na interface."""
    return {item["nome"]: item for item in listar_municipios()}
