# ============================================================== #
# BIBLIOTECAS
# ============================================================== #

import os
import re
import uuid
import fitz
import shutil
import subprocess

from pathlib import Path
from templates_cropper import TEMPLATES

from Cropper_logic_functions.cropper_logic_enel         import cropper_logic_enel
from Cropper_logic_functions.cropper_logic_energisa     import cropper_logic_energisa
from Cropper_logic_functions.cropper_logic_neoenergia   import cropper_logic_neoenergia

# ============================================================== #
# CONFIGURAÇÕES (Serão sobrescritas dinamicamente pela GUI)
# ============================================================== #

PATH_FATURAS        = Path(".")            
PATH_CROPPED        = Path(".")    
PATH_POPPLER        = Path(".")    
PATH_POPPLER_EXE    = Path(".")  

# ============================================================== #
# FUNÇÕES
# ============================================================== #

def selecionar_subpasta(caminho_pasta_pai: Path, municipio_name: str) -> Path:
    '''Retorna o caminho da subpasta correspondente ao nome do município fornecido.'''
    subpastas = sorted([f for f in caminho_pasta_pai.iterdir() if f.is_dir()])
    if not subpastas:
        raise ValueError(f"Nenhuma subpasta encontrada em '{caminho_pasta_pai}'. Certifique-se de que há subpastas.")

    for folder_path in subpastas:
        if folder_path.name == municipio_name:
            return folder_path
    raise ValueError(f"Município '{municipio_name}' não encontrado em '{caminho_pasta_pai}'.")

def limpar_pasta(caminho_pasta: Path) -> None:
    pasta = Path(caminho_pasta)
    if not pasta.exists():
        raise FileNotFoundError(f"A pasta '{pasta}' não existe.")
    if not pasta.is_dir():
        raise NotADirectoryError(f"'{pasta}' não é uma pasta.")
    for item in pasta.iterdir():
        if item.is_file() or item.is_symlink():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)

def selecionar_modelo(templates_dict: dict, concessionaria_name: str) -> dict:
    return templates_dict[concessionaria_name]

def obter_caminho_unico(dir_path, cropped_name):
    full_path = dir_path / cropped_name    
    if not full_path.exists():
        return full_path
    name, extension = os.path.splitext(cropped_name)    
    stem = full_path.stem
    suffix = full_path.suffix
    counter = 1
    new_path = dir_path / f"{stem}-copia{suffix}"
    while new_path.exists():
        new_path = dir_path / f"{stem}-copia({counter}){suffix}"
        counter += 1        
    return new_path

# ============================================================== #
# EXECUÇÃO
# ============================================================== #

def cropper_orchestrator(municipio_name: str, concessionaria_name: str, progress_callback=None):
    
    # Garante que as pastas de saída (Poppler e Cropper) existam
    PATH_CROPPED.mkdir(parents=True, exist_ok=True)
    PATH_POPPLER.mkdir(parents=True, exist_ok=True)

    # Seleciona a Subpasta (Município) baseado no diretório apontado
    src_dir                 = selecionar_subpasta(PATH_FATURAS, municipio_name) 
    nome_subpasta           = src_dir.name                                      
    pdf_files               = sorted([f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]) 
    selected_template_name  = concessionaria_name
    selected_template       = TEMPLATES[selected_template_name]

    # Garante que vai haver uma pasta da pasta ne faturas da Neoenergia para alocação das individuais
    if selected_template_name == "NEOENERGIA":
        ind_dir = src_dir / f"{src_dir.name}-INDIVIDUAIS"    
        ind_dir.mkdir(parents=True, exist_ok=True)
        limpar_pasta(ind_dir)
    
    # Garante a existência das pastas Cropped e Poppler para o município selecionado e limpa elas
    dst_dir = PATH_CROPPED / f"{nome_subpasta}_Cropped"
    txt_dir = PATH_POPPLER / f"{nome_subpasta}_Poppler"    
    dst_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    limpar_pasta(dst_dir)
    limpar_pasta(txt_dir)    
        
    print(f"Quantidade de PDFs para processar: {len(pdf_files)}")

    # Verifica se o Poppler existe
    poppler_disponivel = PATH_POPPLER_EXE.exists()
    if not poppler_disponivel:
        print(f"Aviso: pdftotext não encontrado em {PATH_POPPLER_EXE}. A etapa de conversão para txt será ignorada.")
    
    # Função para processamento de um PDF (definição necessária para existência da barra de progresso)
    def processar_um_pdf_para_cropper(pdf_path: Path):
        cropped_output_name = f"{pdf_path.stem}_Cropped.pdf"
        output_cropped_path = dst_dir / cropped_output_name

        # Lê o texto do PDF
        with fitz.open(pdf_path) as pdf:
            texto_pdf = ""

            for pagina in pdf:
                texto_pdf += pagina.get_text()

        # Normaliza para facilitar a busca
        texto_pdf = texto_pdf.upper()

        # Identifica o template diretamente pelo conteúdo do PDF
        if "ENEL" in texto_pdf:
            selected_template = TEMPLATES["ENEL"]

            cropper_logic_enel(
                pdf_path,
                output_cropped_path,
                selected_template
            )

        elif "ENERGISA" in texto_pdf:
            selected_template = TEMPLATES["ENERGISA"]

            cropper_logic_energisa(
                pdf_path,
                dst_dir,
                txt_dir,
                selected_template,
                PATH_POPPLER_EXE
            )

        elif "NEOENERGIA" in texto_pdf:
            selected_template = TEMPLATES["NEOENERGIA"]

            cropper_logic_neoenergia(
                pdf_path,
                dst_dir,
                txt_dir,
                ind_dir,
                selected_template,
                PATH_POPPLER_EXE
            )

        else:
            raise ValueError(
                f"Não foi possível identificar o template do PDF: {pdf_path.name}"
            )
    # Barra de progresso
    total_pdfs = len(pdf_files)
    for idx, pdf_path in enumerate(pdf_files):
        if progress_callback:
            progress_callback(idx + 1, total_pdfs, f"Cropper: Processando {pdf_path.name} ({idx + 1}/{total_pdfs})...")
        processar_um_pdf_para_cropper(pdf_path)
    print("\nFluxo Cropper finalizado.")

if __name__ == "__main__": 
    print("Este script não deve ser executado diretamente. Use a GUI.")