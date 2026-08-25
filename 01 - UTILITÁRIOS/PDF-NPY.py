import fitz
import numpy as np
from pathlib import Path


def pdf_para_npy(pdf_path: Path, dpi: int = 100) -> None:
    doc = fitz.open(pdf_path)

    try:
        page = doc[0]

        escala = dpi / 72
        matriz = fitz.Matrix(escala, escala)

        pix = page.get_pixmap(
            matrix=matriz,
            colorspace=fitz.csGRAY,
            alpha=False
        )

        imagem = np.frombuffer(
            pix.samples,
            dtype=np.uint8
        ).reshape(
            pix.height,
            pix.width
        )

        npy_path = pdf_path.with_suffix(".npy")

        np.save(npy_path, imagem)

        print(f"Convertido: {pdf_path.name} -> {npy_path.name}")

    finally:
        doc.close()


def converter_pasta(pasta: str = ".") -> None:
    pasta = Path(pasta)

    pdfs = list(pasta.glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado.")
        return

    for pdf_path in pdfs:
        pdf_para_npy(pdf_path)


if __name__ == "__main__":
    converter_pasta(r"C:\Users\Usuário 1\Documents\LEITOR DE FATURAS LOCAL\Faturas\ENERGISA - SALGADO DE SÃO FÉLIX")