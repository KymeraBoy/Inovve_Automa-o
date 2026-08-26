# Permite usar recursos de anotação de tipos de versões
# mais recentes do Python sem problemas de compatibilidade.
from __future__ import annotations

# Importa o módulo sys, usado principalmente para acessar os argumentos passados ao programa pelo sistema operacional.
import sys

# Importa QApplication, que é responsável por criar e gerenciar a aplicação gráfica do PySide6.
from PySide6.QtWidgets import QApplication

# Importa a classe JanelaPrincipal, que representa a janela principal da aplicação.
from interface.janela_principal import JanelaPrincipal


# Define a função principal da aplicação.
# -> int indica que a função retorna um número inteiro.
def main() -> int:
    # Cria a aplicação Qt.
    # sys.argv contém os argumentos passados ao programa
    # quando ele é executado pelo terminal/sistema.
    app = QApplication(sys.argv)

    # Cria uma instância da janela principal.
    # Aqui, o código da classe JanelaPrincipal será executado
    # para construir e configurar a interface.
    janela = JanelaPrincipal()

    # Torna a janela principal visível na tela.
    janela.show()

    # Inicia o loop de eventos do Qt.
    # Esse loop mantém a aplicação funcionando e permite
    # responder a cliques, teclas, eventos da janela etc.
    # O valor retornado pelo app.exec() é o código de saída
    # da aplicação.
    return app.exec()


# Verifica se este arquivo está sendo executado diretamente.
# Se ele estiver sendo importado por outro arquivo, este bloco
# não será executado.
if __name__ == "__main__":
    # Executa a função main() e encerra o programa usando
    # o código inteiro retornado por ela.
    raise SystemExit(main())
