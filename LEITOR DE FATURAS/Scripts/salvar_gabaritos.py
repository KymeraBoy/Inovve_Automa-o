from pathlib import Path
import numpy as np
from PIL import Image
from pathlib import Path
from pdf2image import convert_from_path

def pdf_para_imagem_gray(caminho_pdf: Path, dpi: int = 150) -> np.ndarray:
    """Converte a primeira página do PDF em uma imagem OpenCV em escala de cinza."""
    paginas = convert_from_path(caminho_pdf, first_page=1, last_page=1, dpi=dpi)
    imagem_pil = paginas[0].convert("L")
    return np.array(imagem_pil)
    
def preparar_gabaritos(
    caminho_gabaritos: Path,
    caminho_cache: Path
) -> None:
    """
    Converte os PDFs de gabarito para imagens em escala de cinza
    e salva as imagens em formato .npy.

    A conversão só é feita novamente se o arquivo .npy
    ainda não existir ou se o PDF tiver sido alterado.
    """

    if not caminho_gabaritos.is_dir():
        raise FileNotFoundError(
            f"Pasta de gabaritos não encontrada: {caminho_gabaritos}"
        )

    caminho_cache.mkdir(parents=True, exist_ok=True)

    arquivos_pdf = sorted(caminho_gabaritos.glob("*.pdf"))

    if not arquivos_pdf:
        raise ValueError(
            f"Nenhum PDF encontrado em: {caminho_gabaritos}"
        )

    for caminho_pdf in arquivos_pdf:

        caminho_npy = caminho_cache / f"{caminho_pdf.stem}.npy"

        # Se o cache existe e é mais recente que o PDF,
        # não precisamos processar novamente.
        if (
            caminho_npy.exists()
            and caminho_npy.stat().st_mtime >= caminho_pdf.stat().st_mtime
        ):
            print(f"[Gabarito] Cache já existe: {caminho_pdf.name}")
            continue

        print(f"[Gabarito] Convertendo: {caminho_pdf.name}")

        imagem = pdf_para_imagem_gray(caminho_pdf)

        np.save(caminho_npy, imagem)

        print(f"[Gabarito] Salvo: {caminho_npy}")

gabaritos = Path(r"C:\Users\Usuário 1\Documents\Inovve_Automação\LEITOR DE FATURAS\Faturas\ENERGISA")
caminho_cache = Path(r"C:\Users\Usuário 1\Documents\Inovve_Automação\LEITOR DE FATURAS\Gabaritos Energisa")
preparar_gabaritos(gabaritos, caminho_cache)