import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import traceback
os.environ["PATH"] = (
    r"C:\Tesseract-OCR;"
    + os.environ["PATH"]
)

os.environ["TESSDATA_PREFIX"] = (
    r"C:\Tesseract-OCR\tessdata"
)

import ocrmypdf


# Ajuste para o local correto do Tesseract
os.environ["PATH"] += os.pathsep + r"C:\Tesseract-OCR"
os.environ["TESSDATA_PREFIX"] = r"C:\Tesseract-OCR\tessdata"


def log(texto):
    caixa_log.insert(
        tk.END,
        texto + "\n"
    )
    caixa_log.see(tk.END)
    janela.update()


def selecionar_pdf():

    arquivo = filedialog.askopenfilename(
        title="Selecione um PDF",
        filetypes=[
            ("Arquivos PDF", "*.pdf")
        ]
    )

    if arquivo:

        log("-----------------------------")
        log("PDF selecionado:")
        log(arquivo)

        thread = threading.Thread(
            target=executar_ocr,
            args=(arquivo,)
        )

        thread.start()


def executar_ocr(arquivo):

    try:

        log("Iniciando processo OCR...")
        
        # Verifica arquivo
        if not os.path.exists(arquivo):
            log("ERRO: arquivo não encontrado")
            return

        log("Arquivo encontrado OK")

        pasta = os.path.dirname(arquivo)

        nome = os.path.splitext(
            os.path.basename(arquivo)
        )[0]

        saida = os.path.join(
            pasta,
            nome + "_ocr.pdf"
        )


        log("Arquivo de saída:")
        log(saida)


        log("Chamando OCRmyPDF...")
        log("Idioma: português")
        log("Correção de inclinação ativada")


        ocrmypdf.ocr(
            arquivo,
            saida,
            language=["por"],
            deskew=True,
            rotate_pages=True
        )


        log("OCR FINALIZADO COM SUCESSO")

        messagebox.showinfo(
            "Concluído",
            "PDF pesquisável criado com sucesso!"
        )


    except Exception as erro:

        log("")
        log("========== ERRO ==========")
        log(str(erro))
        log("")
        log("Detalhes técnicos:")
        log(traceback.format_exc())


        messagebox.showerror(
            "Erro no OCR",
            str(erro)
        )



# -------------------------
# Interface
# -------------------------

janela = tk.Tk()

janela.title(
    "OCR PDF - Diagnóstico"
)

janela.geometry(
    "700x500"
)


botao = tk.Button(
    janela,
    text="Selecionar PDF",
    font=("Arial", 12),
    width=20,
    height=2,
    command=selecionar_pdf
)

botao.pack(
    pady=10
)


caixa_log = scrolledtext.ScrolledText(
    janela,
    width=80,
    height=25
)

caixa_log.pack(
    padx=10,
    pady=10
)


log("Programa iniciado.")
log("Aguardando seleção do PDF...")


janela.mainloop()