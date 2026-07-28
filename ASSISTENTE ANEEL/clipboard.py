"""
Módulo da Área de Transferência.
Interface simplificada para manipular o Clipboard.
"""

import tkinter as tk


class ClipboardManager:
    """Gerenciador de operações com o Clipboard utilizando o motor do Tkinter."""

    def __init__(self, root_tk: tk.Tk):
        self._root = root_tk

    def copy_to_clipboard(self, text: str) -> None:
        """Copia a string informada diretamente para o Clipboard sem criar janelas."""
        self._root.clipboard_clear()
        self._root.clipboard_append(text)
        self._root.update()  # Garante retenção do conteúdo na memória do SO