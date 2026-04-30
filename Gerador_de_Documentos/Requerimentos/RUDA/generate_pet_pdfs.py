import shutil
import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "DOCUMENTOS_GERADOS"
BUILD_DIR = ROOT_DIR / "__latex_build__"


def clear_directory(directory: Path) -> None:
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True, exist_ok=True)


def find_main_tex_file(folder: Path) -> Path | None:
    tex_files = sorted(path for path in folder.glob("*.tex") if path.is_file())
    if len(tex_files) != 1:
        return None
    return tex_files[0]


def build_pdf(tex_file: Path) -> None:
    command = [
        "xelatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={BUILD_DIR}",
        tex_file.name,
    ]

    for _ in range(2):
        result = subprocess.run(
            command,
            cwd=tex_file.parent,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Falha ao compilar {tex_file.name}\n{result.stdout}\n{result.stderr}"
            )

    generated_pdf = BUILD_DIR / f"{tex_file.stem}.pdf"
    if not generated_pdf.exists():
        raise FileNotFoundError(f"PDF nao encontrado apos compilacao: {generated_pdf.name}")

    shutil.copy2(generated_pdf, OUTPUT_DIR / generated_pdf.name)


def generate_pdfs() -> None:
    if shutil.which("xelatex") is None:
        raise RuntimeError("XeLaTeX nao foi encontrado no PATH do sistema.")

    clear_directory(OUTPUT_DIR)
    clear_directory(BUILD_DIR)

    try:
        for folder in sorted(ROOT_DIR.iterdir()):
            if not folder.is_dir() or not folder.name.startswith("PET_"):
                continue

            tex_file = find_main_tex_file(folder)
            if tex_file is None:
                print(f"[skip] {folder.name}: esperado exatamente um arquivo .tex")
                continue

            build_pdf(tex_file)
            print(f"[ok] {tex_file.stem}.pdf gerado")
    finally:
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)


if __name__ == "__main__":
    generate_pdfs()