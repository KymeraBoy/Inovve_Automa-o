# ============================================================== #
# BIBLIOTECAS
# ============================================================== #

import os
import re
import subprocess
import shutil

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
    
    # 1. Garantir que as pastas de saída existam no diretório do usuário
    PATH_CROPPED.mkdir(parents=True, exist_ok=True)
    PATH_POPPLER.mkdir(parents=True, exist_ok=True)

    # 2. Seleção de Subpasta baseado no diretório apontado
    src_dir         = selecionar_subpasta(PATH_FATURAS, municipio_name) 
    nome_subpasta   = src_dir.name                                      
    pdf_files       = sorted([f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]) 
    
    selected_template_name = concessionaria_name
    selected_template = TEMPLATES[selected_template_name]

    if selected_template_name == "NEOENERGIA":
        ind_dir = src_dir / f"{src_dir.name}-INDIVIDUAIS"    
        ind_dir.mkdir(parents=True, exist_ok=True)
        limpar_pasta(ind_dir)

    # 3. Processamento local no workspace do usuário
    dst_dir = PATH_CROPPED / f"{nome_subpasta}_Cropped"
    txt_dir = PATH_POPPLER / f"{nome_subpasta}_Poppler"    
    dst_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    limpar_pasta(dst_dir)
    limpar_pasta(txt_dir)    
        
    print(f"Quantidade de PDFs para processar: {len(pdf_files)}")

    poppler_disponivel = PATH_POPPLER_EXE.exists()
    if not poppler_disponivel:
        print(f"Aviso: pdftotext não encontrado em {PATH_POPPLER_EXE}. A etapa de conversão para txt será ignorada.")
    
    def processar_um_pdf_para_cropper(pdf_path: Path):
        cropped_output_name = f"{pdf_path.stem}_Cropped.pdf"
        output_cropped_path = dst_dir / cropped_output_name

        poppler_output_name = pdf_path.name.replace(".pdf", "_Poppler.txt")
        output_poppler_path = txt_dir / poppler_output_name

        if selected_template_name == "ENEL":
            cropper_logic_enel(pdf_path, output_cropped_path, selected_template)
        elif selected_template_name == "ENERGISA":
            cropper_logic_energisa(pdf_path, dst_dir, selected_template)
        elif selected_template_name == "NEOENERGIA":
            cropper_logic_neoenergia(pdf_path, dst_dir, txt_dir, ind_dir, selected_template, PATH_POPPLER_EXE)          
    
    total_pdfs = len(pdf_files)
    for idx, pdf_path in enumerate(pdf_files):
        if progress_callback:
            progress_callback(idx + 1, total_pdfs, f"Cropper: Processando {pdf_path.name} ({idx + 1}/{total_pdfs})...")
        processar_um_pdf_para_cropper(pdf_path)
    print("\nFluxo Cropper finalizado.")

if __name__ == "__main__": 
    print("Este script não deve ser executado diretamente. Use a GUI.")