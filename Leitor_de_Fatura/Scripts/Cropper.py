# ============================================================== #
# BIBLIOTECAS
# ============================================================== #

import os
import re
import subprocess
import sys
import shutil
from tqdm import tqdm

from pathlib import Path
from templates_cropper import TEMPLATES

from Cropper_logic_functions.cropper_logic_enel         import cropper_logic_enel
from Cropper_logic_functions.cropper_logic_energisa     import cropper_logic_energisa
from Cropper_logic_functions.cropper_logic_neoenergia   import cropper_logic_neoenergia

# ============================================================== #
# CONFIGURAÇÕES
# ============================================================== #

if getattr(sys, "frozen", False):
    diretorio = Path(sys.executable).resolve().parent
else:
    diretorio = Path(__file__).resolve().parent.parent

PATH_FATURAS        = diretorio / "Faturas"            
PATH_CROPPED        = diretorio / "Faturas_Cropped"    
PATH_POPPLER        = diretorio / "Faturas_Poppler"    
PATH_POPPLER_EXE    = diretorio / "poppler" / "Library" / "bin" / "pdftotext.exe"  

# ============================================================== #
# FUNÇÕES
# ============================================================== #

def selecionar_subpasta(caminho_pasta_pai: Path) -> Path:
    '''Lista as subpastas disponíveis em uma pasta pai e permite que o usuário selecione uma delas. Retorna o caminho da subpasta selecionada.'''
    subpastas = sorted([f for f in caminho_pasta_pai.iterdir() if f.is_dir()])
    if not subpastas:
        raise ValueError(f"Nenhuma subpasta encontrada em '{caminho_pasta_pai}'. Certifique-se de que há subpastas.")

    print(f"\n--- SUBPASTAS DISPONÍVEIS EM '{caminho_pasta_pai.name}' ---")
    for i, folder_path in enumerate(subpastas):
        print(f"{i} - {folder_path.name}")
    
    f_choice = int(input("Escolha a pasta (índice): "))
    return subpastas[f_choice]

def renomear_pdfs_em_ordem(src_dir):
    pdf_files = sorted(
        [file_path for file_path in src_dir.iterdir() if file_path.is_file() and file_path.suffix.lower() == ".pdf"]
    )

    if not pdf_files:
        return []

    arquivos_temporarios = []
    for idx, file_path in enumerate(pdf_files):
        temp_path = src_dir / f"__renomeando_pdf_{idx}__.pdf"
        file_path.rename(temp_path)
        arquivos_temporarios.append(temp_path)

    arquivos_renomeados = []
    for idx, temp_path in enumerate(arquivos_temporarios):
        final_path = src_dir / f"{idx}.pdf"
        temp_path.rename(final_path)
        arquivos_renomeados.append(final_path.name)

    return arquivos_renomeados

def limpar_pasta(caminho_pasta: str | Path) -> None:
    """
    Remove todo o conteúdo de uma pasta, mas mantém a própria pasta.

    Args:
        caminho_pasta: Caminho da pasta a ser limpa.
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

def selecionar_modelo(lista):
        modelos_disponiveis = list(lista.keys())
        print("\n--- MODELOS DISPONÍVEIS ---")
        for i, mod in enumerate(modelos_disponiveis): print(f"{i} - {mod}")
        m_choice = int(input("Escolha o modelo (índice): "))
        return modelos_disponiveis[m_choice]

def progresso(pasta: str | Path, processar_pdf):
    """
    Varre todos os PDFs de uma pasta e exibe uma barra de progresso.

    Args:
        pasta: Caminho da pasta contendo os PDFs.
        processar_pdf: Função que receberá um objeto Path para cada PDF.
    """
    pasta = Path(pasta)

    if not pasta.exists():
        raise FileNotFoundError(f"Pasta não encontrada: {pasta}")

    if not pasta.is_dir():
        raise NotADirectoryError(f"O caminho informado não é uma pasta: {pasta}")

    pdfs = list(pasta.glob("*.pdf"))

    if not pdfs:
        print("Nenhum PDF encontrado.")
        return

    for pdf in tqdm(
        pdfs,
        total=len(pdfs),
        desc="Processando PDFs",
        unit="pdf",
        colour="green"
    ):
        processar_pdf(pdf)

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

def integralaiser_orchestrator():
    
    # 1. Garantir que as pastas de saída (Cropped e Poppler) existam.
    PATH_CROPPED.mkdir(parents=True, exist_ok=True)
    PATH_POPPLER.mkdir(parents=True, exist_ok=True)

    # 2. Seleção de Subpasta
    src_dir         = selecionar_subpasta(PATH_FATURAS) # Endereço da subpasta
    nome_subpasta   = src_dir.name                      # Nome da subpasta
    pdf_files       = renomear_pdfs_em_ordem(src_dir)   # PDFs da subpasta
    
    # 2. Seleção de Modelo     
    selected_template_name = selecionar_modelo(TEMPLATES)
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
        cropped_output_name = pdf_path.name.replace(".pdf", "_Cropped.pdf")
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

    progresso(src_dir, processar_um_pdf_para_cropper)

if __name__ == "__main__":
    integralaiser_orchestrator()
