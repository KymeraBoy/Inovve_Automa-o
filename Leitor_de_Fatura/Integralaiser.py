# ============================================================== #
# LAUNCHER DO INTEGRALAISER
# ============================================================== #

# Importa as bibliotecas
import sys
from pathlib import Path

# garante que ele funcione na pasta onde ele estiver
if getattr(sys, "frozen", False):
    DIRETORIO_BASE = Path(sys.executable).resolve().parent
else:
    DIRETORIO_BASE = Path(__file__).resolve().parent
SCRIPTS_DIR = DIRETORIO_BASE / "Scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from Scripts.integralaiser_gui import run_app

# ============================================================== #
# FUNÇÕES
# ============================================================== #

def integralaiser_main():
    run_app()


if __name__ == "__main__":
    integralaiser_main()
