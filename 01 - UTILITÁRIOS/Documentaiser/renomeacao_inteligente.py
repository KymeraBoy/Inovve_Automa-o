"""Renomeação inteligente (contratos).

Este módulo extrai os métodos do antigo Documentaiser.py para um mixin.
Ele assume que a classe que o herda implementa/possui os atributos de UI:

- ri_dir, ri_pdf_files, ri_idx
- ri_selected_t1, ri_selected_ras_or_pub_kind, ri_selected_adt_number
- ri_current_municipio
- ri_undo_stack, ri_used_names_in_session, ri_last_confirmed_token
- ri_listbox, ri_t2_container, ri_lbl_adt_suggestion
- ri_btn_prev, ri_btn_next, ri_btn_skip, ri_btn_undo, ri_btn_confirm
- ri_btn_ctr, ri_btn_adt, ri_btn_ras, ri_btn_pub, ri_btn_proc, ri_btn_kit
- ri_lbl_original, ri_lbl_new

A lógica usa normalize_string_for_filename do ../utils.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import re

import tkinter as tk
from tkinter import filedialog, messagebox

# utils.py fica em ../utils.py
import sys
UTILS_DIR = Path(__file__).resolve().parent.parent
if str(UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(UTILS_DIR))

from utils import normalize_string_for_filename


class RenomeacaoInteligenteMixin:
    # -------------------- Renomeação Inteligente --------------------
    def ri_choose_dir(self) -> None:
        directory = filedialog.askdirectory()
        if not directory:
            return

        self.ri_dir = Path(directory)
        self.ri_used_names_in_session.clear()
        self.ri_undo_stack.clear()
        self.ri_selected_t1 = None
        self.ri_selected_ras_or_pub_kind = None
        self.ri_selected_adt_number = None
        self.ri_current_municipio = None
        self.ri_last_confirmed_token = None

        # Apenas nível da pasta (como definido)
        self.ri_pdf_files = sorted(self.ri_dir.glob("*.pdf"), key=lambda p: p.name.lower())

        self.ri_listbox.delete(0, tk.END)
        for p in self.ri_pdf_files:
            self.ri_listbox.insert(tk.END, p.name)

        if not self.ri_pdf_files:
            messagebox.showwarning("Aviso", "Nenhum PDF encontrado na pasta selecionada (nível da pasta).")
            self.ri_idx = -1
            self.ri_state_refresh()
            self._ri_clear_name_panel()
            self.ri_clear_t2()
            return

        self.ri_idx = 0
        self.ri_listbox.select_set(0)
        self.ri_listbox.see(0)
        self.ri_load_current_pdf()
        self.ri_state_refresh()

    def ri_on_select_from_list(self, _evt=None) -> None:
        if self.ri_dir is None:
            return

        sel = self.ri_listbox.curselection()
        if not sel:
            return
        i = int(sel[0])
        if i < 0 or i >= len(self.ri_pdf_files):
            return

        self.ri_idx = i
        self.ri_reset_classification_for_new_pdf()
        self.ri_load_current_pdf()

    def ri_reset_classification_for_new_pdf(self) -> None:
        self.ri_selected_t1 = None
        self.ri_selected_ras_or_pub_kind = None
        self.ri_selected_adt_number = None
        # compat não usado, mas mantido pra não quebrar referências antigas
        self.ri_selected_t2 = None
        self.ri_current_municipio = None
        self.ri_lbl_adt_suggestion.config(text="")
        self.ri_clear_t2()
        self._ri_update_new_name_preview()

    def ri_load_current_pdf(self) -> None:
        if self.ri_idx < 0 or self.ri_idx >= len(self.ri_pdf_files):
            return

        pdf_path = self.ri_pdf_files[self.ri_idx]
        self.ri_lbl_original.config(text=f"Nome Original: {pdf_path.name}")

        municipio = self.ri_get_municipio_for_file(pdf_path)
        self.ri_current_municipio = municipio

        self._ri_update_new_name_preview()

    def ri_get_municipio_for_file(self, pdf_path: Path) -> str:
        """Regra: MUNICÍPIO = nome da pasta avô do PDF."""
        parent = pdf_path.parent
        grand_parent = parent.parent.parent
        return grand_parent.name if grand_parent != parent else parent.name

    def ri_clear_t2(self) -> None:
        for w in self.ri_t2_container.winfo_children():
            w.destroy()

    def ri_state_refresh(self) -> None:
        enabled = self.ri_dir is not None and self.ri_idx >= 0 and self.ri_idx < len(self.ri_pdf_files)
        state = tk.NORMAL if enabled else tk.DISABLED

        for b in [
            self.ri_btn_prev,
            self.ri_btn_next,
            self.ri_btn_skip,
            self.ri_btn_undo,
            self.ri_btn_confirm,
            self.ri_btn_ctr,
            self.ri_btn_adt,
            self.ri_btn_ras,
            self.ri_btn_pub,
            self.ri_btn_proc,
            self.ri_btn_kit,
        ]:
            try:
                b.config(state=state)
            except Exception:
                pass

    def ri_prev(self) -> None:
        if self.ri_idx <= 0:
            return
        self.ri_idx -= 1
        self.ri_listbox.select_clear(0, tk.END)
        self.ri_listbox.select_set(self.ri_idx)
        self.ri_listbox.see(self.ri_idx)
        self.ri_reset_classification_for_new_pdf()
        self.ri_load_current_pdf()
        self.ri_state_refresh()

    def ri_next(self) -> None:
        if self.ri_dir is None:
            return
        if self.ri_idx < 0:
            return
        if self.ri_idx >= len(self.ri_pdf_files) - 1:
            return

        self.ri_idx += 1
        self.ri_listbox.select_clear(0, tk.END)
        self.ri_listbox.select_set(self.ri_idx)
        self.ri_listbox.see(self.ri_idx)
        self.ri_reset_classification_for_new_pdf()
        self.ri_load_current_pdf()
        self.ri_state_refresh()

    def ri_skip(self) -> None:
        self.ri_next()

    def ri_undo(self) -> None:
        if not self.ri_undo_stack:
            messagebox.showinfo("Info", "Nada para desfazer.")
            return

        old_path, new_path = self.ri_undo_stack.pop()

        try:
            if new_path.exists():
                new_path.replace(old_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao desfazer: {e}")
            return

        self.ri_used_names_in_session.discard(new_path.name)
        if getattr(self, "ri_confirmed_history", None):
            self.ri_confirmed_history.pop()

        self._ri_update_new_name_preview()

    def ri_choose_t1(self, t1: str) -> None:
        if self.ri_current_municipio is None:
            return

        self.ri_selected_t1 = t1
        self.ri_selected_ras_or_pub_kind = None
        self.ri_selected_adt_number = None
        self.ri_lbl_adt_suggestion.config(text="")

        self.ri_clear_t2()

        if t1 == "RAS":
            self._ri_build_t2_buttons_ras()
        elif t1 == "PUB":
            self._ri_build_t2_buttons_pub()
        elif t1 == "ADT":
            self.ri_selected_adt_number = self.ri_suggest_next_adt_number()
            if self.ri_selected_adt_number is not None:
                self.ri_lbl_adt_suggestion.config(
                    text=f"Sugestão ADT: {self.ri_selected_adt_number:02d} (clique em Confirmar)"
                )

        self._ri_update_new_name_preview()

    def _ri_build_t2_buttons_ras(self) -> None:
        kind_frame = self.ri_t2_container
        tk.Label(kind_frame, text="Selecione o tipo dentro de RAS:").pack(anchor="w")

        btn_ctr = tk.Button(
            kind_frame, text="RAS - CTR", width=18, command=lambda: self.ri_choose_ras_kind("RAS_CTR")
        )
        btn_adt = tk.Button(
            kind_frame, text="RAS - ADT", width=18, command=lambda: self.ri_choose_ras_kind("RAS_ADT")
        )
        btn_proc = tk.Button(
            kind_frame, text="RAS - PROC", width=18, command=lambda: self.ri_choose_ras_kind("RAS_PROC")
        )

        btn_ctr.pack(side=tk.LEFT, padx=6, pady=6)
        btn_adt.pack(side=tk.LEFT, padx=6, pady=6)
        btn_proc.pack(side=tk.LEFT, padx=6, pady=6)

    def _ri_build_t2_buttons_pub(self) -> None:
        kind_frame = self.ri_t2_container
        tk.Label(kind_frame, text="Selecione o tipo dentro de PUB:").pack(anchor="w")

        btn_ctr = tk.Button(
            kind_frame, text="PUB - CTR", width=18, command=lambda: self.ri_choose_pub_kind("PUB_CTR")
        )
        btn_adt = tk.Button(
            kind_frame, text="PUB - ADT", width=18, command=lambda: self.ri_choose_pub_kind("PUB_ADT")
        )

        btn_ctr.pack(side=tk.LEFT, padx=6, pady=6)
        btn_adt.pack(side=tk.LEFT, padx=6, pady=6)

    def ri_choose_ras_kind(self, kind: str) -> None:
        self.ri_selected_ras_or_pub_kind = kind
        self.ri_selected_adt_number = None
        self.ri_lbl_adt_suggestion.config(text="")

        if kind == "RAS_ADT":
            self.ri_selected_adt_number = self.ri_suggest_next_adt_number(ras_or_pub_prefix="RAS_ADT")
            if self.ri_selected_adt_number is not None:
                self.ri_lbl_adt_suggestion.config(
                    text=f"Sugestão RAS_ADT: {self.ri_selected_adt_number:02d} (clique em Confirmar)"
                )

        self._ri_update_new_name_preview()

    def ri_choose_pub_kind(self, kind: str) -> None:
        self.ri_selected_ras_or_pub_kind = kind
        self.ri_selected_adt_number = None
        self.ri_lbl_adt_suggestion.config(text="")

        if kind == "PUB_ADT":
            self.ri_selected_adt_number = self.ri_suggest_next_adt_number(ras_or_pub_prefix="PUB_ADT")
            if self.ri_selected_adt_number is not None:
                self.ri_lbl_adt_suggestion.config(
                    text=f"Sugestão PUB_ADT: {self.ri_selected_adt_number:02d} (clique em Confirmar)"
                )

        self._ri_update_new_name_preview()

    def ri_suggest_next_adt_number(self, ras_or_pub_prefix: Optional[str] = None) -> Optional[int]:
        if self.ri_dir is None or self.ri_current_municipio is None:
            return None

        municipio = normalize_string_for_filename(self.ri_current_municipio)

        if ras_or_pub_prefix == "RAS_ADT":
            pattern = re.compile(rf"^{re.escape(municipio)}_RAS_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)
        elif ras_or_pub_prefix == "PUB_ADT":
            pattern = re.compile(rf"^{re.escape(municipio)}_PUB_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)
        else:
            pattern = re.compile(rf"^{re.escape(municipio)}_ADT_(\d{{2}})\.pdf$", re.IGNORECASE)

        max_num = 0
        for p in self.ri_dir.glob("*.pdf"):
            m = pattern.match(p.name)
            if m:
                try:
                    n = int(m.group(1))
                    max_num = max(max_num, n)
                except Exception:
                    pass

        return max_num + 1

    def _ri_update_new_name_preview(self) -> None:
        if self.ri_idx < 0 or self.ri_idx >= len(self.ri_pdf_files):
            self.ri_lbl_new.config(text="Novo Nome: -")
            return

        pdf_path = self.ri_pdf_files[self.ri_idx]
        new_name = self._ri_build_new_name(pdf_path)
        if new_name is None:
            self.ri_lbl_new.config(text="Novo Nome: -")
        else:
            self.ri_lbl_new.config(text=f"Novo Nome: {new_name}")

    def _ri_build_new_name(self, pdf_path: Path) -> Optional[str]:
        if self.ri_current_municipio is None or self.ri_selected_t1 is None:
            return None

        municipio = normalize_string_for_filename(self.ri_current_municipio)
        t1 = self.ri_selected_t1

        if t1 == "CTR":
            return f"{municipio}_CTR.pdf"
        if t1 == "PROC":
            return f"{municipio}_PROC.pdf"
        if t1 == "KIT":
            return f"{municipio}_KIT.pdf"

        if t1 == "ADT":
            if self.ri_selected_adt_number is None:
                return None
            return f"{municipio}_ADT_{self.ri_selected_adt_number:02d}.pdf"

        if t1 == "RAS":
            if self.ri_selected_ras_or_pub_kind == "RAS_CTR":
                return f"{municipio}_RAS_CTR.pdf"
            if self.ri_selected_ras_or_pub_kind == "RAS_PROC":
                return f"{municipio}_RAS_PROC.pdf"
            if self.ri_selected_ras_or_pub_kind == "RAS_ADT":
                if self.ri_selected_adt_number is None:
                    return None
                return f"{municipio}_RAS_ADT_{self.ri_selected_adt_number:02d}.pdf"

        if t1 == "PUB":
            if self.ri_selected_ras_or_pub_kind == "PUB_CTR":
                return f"{municipio}_PUB_CTR.pdf"
            if self.ri_selected_ras_or_pub_kind == "PUB_ADT":
                if self.ri_selected_adt_number is None:
                    return None
                return f"{municipio}_PUB_ADT_{self.ri_selected_adt_number:02d}.pdf"

        return None

    def _ri_clear_name_panel(self) -> None:
        self.ri_lbl_original.config(text="Nome Original: -")
        self.ri_lbl_new.config(text="Novo Nome: -")

    def ri_confirm(self) -> None:
        if self.ri_idx < 0 or self.ri_idx >= len(self.ri_pdf_files):
            return

        pdf_path = self.ri_pdf_files[self.ri_idx]
        new_name = self._ri_build_new_name(pdf_path)
        if new_name is None:
            messagebox.showwarning("Aviso", "Selecione as opções para gerar o novo nome.")
            return

        target_path = pdf_path.with_name(new_name)

        if target_path.exists():
            messagebox.showwarning("Aviso", f"Já existe um arquivo com esse nome: {new_name}")
            return

        if new_name in self.ri_used_names_in_session:
            messagebox.showwarning("Aviso", f"Nome já usado nesta sessão: {new_name}")
            return

        old_path = pdf_path
        try:
            old_path.replace(target_path)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao renomear: {e}")
            return

        self.ri_used_names_in_session.add(new_name)
        self.ri_undo_stack.append((old_path, target_path))

        self.ri_pdf_files[self.ri_idx] = target_path
        self.ri_lbl_original.config(text=f"Nome Original: {target_path.name}")
        self._ri_update_new_name_preview()

        try:
            self.ri_listbox.delete(self.ri_idx)
            self.ri_listbox.insert(self.ri_idx, target_path.name)
            self.ri_listbox.select_set(self.ri_idx)
            self.ri_listbox.see(self.ri_idx)
        except Exception:
            pass

        self.ri_last_confirmed_token = new_name.replace(".pdf", "")
        self.ri_next()

