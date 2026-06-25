import os
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

def comprimir_pdf(caminho_pdf: Path, caminho_gs: str, nivel_compression: str = "screen") -> bool:
    """ Comprime um único arquivo PDF e o substitui se for menor. """
    tmp_out = caminho_pdf.with_suffix(".compressed.pdf")
    
    try:
        cmd = [
            caminho_gs,
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{nivel_compression}",
            "-dColorImageDownsampleType=/Average",
            "-dColorImageResolution=72",
            "-dGrayImageDownsampleType=/Average",
            "-dGrayImageResolution=72",
            "-dMonoImageDownsampleType=/Average",
            "-dMonoImageResolution=72",
            "-dNOPAUSE",
            "-dBATCH",
            f"-sOutputFile={os.fspath(tmp_out)}",
            os.fspath(caminho_pdf)
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if tmp_out.exists() and tmp_out.stat().st_size > 0:
            tam_original = caminho_pdf.stat().st_size
            tam_comprimido = tmp_out.stat().st_size
            
            if tam_comprimido < tam_original:
                caminho_pdf.unlink()
                tmp_out.rename(caminho_pdf)
                return True
            else:
                tmp_out.unlink()
                return False
    except Exception as e:
        print(f"Erro ao processar {caminho_pdf.name}: {e}")
        if tmp_out.exists():
            tmp_out.unlink()
    return False

def processar_pastas_continuamente():
    # =========================================================================
    # AJUSTE AQUI O CAMINHO DO SEU GHOSTSCRIPT SE FOR DIFERENTE
    # =========================================================================
    caminho_ghostscript = r"C:\Program Files\gs\gs10.07.1\bin\gswin64c.exe"
    
    if not Path(caminho_ghostscript).exists():
        # Inicializa uma janela oculta apenas para mostrar o messagebox de erro
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro", f"Não foi possível encontrar o Ghostscript em:\n{caminho_ghostscript}\n\nPor favor, verifique a pasta da instalação.")
        return

    # Inicializa o ambiente do tkinter de forma oculta
    root = tk.Tk()
    root.withdraw()

    while True:
        # Abre a janela para o usuário selecionar a pasta
        pasta_selecionada = filedialog.askdirectory(title="Selecione a pasta com os PDFs para comprimir")
        
        # Se o usuário cancelar a seleção da pasta, sai do loop e fecha o programa
        if not pasta_selecionada:
            print("Seleção de pasta cancelada. Encerrando o programa.")
            break

        pasta_path = Path(pasta_selecionada)
        # Busca arquivos .pdf
        arquivos_pdf = [f for f in pasta_path.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]

        if not arquivos_pdf:
            print(f"\nNenhum arquivo PDF encontrado na pasta:\n{pasta_selecionada}")
            resposta = messagebox.askyesno("Sem PDFs", f"Nenhum arquivo PDF encontrado na pasta:\n{pasta_selecionada}\n\nDeseja selecionar outra pasta?")
            if not resposta:
                break
            continue

        print(f"\n=======================================================================")
        print(f"Iniciando a compressão de {len(arquivos_pdf)} arquivos na pasta: {pasta_selecionada}")
        print(f"=======================================================================\n")
        
        cont_sucesso = 0
        
        for idx, pdf in enumerate(arquivos_pdf, start=1):
            print(f"[{idx}/{len(arquivos_pdf)}] Processando: {pdf.name}...")
            
            tamanho_antigo = pdf.stat().st_size
            
            if comprimir_pdf(pdf, caminho_ghostscript, nivel_compression="screen"):
                tamanho_novo = pdf.stat().st_size
                reducao = ((tamanho_antigo - tamanho_novo) / tamanho_antigo) * 100
                print(f" -> Sucesso! Reduzido em {reducao:.1f}% ({tamanho_antigo/1024/1024:.2f}MB -> {tamanho_novo/1024/1024:.2f}MB)")
                cont_sucesso += 1
            else:
                print(" -> Pulado (já estava otimizado ou não pôde ser reduzido ainda mais).")

        msg_final = f"Pasta concluída!\n\nPDFs reduzidos com sucesso nesta pasta: {cont_sucesso} de {len(arquivos_pdf)}."
        print(f"\n{msg_final}\n")
        
        # Pergunta ao usuário se ele quer continuar para a próxima pasta
        deseja_continuar = messagebox.askyesno("Concluído", f"{msg_final}\n\nDeseja selecionar a próxima pasta?")
        
        if not deseja_continuar:
            print("Encerrando o programa a pedido do usuário.")
            break

    messagebox.showinfo("Encerrado", "Programa finalizado com sucesso!")

if __name__ == "__main__":
    processar_pastas_continuamente()