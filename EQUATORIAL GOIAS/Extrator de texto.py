from pathlib import Path
import subprocess


# Pasta onde o próprio script está
pasta = Path(__file__).resolve().parent


def converter_pdf(pdf_path):
    txt_path = pdf_path.with_suffix(".txt")

    comando = [
        "pdftotext",
        "-layout",
        str(pdf_path),
        str(txt_path)
    ]

    try:
        subprocess.run(
            comando,
            check=True,
            capture_output=True,
            text=True
        )

        print(f"✓ {pdf_path.name} -> {txt_path.name}")

    except subprocess.CalledProcessError as erro:
        print(f"✗ Erro ao converter {pdf_path.name}")
        print(erro.stderr)

    except FileNotFoundError:
        print(
            "✗ pdftotext não encontrado. "
            "Verifique se o Poppler está instalado e no PATH."
        )


def main():
    pdfs = list(pasta.glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado.")
        return

    print(f"Encontrados {len(pdfs)} PDFs.\n")

    for pdf in pdfs:
        converter_pdf(pdf)

    print("\nConversão concluída.")


if __name__ == "__main__":
    main()
