from pathlib import Path
import subprocess

# Pasta onde o próprio script está
pasta = Path(__file__).resolve().parent.parent

# Caminho do pdftotext.exe dentro da pasta do programa
PDFTOTEXT = pasta / "LEITOR DE FATURAS" / "Poppler" / "Library" / "bin" / "pdftotext.exe"
pasta = Path(__file__).resolve().parent

def converter_pdf(pdf_path):
    txt_path = pdf_path.with_suffix(".txt")

    comando = [
        str(PDFTOTEXT),
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
            f"✗ pdftotext não encontrado.\n"
            f"Procurado em:\n{PDFTOTEXT}\n\n"
            "Verifique se a pasta do Poppler está no local correto."
        )


def main():
    pdfs = list(pasta.glob("*.pdf")) + list(pasta.glob("*.PDF"))

    if not pdfs:
        print("Nenhum PDF encontrado.")
        return

    print(f"Encontrados {len(pdfs)} PDFs.\n")

    for pdf in pdfs:
        converter_pdf(pdf)

    print("\nConversão concluída.")


if __name__ == "__main__":
    main()