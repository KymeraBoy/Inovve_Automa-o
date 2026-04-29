# ============================================================== #
# BIBLIOTECAS
# ============================================================== #

import os
import subprocess
import sys

from pathlib import Path
from templates_cropper import TEMPLATES

from Cropper_logic_functions.cropper_logic_enel         import cropper_logic_enel
from Cropper_logic_functions.cropper_logic_energisa     import cropper_logic_energisa
from Cropper_logic_functions.cropper_logic_neoenergia   import cropper_logic_neoenergiaPE

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

def obter_caminho_unico(dir_path, cropped_name):
    full_path = dir_path / cropped_name    
    # Se o arquivo não existe, retorna o caminho original
    if not full_path.exists():
        return full_path
    # Separa o nome da extensão (ex: "imagem" e ".jpg")
    name, extension = os.path.splitext(cropped_name)    
    # Adiciona "-copia" e verifica repetidamente
    counter = 1
    new_name = f"{name}-copia{extension}"
    new_path = dir_path / new_name    
    while new_path.exists():
        new_name = f"{name}-copia({counter}){extension}"
        new_path = dir_path / new_name
        counter += 1        
    return new_path

def run_pdftotext(input_pdf, output_txt):
    """Executa o comando externo pdftotext via subprocess."""
    try:
        # O argumento '-layout' preserva a estrutura visual do texto
        subprocess.run([PATH_POPPLER_EXE, "-layout", "-enc", "UTF-8", input_pdf, output_txt], check=True)
        return True
    except Exception as e:
        print(f"Erro ao converter {input_pdf}: {e}")
        return False

def format_progress_bar(current, total, width=30):
    """Cria uma barra textual de progresso com preenchimento proporcional."""
    if total <= 0:
        return "[------------------------------]   0.0%"
    ratio = current / total
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {ratio * 100:5.1f}%"

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

# ============================================================== #
# EXECUÇÃO
# ============================================================== #

def integralaiser_orchestrator():
    if not os.path.exists(PATH_CROPPED): os.makedirs(PATH_CROPPED)  # Verifica se o caminho de saída já existe, e cria um caso não exista
    if not os.path.exists(PATH_POPPLER): os.makedirs(PATH_POPPLER)  # Verifica se o caminho de saída dos txts já existe

    # 1. Seleção de Pasta
    subfolders = [f for f in os.listdir(PATH_FATURAS) if os.path.isdir(os.path.join(PATH_FATURAS, f))]  # Essa variavel ira conter a lista de passtas dentro da pasta de Faturas
    print("\n--- PASTAS DISPONÍVEIS ---")
    for i, folder in enumerate(subfolders): print(f"{i} - {folder}")
    f_choice = int(input("Escolha a pasta (índice): "))
    selected_folder = subfolders[f_choice]
    src_dir = PATH_FATURAS / selected_folder
    pdf_files = renomear_pdfs_em_ordem(src_dir)
    print(f"PDFs renomeados na pasta {selected_folder}: {len(pdf_files)} arquivo(s).")
    
    # 2. Seleção de Modelo 
    modelos_disponiveis = list(TEMPLATES.keys())
    print("\n--- MODELOS DISPONÍVEIS ---")
    for i, mod in enumerate(modelos_disponiveis): print(f"{i} - {mod}")
    m_choice = int(input("Escolha o modelo (índice): "))
    selected_template_name = modelos_disponiveis[m_choice]
    selected_template = TEMPLATES[selected_template_name]

    # 3. Processamento: Garante e salva os endereços das pastas e subpastas de origem e de saída
    dst_dir = PATH_CROPPED / f"{selected_folder}_Cropped"
    txt_dir = PATH_POPPLER / f"{selected_folder}_Poppler"
    if not os.path.exists(dst_dir): os.makedirs(dst_dir)
    if not os.path.exists(txt_dir): os.makedirs(txt_dir)

    lista = os.listdir(src_dir)
    pdf_files = [file_name for file_name in lista if file_name.lower().endswith('.pdf')]
    total_pdfs = len(pdf_files)
    print(f"Quantidade de documentos: {len(lista)}")
    print(f"Quantidade de PDFs para processar: {total_pdfs}")

    poppler_disponivel = os.path.exists(PATH_POPPLER_EXE)
    if not poppler_disponivel:
        print(f"Aviso: pdftotext não encontrado em {PATH_POPPLER_EXE}. A etapa de conversão para txt será ignorada.")

    for idx, file_name in enumerate(pdf_files, start=1):
        restantes = total_pdfs - idx
        barra = format_progress_bar(idx, total_pdfs)
        print(f"\n{barra} | {idx}/{total_pdfs} processados | {restantes} restantes")

        input_file = os.path.join(src_dir, file_name)
        output_file = os.path.join(dst_dir, f"{os.path.splitext(file_name)[0]}_Cropped.pdf")
        print(f"Processando {file_name} com template {selected_template_name}...")
        cropped_pdf_path = output_file
        if selected_template_name == "ENEL":
            cropped_pdf_path = cropper_logic_enel(input_file, output_file, selected_template)
        if selected_template_name == "ENERGISA":
            cropped_pdf_path = cropper_logic_energisa(input_file, output_file, selected_template)
        if selected_template_name == "NEOENERGIA":
            cropped_pdf_path = cropper_logic_neoenergiaPE(input_file, output_file, selected_template)

        if poppler_disponivel and cropped_pdf_path and os.path.exists(cropped_pdf_path):
            txt_name = os.path.basename(cropped_pdf_path).replace("Cropped", "Poppler").replace(".pdf", ".txt")
            output_txt = os.path.join(txt_dir, txt_name)
            print(f"Convertendo para txt: {os.path.basename(cropped_pdf_path)} -> {txt_name}")
            run_pdftotext(cropped_pdf_path, output_txt)
        elif poppler_disponivel:
            
            (f"Aviso: PDF cropado não encontrado para conversão: {cropped_pdf_path}")

if __name__ == "__main__":
    integralaiser_orchestrator()
