"""Ponto de entrada da automação de arquivamento de teses."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from config import FILE_DIALOG_FILTERS, FILE_DIALOG_TITLE
from organizer import ThesisOrganizer
from utils import OrganizationError


def select_pdf_file(root: tk.Tk) -> Path | None:
    """Abre diálogo de seleção e retorna o PDF escolhido.

    Args:
        root: Janela raiz do tkinter, usada como parent dos diálogos.

    Returns:
        Caminho do PDF selecionado, ou None quando o usuário cancelar.
    """
    selected = filedialog.askopenfilename(
        title=FILE_DIALOG_TITLE,
        filetypes=FILE_DIALOG_FILTERS,
        parent=root,
    )
    if not selected:
        return None

    return Path(selected)


def run() -> None:
    """Executa o fluxo completo da automação com interação mínima."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        pdf_path = select_pdf_file(root)
        if pdf_path is None:
            messagebox.showinfo(
                "Operação cancelada",
                "Nenhum arquivo foi selecionado.",
                parent=root,
            )
            return

        organizer = ThesisOrganizer.from_default_config()
        destination = organizer.organize(pdf_path)
        messagebox.showinfo(
            "Sucesso",
            "Arquivamento concluído com sucesso.\n"
            f"Arquivo movido para:\n{destination}",
            parent=root,
        )
    except OrganizationError as exc:
        messagebox.showerror("Falha na automação", str(exc), parent=root)
    except Exception as exc:  # noqa: BLE001
        # Mensagem final amigável para erros inesperados.
        messagebox.showerror(
            "Erro inesperado",
            f"Ocorreu um erro não previsto: {exc}",
            parent=root,
        )
    finally:
        root.destroy()


if __name__ == "__main__":
    run()
