import os
import shutil
import sys


def _get_base_dir() -> str:
    # Quando empacotado em .exe (PyInstaller), __file__ aponta para pasta temporária.
    # Nesse caso, usamos a pasta onde o executável está.
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def desfolhar_pasta(caminho_principal, arquivo_em_execucao=None):
    arquivo_exec_norm = (
        os.path.normcase(os.path.abspath(arquivo_em_execucao))
        if arquivo_em_execucao
        else None
    )

    for raiz, dirs, arquivos in os.walk(caminho_principal, topdown=False):
        for arquivo in arquivos:
            caminho_origem = os.path.join(raiz, arquivo)
            caminho_destino = os.path.join(caminho_principal, arquivo)

            origem_norm = os.path.normcase(os.path.abspath(caminho_origem))
            destino_norm = os.path.normcase(os.path.abspath(caminho_destino))

            # Não tenta mover o próprio script/executável em execução.
            if arquivo_exec_norm and origem_norm == arquivo_exec_norm:
                continue

            # Se o arquivo já está na pasta principal, não há o que mover.
            if origem_norm == destino_norm:
                continue

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
    pasta = _get_base_dir()
    arquivo_em_execucao = sys.executable if getattr(sys, "frozen", False) else __file__
    desfolhar_pasta(pasta, arquivo_em_execucao=arquivo_em_execucao)
    print("Processo concluído!")