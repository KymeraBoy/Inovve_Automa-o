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
# CONFIGURAÇÕES
# ============================================================== #

diretorio = Path(__file__).resolve().parent.parent

PATH_FATURAS        = diretorio / "Faturas"            
PATH_CROPPED        = diretorio / "Faturas_Cropped"    
PATH_POPPLER        = diretorio / "Faturas_Poppler"    
PATH_POPPLER_EXE    = diretorio / "poppler" / "Library" / "bin" / "pdftotext.exe"  

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
    """
    Remove todo o conteúdo de uma pasta, mas mantém a própria pasta.
    Args: caminho_pasta: Caminho da pasta a ser limpa.
    """
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
    '''Retorna o template correspondente ao nome da concessionária fornecida.'''
    return templates_dict[concessionaria_name]


def obter_caminho_unico(dir_path, cropped_name):
    '''Pega a pasta e o nome do arquivo, ve se tem um arquivo com mesmo nome, caso tenh adiciona o sufixo "-copia" e um contador para criar um nome unico, evitando sobrescrever arquivos existentes.'''

    full_path = dir_path / cropped_name    
    # Se o arquivo não existe, retorna o caminho original
    if not full_path.exists():
        return full_path
    # Separa o nome da extensão (ex: "imagem" e ".jpg")
    name, extension = os.path.splitext(cropped_name)    

    stem = full_path.stem
    suffix = full_path.suffix
    # Adiciona "-copia" e verifica repetidamente
    counter = 1
    new_name = f"{name}-copia{extension}"
    new_path = dir_path / new_name    
    new_path = dir_path / f"{stem}-copia{suffix}"
    while new_path.exists():
        new_name = f"{name}-copia({counter}){extension}"
        new_path = dir_path / new_name
        new_path = dir_path / f"{stem}-copia({counter}){suffix}"
        counter += 1        
    return new_path


# ============================================================== #
# EXECUÇÃO
# ============================================================== #

def cropper_orchestrator(municipio_name: str, concessionaria_name: str, progress_callback=None):
    
    # 1. Garantir que as pastas de saída (Cropped e Poppler) existam.
    PATH_CROPPED.mkdir(parents=True, exist_ok=True)
    PATH_POPPLER.mkdir(parents=True, exist_ok=True)

    # 2. Seleção de Subpasta
    src_dir         = selecionar_subpasta(PATH_FATURAS, municipio_name) # Endereço da subpasta
    nome_subpasta   = src_dir.name                                      # Nome da subpasta
    pdf_files       = sorted([f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]) # PDFs da subpasta
    
    # 2. Seleção de Modelo (agora recebe o nome da concessionária)
    selected_template_name = concessionaria_name
    selected_template = TEMPLATES[selected_template_name]

    if selected_template_name == "NEOENERGIA":
        ind_dir = src_dir / f"{src_dir.name}-INDIVIDUAIS"    
        ind_dir.mkdir(parents=True, exist_ok=True)
        limpar_pasta(ind_dir)

    # 3. Processamento: Garante e salva os endereços das pastas e subpastas de origem e de saída
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
        # Determine the output path for the cropped PDF
        # A lógica de renomear_pdfs_em_ordem foi removida, então o nome do arquivo de saída deve ser baseado no original
        # ou em um novo esquema se necessário. Por enquanto, vamos manter o nome original com sufixo.
        # Se a renomeação sequencial for crucial, ela precisará ser reintroduzida ou adaptada.
        # Para este diff, assumimos que o nome original do PDF é suficiente para o output.
        cropped_output_name = f"{pdf_path.stem}_Cropped.pdf"
        output_cropped_path = dst_dir / cropped_output_name

        # Determine the output path for the Poppler TXT (if applicable)
        poppler_output_name = pdf_path.name.replace(".pdf", "_Poppler.txt")
        output_poppler_path = txt_dir / poppler_output_name

        if selected_template_name == "ENEL":
            # cropper_logic_enel expects input_path, output_path, template
            cropper_logic_enel(pdf_path, output_cropped_path, selected_template)
            # A lógica original não gerava TXT para ENEL.

        elif selected_template_name == "ENERGISA":
            # cropper_logic_energisa agora espera input_path e output_dir.
            # A função foi modificada para não renomear o arquivo de entrada.
            cropper_logic_energisa(pdf_path, dst_dir, selected_template)
            # A lógica original não gerava TXT para ENERGISA.

        if selected_template_name == "NEOENERGIA":
            # cropper_logic_neoenergia lida com a criação de múltiplos PDFs e TXTs internamente.
            # Criar a pasta de faturas individuais            
            cropper_logic_neoenergia(pdf_path, dst_dir, txt_dir, ind_dir, selected_template, PATH_POPPLER_EXE)          
    
    total_pdfs = len(pdf_files)
    for idx, pdf_path in enumerate(pdf_files):
        if progress_callback:
            progress_callback(idx + 1, total_pdfs, f"Cropper: Processando {pdf_path.name} ({idx + 1}/{total_pdfs})...")
        processar_um_pdf_para_cropper(pdf_path)
    print("\nFluxo Cropper finalizado.")

if __name__ == "__main__": # Este bloco é para permitir que o script Cropper.py seja executado diretamente para testes, se necessário.
    print("Este script não deve ser executado diretamente. Use a GUI.")
