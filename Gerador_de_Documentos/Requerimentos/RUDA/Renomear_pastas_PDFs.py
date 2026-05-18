import re
import unicodedata
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
INFO_FILE = ROOT_DIR.parent / "info.tex"
PET_FOLDER_PATTERN = re.compile(r"^PET_\d+-\d{4}_(.+)$")
MUNICIPIO_PATTERN = re.compile(r"\\newcommand\{\\Municipio\}\{([^}]*)\}")
ANO_PATTERN = re.compile(r"\\newcommand\{\\Ano\}\{([^}]*)\}")
NUMERODOC_PATTERN = re.compile(r"\\newcommand\{\\NumeroDoc\}\{([^}]*)\}")


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    safe_name = re.sub(r"[^A-Za-z0-9]+", "-", without_accents).strip("-")
    return safe_name.upper()


def get_municipio_name() -> str:
    info_content = INFO_FILE.read_text(encoding="utf-8")
    match = MUNICIPIO_PATTERN.search(info_content)
    if match is None:
        raise ValueError("Nao foi possivel localizar \\Municipio em info.tex")
    municipio = match.group(1).strip()
    if not municipio:
        raise ValueError("O valor de \\Municipio em info.tex esta vazio")
    return normalize_name(municipio)


def get_ano() -> str:
    info_content = INFO_FILE.read_text(encoding="utf-8")
    match = ANO_PATTERN.search(info_content)
    if match is None:
        raise ValueError("Nao foi possivel localizar \\Ano em info.tex")
    return match.group(1).strip()


def get_numerodoc(tex_file: Path) -> str | None:
    content = tex_file.read_text(encoding="utf-8")
    match = NUMERODOC_PATTERN.search(content)
    if match is None:
        return None
    value = match.group(1).strip()
    try:
        return f"{int(value):03d}"
    except ValueError:
        return value


def get_description_from_folder(folder_name: str, municipio_name: str) -> str | None:
    """Extrai a descricao do nome da pasta, removendo o prefixo PET_num-ano e o municipio se presente."""
    match = PET_FOLDER_PATTERN.match(folder_name)
    if match is None:
        return None
    rest = match.group(1)  # ex: GURINHEM_INCLUSAO-E-MAILS ou INCLUSAO-E-MAILS
    # remove municipio do inicio se ja estiver presente
    if rest.startswith(municipio_name + "_"):
        rest = rest[len(municipio_name) + 1:]
    return normalize_name(rest)


def rename_tex_files() -> None:
    municipio_name = get_municipio_name()
    ano = get_ano()

    for folder in sorted(ROOT_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("PET"):
            continue

        tex_files = [path for path in folder.glob("*.tex") if path.is_file()]
        if not tex_files:
            print(f"[skip] {folder.name}: nenhum arquivo .tex encontrado")
            continue

        if len(tex_files) > 1:
            print(f"[skip] {folder.name}: mais de um arquivo .tex encontrado")
            continue

        current_file = tex_files[0]

        numero_doc = get_numerodoc(current_file)
        if numero_doc is None:
            print(f"[skip] {folder.name}: \\NumeroDoc nao encontrado em {current_file.name}")
            continue

        description = get_description_from_folder(folder.name, municipio_name)
        if description is None:
            print(f"[skip] {folder.name}: nao foi possivel extrair descricao do nome da pasta")
            continue

        target_base_name = f"PET_{numero_doc}-{ano}_{municipio_name}_{description}"
        target_file = folder / f"{target_base_name}.tex"
        final_folder = ROOT_DIR / target_base_name

        if current_file.resolve() == target_file.resolve() and folder.resolve() == final_folder.resolve():
            print(f"[ok] {folder.name}: nomes ja estao corretos")
            continue

        if current_file.name != target_file.name:
            if target_file.exists():
                print(f"[skip] {folder.name}: {target_file.name} ja existe")
                continue
            current_file.rename(target_file)
            print(f"[renamed-file] {current_file.name} -> {target_file.name}")

        if folder.resolve() != final_folder.resolve():
            if final_folder.exists():
                print(f"[skip] {folder.name}: pasta {final_folder.name} ja existe")
                continue
            folder.rename(final_folder)
            print(f"[renamed-folder] {folder.name} -> {final_folder.name}")


if __name__ == "__main__":
    rename_tex_files()