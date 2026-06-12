import os
import shutil

def organizar_reclamacoes():
    """
    Organiza arquivos PDF de reclamações em uma estrutura de pastas padronizada.
    """
    # Define a pasta de trabalho como o diretório onde o script está localizado
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Subpastas que devem ser criadas dentro de cada reclamação
    subpastas_objetivo = [
        "RECLAMACAO_FORMAL",
        "ANEEL",
        "PAGAMENTO",
        "DOCUMENTOS_RECEBIDOS",
        "E-MAILS"
    ]

    print(f"Trabalhando no diretório: {diretorio_atual}")
    print("-" * 50)

    # Listar todos os arquivos na pasta
    arquivos = os.listdir(diretorio_atual)
    contador = 0

    for arquivo in arquivos:
        # Verifica se o arquivo é um PDF e termina com o sufixo esperado (case-insensitive)
        if arquivo.upper().endswith("-ASSINADO.PDF"):
            # 1. Determina o nome base (ID da Reclamação)
            # Encontra a posição do sufixo para removê-lo preservando o nome original
            posicao_sufixo = arquivo.upper().rfind("-ASSINADO.PDF")
            nome_reclamacao = arquivo[:posicao_sufixo]
            
            if not nome_reclamacao:
                continue

            # 2. Define o caminho da pasta principal da reclamação
            caminho_base_reclamacao = os.path.join(diretorio_atual, nome_reclamacao)

            # 3. Cria a estrutura de pastas (não gera erro se já existir)
            for sub in subpastas_objetivo:
                caminho_subpasta = os.path.join(caminho_base_reclamacao, sub)
                if not os.path.exists(caminho_subpasta):
                    os.makedirs(caminho_subpasta)

            # 4. Define origem e destino (Movendo para RECLAMACAO_FORMAL)
            caminho_origem = os.path.join(diretorio_atual, arquivo)
            caminho_destino = os.path.join(caminho_base_reclamacao, "RECLAMACAO_FORMAL", arquivo)

            try:
                shutil.move(caminho_origem, caminho_destino)
                print(f"[OK] Organizado: {arquivo} -> {nome_reclamacao}/")
                contador += 1
            except Exception as e:
                print(f"[ERRO] Falha ao mover {arquivo}: {e}")

    print("-" * 50)
    print(f"Processo concluído! {contador} reclamação(ões) organizada(s).")

if __name__ == "__main__":
    organizar_reclamacoes()
    input("\nPressione Enter para sair...")
