# ============================================================== #
# BIBLIOTECAS
# ============================================================== #

# Código para criação do executável
# python -m PyInstaller --onefile --windowed integralaiser.py

import os
import Cropper
import Texter

# ============================================================== #
# CONFIGURAÇÕES
# ============================================================== #

# ============================================================== #
# FUNÇÕES
# ============================================================== #

def integralaiser_main():
    while True:
        print("\n" + "="*40)
        print("      SISTEMA INTEGRALAISER v1.3")
        print("="*40)
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

# ============================================================== #
# EXECUÇÃO
# ============================================================== #

if __name__ == "__main__":
    integralaiser_main()