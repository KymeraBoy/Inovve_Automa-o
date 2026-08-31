from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from interface.janela_principal import JanelaPrincipal

def main() -> int:

    app    = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
