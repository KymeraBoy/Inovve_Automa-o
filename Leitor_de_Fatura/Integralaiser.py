# ============================================================== #
# LAUNCHER DO INTEGRALAISER
# ============================================================== #

import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    DIRETORIO_BASE = Path(sys.executable).resolve().parent
else:
    DIRETORIO_BASE = Path(__file__).resolve().parent

SCRIPTS_DIR = DIRETORIO_BASE / "Scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from Scripts import Cropper
from Scripts import Texter


# ============================================================== #
# FUNÇÕES
# ============================================================== #

def integralaiser_main():
    while True:
        print("\n" + "=" * 40)
        print("      SISTEMA INTEGRALAISER v1.3")
        print("=" * 40)
        print("1. [CROPPER]     - Recortar PDFs Originais")
        print("2. [TEXTER]      - Formatar Dados Extraídos")
        print("0. Sair")
        print("-" * 40)

        opcao = input("Escolha a etapa para execução: ")

        if opcao == "1":
            print("\n>>> INICIANDO CROPPER (RECORTE)...")
            try:
                Cropper.integralaiser_orchestrator()
                print("\n[SUCESSO] PDFs recortados e salvos em Faturas_Cropped.")
            except Exception as e:
                print(f"\n[ERRO NO CROPPER]: {e}")

        elif opcao == "2":
            print("\n>>> INICIANDO TEXTER (FORMATAÇÃO)...")
            try:
                Texter.texter_orchestrator()
                print("\n[SUCESSO] Dados formatados e salvos em Faturas_Texter.")
            except Exception as e:
                print(f"\n[ERRO NO TEXTER]: {e}")

        elif opcao == "0":
            print("Encerrando Integralaiser. Até logo!")
            break
        else:
            print("Opção inválida. Selecione 1, 2 ou 0.")


if __name__ == "__main__":
    integralaiser_main()
