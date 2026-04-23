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

diretorio = Path(__file__).resolve().parent.parent
print(f"Diretório do script: {diretorio}")

PATH_FATURAS = diretorio / "Faturas"            # Endereço da pasta onde estão guardadas as subpastas contendo as faturas
PATH_CROPPED = diretorio / "Faturas_Cropped"    # Enderço de para onde vão as subpastas contendo os PDFs croppados
PATH_POPPLER = diretorio / "Faturas_Poppler"    # Endereço para onde vão os arquivos txt extraídos dos PDFs cropados

# ============================================================== #
# FUNÇÕES
# ============================================================== #

def obter_caminho_unico(dir_path, cropped_name):
    full_path = os.path.join(dir_path, cropped_name)    
    # Se o arquivo não existe, retorna o caminho original
    if not os.path.exists(full_path):
        return full_path
    # Separa o nome da extensão (ex: "imagem" e ".jpg")
    name, extension = os.path.splitext(cropped_name)    
    # Adiciona "-copia" e verifica repetidamente
    counter = 1
    new_name = f"{name}-copia{extension}"
    new_path = os.path.join(dir_path, new_name)    
    while os.path.exists(new_path):
        new_name = f"{name}-copia({counter}){extension}"
        new_path = os.path.join(dir_path, new_name)
        counter += 1        
    return new_path

def obter_caminho_poppler():
    # Detecta se o script está rodando como um executável (.exe) ou script (.py)
    if getattr(sys, 'frozen', False):
        diretorio_atual = os.path.dirname(sys.executable)
    else:
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))

    # Aceita tanto pasta "Poppler" quanto "poppler"
    caminhos_possiveis = [
        os.path.join(diretorio_atual, "Poppler", "bin", "pdftotext.exe"),
        os.path.join(diretorio_atual, "poppler", "bin", "pdftotext.exe"),
    ]

    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            return caminho

    return caminhos_possiveis[0]

PATH_POPPLER_EXE = obter_caminho_poppler()

def run_pdftotext(input_pdf, output_txt):
    """Executa o comando externo pdftotext via subprocess."""
    try:
        # O argumento '-layout' preserva a estrutura visual do texto
        subprocess.run([PATH_POPPLER_EXE, "-layout", "-enc", "UTF-8", input_pdf, output_txt], check=True)
        return True
    except Exception as e:
        print(f"Erro ao converter {input_pdf}: {e}")
        return False

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
    
    # 2. Seleção de Modelo 
    modelos_disponiveis = list(TEMPLATES.keys())
    print("\n--- MODELOS DISPONÍVEIS ---")
    for i, mod in enumerate(modelos_disponiveis): print(f"{i} - {mod}")
    m_choice = int(input("Escolha o modelo (índice): "))
    selected_template_name = modelos_disponiveis[m_choice]
    selected_template = TEMPLATES[selected_template_name]

    # 3. Processamento: Garante e salva os endereços das pastas e subpastas de origem e de saída
    src_dir = os.path.join(PATH_FATURAS, selected_folder)
    dst_dir = os.path.join(PATH_CROPPED, f"{selected_folder}_Cropped") 
    txt_dir = os.path.join(PATH_POPPLER, f"{selected_folder}_Poppler")
    if not os.path.exists(dst_dir): os.makedirs(dst_dir)
    if not os.path.exists(txt_dir): os.makedirs(txt_dir)

    lista = os.listdir(src_dir)
    print(f"Quantidade de documentos: {len(lista)}")

    poppler_disponivel = os.path.exists(PATH_POPPLER_EXE)
    if not poppler_disponivel:
        print(f"Aviso: pdftotext não encontrado em {PATH_POPPLER_EXE}. A etapa de conversão para txt será ignorada.")

    for file_name in os.listdir(src_dir):
        if file_name.lower().endswith('.pdf'):
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
                print(f"Aviso: PDF cropado não encontrado para conversão: {cropped_pdf_path}")

if __name__ == "__main__":
    integralaiser_orchestrator()