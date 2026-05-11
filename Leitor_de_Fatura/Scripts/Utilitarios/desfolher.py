import os
import shutil

def desfolhar_pasta(caminho_principal):
    for raiz, dirs, arquivos in os.walk(caminho_principal, topdown=False):
        for arquivo in arquivos:
            caminho_origem = os.path.join(raiz, arquivo)
            caminho_destino = os.path.join(caminho_principal, arquivo)

            # Evita sobrescrever arquivos com mesmo nome
            if os.path.exists(caminho_destino):
                nome, ext = os.path.splitext(arquivo)
                contador = 1
                while True:
                    novo_nome = f"{nome}_{contador}{ext}"
                    caminho_destino = os.path.join(caminho_principal, novo_nome)
                    if not os.path.exists(caminho_destino):
                        break
                    contador += 1

            shutil.move(caminho_origem, caminho_destino)

        # Remove diretórios vazios (menos a principal)
        if raiz != caminho_principal:
            try:
                os.rmdir(raiz)
            except OSError:
                pass

if __name__ == "__main__":
    pasta = r"C:\Users\Usuário 1\Documents\Inovve_Automação\Leitor_de_Fatura\Faturas\LUCENA"
    desfolhar_pasta(pasta)
    print("Processo concluído!")