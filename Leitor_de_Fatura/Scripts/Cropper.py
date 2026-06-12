# ============================================================== #
# BIBLIOTECAS
# ============================================================== #

import os
import re
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
        inserir_divisorias_paginas_txt(output_txt)
        return True
    except Exception as e:
        print(f"Erro ao converter {input_pdf}: {e}")
        return False


def inserir_divisorias_paginas_txt(caminho_txt):
    """Insere divisorias legiveis entre paginas em arquivos de texto do Poppler."""
    if not os.path.exists(caminho_txt):
        return

    with open(caminho_txt, "r", encoding="utf-8", errors="replace") as arquivo:
        conteudo = arquivo.read()

    # O pdftotext separa paginas por \f; mantemos o texto original e inserimos marcadores entre paginas.
    paginas = [pagina.strip("\r\n") for pagina in conteudo.replace("\r\n", "\n").split("\f") if pagina.strip()]
    if len(paginas) <= 1:
        return

    separadas = []
    for indice, pagina in enumerate(paginas, start=1):
        separadas.append(pagina)
        if indice < len(paginas):
            separadas.append(f"\n===== FIM_PAGINA_{indice} | INICIO_PAGINA_{indice + 1} =====\n")

    with open(caminho_txt, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(separadas).strip() + "\n")


def normalizar_nome_por_tag(nome_arquivo, tag, nova_extensao=None):
    nome_base, ext = os.path.splitext(nome_arquivo)
    nome_limpo = re.sub(r"(?:_(?:Cropped|Poppler))+\Z", "", nome_base, flags=re.IGNORECASE)
    extensao = nova_extensao if nova_extensao is not None else ext
    return f"{nome_limpo}_{tag}{extensao}"

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


def listar_pdfs_disponiveis(src_dir):
    return sorted(
        [file_path.name for file_path in src_dir.iterdir() if file_path.is_file() and file_path.suffix.lower() == ".pdf"]
    )


def processar_cropper(
    src_dir,
    selected_template_name,
    selected_template,
    selected_files=None,
    progress_callback=None,
    log_callback=None,
    gerar_txt=True,
    limpar_saida=False,
):
    dst_dir = PATH_CROPPED / f"{src_dir.name}_Cropped"
    txt_dir = PATH_POPPLER / f"{src_dir.name}_Poppler"
    os.makedirs(dst_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)

    if limpar_saida:
        for pasta in (dst_dir, txt_dir):
            for item in Path(pasta).iterdir():
                if item.is_file():
                    item.unlink()

    arquivos = selected_files or listar_pdfs_disponiveis(src_dir)
    if not arquivos:
        raise ValueError("Nenhum PDF disponível para processamento.")

    poppler_disponivel = os.path.exists(PATH_POPPLER_EXE)
    if not poppler_disponivel and log_callback:
        log_callback(f"Aviso: pdftotext não encontrado em {PATH_POPPLER_EXE}. A conversão para txt será ignorada.")

    resultados = []
    for idx, file_name in enumerate(arquivos, start=1):
        input_file = src_dir / file_name
        output_file = os.path.join(dst_dir, f"{os.path.splitext(file_name)[0]}_Cropped.pdf")

        if log_callback:
            log_callback(f"Processando {file_name} com template {selected_template_name}...")

        cropped_pdf_path = output_file
        if selected_template_name == "ENEL":
            cropped_pdf_path = cropper_logic_enel(str(input_file), output_file, selected_template)
        elif selected_template_name == "ENERGISA":
            cropped_pdf_path = cropper_logic_energisa(str(input_file), output_file, selected_template)
        elif selected_template_name == "NEOENERGIA":
            cropped_pdf_path = cropper_logic_neoenergiaPE(
                str(input_file),
                output_file,
                selected_template,
                output_poppler_dir=txt_dir,
            )

        txt_path = ""
        if gerar_txt and poppler_disponivel and cropped_pdf_path and os.path.exists(cropped_pdf_path):
            txt_name = normalizar_nome_por_tag(os.path.basename(cropped_pdf_path), "Poppler", ".txt")
            txt_path = os.path.join(txt_dir, txt_name)
            if log_callback:
                log_callback(f"Convertendo para txt: {os.path.basename(cropped_pdf_path)} -> {txt_name}")
            run_pdftotext(cropped_pdf_path, txt_path)

        resultados.append(
            {
                "arquivo": file_name,
                "cropped_pdf": cropped_pdf_path,
                "txt": txt_path,
                "sucesso": bool(cropped_pdf_path and os.path.exists(cropped_pdf_path)),
            }
        )

        if progress_callback:
            progress_callback(idx, len(arquivos), file_name)

    return {
        "origem": src_dir,
        "cropped_dir": dst_dir,
        "poppler_dir": txt_dir,
        "resultados": resultados,
        "processados": len(resultados),
        "sucesso": sum(1 for item in resultados if item["sucesso"]),
        "falhas": sum(1 for item in resultados if not item["sucesso"]),
    }

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
            cropped_pdf_path = cropper_logic_neoenergiaPE(
                input_file,
                output_file,
                selected_template,
                output_poppler_dir=txt_dir,
            )

        if poppler_disponivel and cropped_pdf_path and os.path.exists(cropped_pdf_path):
            txt_name = normalizar_nome_por_tag(os.path.basename(cropped_pdf_path), "Poppler", ".txt")
            output_txt = os.path.join(txt_dir, txt_name)
            print(f"Convertendo para txt: {os.path.basename(cropped_pdf_path)} -> {txt_name}")
            run_pdftotext(cropped_pdf_path, output_txt)
        elif poppler_disponivel:
            
            (f"Aviso: PDF cropado não encontrado para conversão: {cropped_pdf_path}")

if __name__ == "__main__":
    integralaiser_orchestrator()
