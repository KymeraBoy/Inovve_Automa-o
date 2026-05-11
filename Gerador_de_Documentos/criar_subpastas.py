import os
import sys

SUBPASTAS = ["DOCUMENTOS_RECEBIDOS", "E-MAILS", "PETICAO_FORMAL"]

def criar_subpastas(pasta_raiz):
    if not os.path.isdir(pasta_raiz):
        print(f"Erro: '{pasta_raiz}' não é uma pasta válida.")
        sys.exit(1)

    for entrada in os.scandir(pasta_raiz):
        if entrada.is_dir():
            for subpasta in SUBPASTAS:
                caminho = os.path.join(entrada.path, subpasta)
                os.makedirs(caminho, exist_ok=True)
                print(f"Criado: {caminho}")

if __name__ == "__main__":
    pasta = input("Digite o endereço da pasta: ").strip()
    criar_subpastas(pasta)
