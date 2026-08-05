from __future__ import annotations

from configuracao.config import CONFIG


def listar_empresas() -> list[str]:
    empresas = [p.name.upper() for p in CONFIG.empresas_dir.iterdir() if p.is_dir()]
    return sorted(set(empresas))


def inferir_empresa_por_municipio(municipio_meta: dict[str, str]) -> str:
    return municipio_meta.get("empresa", "").strip().upper()
