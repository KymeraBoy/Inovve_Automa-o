"""
Módulo da Interface Gráfica (GUI).
Construído com CustomTkinter para um visual moderno e limpo.
"""

from pathlib import Path
from typing import Dict, Optional
import tkinter as tk
import customtkinter as ctk

from clipboard import ClipboardManager
from config import APP_GEOMETRY, APP_TITLE, COLOR_THEME, MUNICIPIOS_DIR, THEME_MODE
from models import ClienteMunicipio
from parser_tex import TexParser


class AppGUI(ctk.CTk):
    """Janela Principal da Aplicação."""

    def __init__(self):
        super().__init__()

        # Configurações iniciais de estilo
        ctk.set_appearance_mode(THEME_MODE)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.resizable(False, False)

        # Serviços e Dados
        self.clipboard_mgr = ClipboardManager(self)
        self.municipios_dados: Dict[str, ClienteMunicipio] = {}
        self.cliente_atual: Optional[ClienteMunicipio] = None
        self.tipos_documento_tese = ["RECLAMAÇÃO", "OFÍCIO", "REQUERIMENTO"]
        self.anos_tese = ["2024", "2025", "2026"]
        self.objetivos_modelos = {
            "Contestação de Indeferimento": "Contestar o indeferimento da reclamação",
            "Contestação de Memorial de Cálculo": "Contestar o memorial de cálculo",
            "Contestação do Deferimento Parcial": "Contestar o deferimento parcial da reclamação",

        }
        self.modelos_config = {
            "Modelo de ouvidoria": """Prezado ouvidor,

Esta reclamação é direcionada à <<CONCESSIONÁRIA>>.

Referente a <<TESE>> de <<MUNICÍPIO>>. O pedido visa <<OBJETIVO>>.

A descrição detalhada consta no <<OFÍCIO>>, enviado em anexo."""
        }
        self.opcoes_modelos = list(self.objetivos_modelos.keys())
        self._scroll_widget = None

        # Construção da Interface
        self._build_widgets()
        self.carregar_arquivos_municipios()

    def _build_widgets(self):
        """Monta a estrutura visual dos componentes."""
        # Área principal rolável
        self._scroll_widget = ctk.CTkScrollableFrame(self)
        self._scroll_widget.pack(fill="both", expand=True, padx=15, pady=(15, 8))

        self._bind_mousewheel(self._scroll_widget)

        # Container de Seleção Topo
        frame_topo = ctk.CTkFrame(self._scroll_widget)
        frame_topo.pack(fill="x", padx=15, pady=15)

        lbl_select = ctk.CTkLabel(
            frame_topo,
            text="Selecione o Município:",
            font=ctk.CTkFont(weight="bold"),
        )
        lbl_select.pack(anchor="w", padx=10, pady=(10, 2))

        frame_combo = ctk.CTkFrame(frame_topo, fg_color="transparent")
        frame_combo.pack(fill="x", padx=10, pady=(0, 10))

        self.combo_municipios = ctk.CTkOptionMenu(
            frame_combo,
            values=["Nenhum carregado"],
            command=self._on_municipio_selected,
        )
        self.combo_municipios.pack(side="left", fill="x", expand=True, padx=(0, 5))

        btn_refresh = ctk.CTkButton(
            frame_combo, text="🔄", width=40, command=self.carregar_arquivos_municipios
        )
        btn_refresh.pack(side="right")

        # Container de Informações Atuais
        frame_info = ctk.CTkFrame(self._scroll_widget)
        frame_info.pack(fill="x", padx=15, pady=5)

        self.lbl_status_municipio = ctk.CTkLabel(
            frame_info,
            text="Nenhum município selecionado",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#1f538d",
        )
        self.lbl_status_municipio.pack(pady=10)

        # Container de Botões de Cópia
        frame_botoes = ctk.CTkFrame(self._scroll_widget)
        frame_botoes.pack(fill="both", expand=True, padx=15, pady=15)

        lbl_botoes = ctk.CTkLabel(
            frame_botoes,
            text="Clique para copiar os dados:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        lbl_botoes.pack(anchor="w", padx=15, pady=(10, 5))

        self.btn_nome = self._criar_botao_copia(
            frame_botoes, "NOME", lambda: self._copiar_campo("NOME")
        )
        self.btn_telefone = self._criar_botao_copia(
            frame_botoes, "TELEFONE", lambda: self._copiar_campo("TELEFONE")
        )
        self.btn_email = self._criar_botao_copia(
            frame_botoes, "EMAIL", lambda: self._copiar_campo("EMAIL")
        )
        self.btn_cnpj = self._criar_botao_copia(
            frame_botoes, "CNPJ", lambda: self._copiar_campo("CNPJ")
        )
        self.btn_tel_rep = self._criar_botao_copia(
            frame_botoes, 
            "TEL. REPRESENTANTE", 
            lambda: self._copiar_campo("TEL_REPRESENTANTE")
        )
        self.btn_nome_rep = self._criar_botao_copia(
            frame_botoes,
            "NOME DO REPRESENTANTE",
            lambda: self._copiar_campo("NOME_REPRESENTANTE"),
        )
        self.btn_cnpj_rep = self._criar_botao_copia(
            frame_botoes,
            "CNPJ DO REPRESENTANTE",
            lambda: self._copiar_campo("CNPJ_REPRESENTANTE"),
        )
        self.btn_email_rep = self._criar_botao_copia(
            frame_botoes,
            "E-MAIL DO REPRESENTANTE",
            lambda: self._copiar_campo("EMAIL_REPRESENTANTE"),
        )

        lbl_modelos = ctk.CTkLabel(
            frame_botoes,
            text="Modelo de ouvidoria:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        lbl_modelos.pack(anchor="w", padx=15, pady=(12, 5))

        frame_modelos = ctk.CTkFrame(frame_botoes, fg_color="transparent")
        frame_modelos.pack(fill="x", padx=15, pady=(0, 6))

        self.combo_modelos = ctk.CTkOptionMenu(
            frame_modelos,
            values=self.opcoes_modelos,
            width=280,
        )
        self.combo_modelos.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.combo_modelos.set(self.opcoes_modelos[0])

        self.btn_copiar_objetivo = self._criar_botao_copia(
            frame_modelos,
            "OBJETIVO",
            self._copiar_objetivo_selecionado,
            state="normal",
        )
        self.btn_copiar_objetivo.pack(side="right", padx=(6, 0))

        frame_tese = ctk.CTkFrame(frame_botoes, fg_color="transparent")
        frame_tese.pack(fill="x", padx=15, pady=(0, 6))

        ctk.CTkLabel(frame_tese, text="Tipo:").pack(side="left", padx=(0, 6))
        self.combo_tipo_tese = ctk.CTkOptionMenu(frame_tese, values=self.tipos_documento_tese, width=120)
        self.combo_tipo_tese.pack(side="left", padx=(0, 10))
        self.combo_tipo_tese.set(self.tipos_documento_tese[0])

        ctk.CTkLabel(frame_tese, text="Ano:").pack(side="left", padx=(0, 6))
        self.combo_ano_tese = ctk.CTkOptionMenu(frame_tese, values=self.anos_tese, width=100)
        self.combo_ano_tese.pack(side="left", padx=(0, 10))
        self.combo_ano_tese.set(self.anos_tese[0])

        ctk.CTkLabel(frame_tese, text="Nº:").pack(side="left", padx=(0, 6))
        self.spin_numero_tese = tk.Spinbox(frame_tese, from_=1, to=999, width=8)
        self.spin_numero_tese.pack(side="left")
        self.spin_numero_tese.delete(0, tk.END)
        self.spin_numero_tese.insert(0, "1")

        self.btn_copiar_modelo = self._criar_botao_copia(
            frame_botoes,
            "MODELO DE OUVIDORIA",
            self._copiar_modelo_ouvidoria,
            state="normal",
        )

        # Barra de Status/Feedback Inferior
        self.lbl_feedback = ctk.CTkLabel(
            self,
            text="Aguardando seleção...",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.lbl_feedback.pack(side="bottom", pady=8)

    def _bind_mousewheel(self, widget):
        """Permite rolar a área principal com o mouse em Windows."""

        def _on_mousewheel(event):
            delta = -1 * int(event.delta / 120) if event.delta else 0
            if delta:
                widget._parent_canvas.yview_scroll(delta, "units")

        widget.bind("<Enter>", lambda _event: widget.bind_all("<MouseWheel>", _on_mousewheel))
        widget.bind("<Leave>", lambda _event: widget.unbind_all("<MouseWheel>"))

    def _criar_botao_copia(self, master, label: str, command, state: str = "disabled") -> ctk.CTkButton:
        """Helper para padronizar os botões de ação."""
        btn = ctk.CTkButton(
            master,
            text=f"Copiar {label}",
            height=40,
            command=command,
            state=state,
        )
        btn.pack(fill="x", padx=15, pady=6)
        return btn

    def carregar_arquivos_municipios(self):
        """Varre o diretório configurado e carrega/atualiza a lista de municípios."""
        self.municipios_dados.clear()

        if not MUNICIPIOS_DIR.exists():
            self._set_feedback(
                f"Erro: Pasta '{MUNICIPIOS_DIR}' não encontrada.", erro=True
            )
            self.combo_municipios.configure(values=["Pasta não encontrada"])
            self.combo_municipios.set("Pasta não encontrada")
            return

        arquivos_tex = list(MUNICIPIOS_DIR.glob("*.tex"))

        if not arquivos_tex:
            self._set_feedback("Nenhum arquivo .tex encontrado.", erro=True)
            self.combo_municipios.configure(values=["Nenhum arquivo .tex"])
            self.combo_municipios.set("Nenhum arquivo .tex")
            return

        nomes_lista = []
        for file in arquivos_tex:
            try:
                cliente = TexParser.parse_file(file)
                self.municipios_dados[cliente.nome_municipio] = cliente
                nomes_lista.append(cliente.nome_municipio)
            except Exception as e:
                print(f"[Aviso] Erro no arquivo {file.name}: {e}")

        if not nomes_lista:
            self._set_feedback(
                "Erro ao ler os arquivos .tex (incompatíveis/incompletos).",
                erro=True,
            )
            return

        nomes_lista.sort()
        self.combo_municipios.configure(values=nomes_lista)

        # Seleciona o primeiro da lista automaticamente
        primeiro = nomes_lista[0]
        self.combo_municipios.set(primeiro)
        self._on_municipio_selected(primeiro)

        self._set_feedback(
            f"{len(nomes_lista)} municípios carregados com sucesso!"
        )

    def _on_municipio_selected(self, nome_selecionado: str):
        """Callback executado ao mudar o item da ComboBox."""
        self.cliente_atual = self.municipios_dados.get(nome_selecionado)

        if self.cliente_atual:
            self.lbl_status_municipio.configure(
                text=f"{self.cliente_atual.nome_formatado}", text_color="#2FA572"
            )
            self._habilitar_botoes(True)
            self._set_feedback(f"Município '{nome_selecionado}' selecionado.")
        else:
            self.lbl_status_municipio.configure(
                text="Erro ao carregar dados do município", text_color="#D32F2F"
            )
            self._habilitar_botoes(False)

    def _habilitar_botoes(self, state: bool):
        """Habilita ou desabilita os botões de cópia."""
        st = "normal" if state else "disabled"
        self.btn_nome.configure(state=st)
        self.btn_telefone.configure(state=st)
        self.btn_email.configure(state=st)
        self.btn_cnpj.configure(state=st)
        self.btn_tel_rep.configure(state=st)
        self.btn_nome_rep.configure(state=st)
        self.btn_cnpj_rep.configure(state=st)
        self.btn_email_rep.configure(state=st)

    def _copiar_campo(self, campo: str):
        """Copia o conteúdo do campo solicitado e exibe feedback imediato."""
        if not self.cliente_atual:
            return

        valor = self.cliente_atual.obter_campo(campo)
        if valor:
            self.clipboard_mgr.copy_to_clipboard(valor)
            self._set_feedback(f"'{campo}' copiado com sucesso: ({valor})")

    def _copiar_modelo_ouvidoria(self):
        """Copia o modelo de ouvidoria com os placeholders preenchidos."""
        texto = self._gerar_texto_modelo()
        if texto:
            self.clipboard_mgr.copy_to_clipboard(texto)
            self._set_feedback("Modelo de ouvidoria copiado.")

    def _copiar_objetivo_selecionado(self):
        """Copia o texto do objetivo associado à opção selecionada."""
        objetivo = self.objetivos_modelos.get(self.combo_modelos.get())
        if objetivo:
            self.clipboard_mgr.copy_to_clipboard(objetivo)
            self._set_feedback(f"Objetivo copiado: ({objetivo})")

    def _gerar_texto_modelo(self) -> str:
        """Gera o conteúdo final do modelo com os placeholders preenchidos."""
        template = self.modelos_config.get("Modelo de ouvidoria", "")
        if not template:
            return ""

        if not self.cliente_atual:
            return template

        concessionaria = (
            getattr(self.cliente_atual, "concessionaria", "")
            or self.cliente_atual.empresa_responsavel
            or "CONCESSIONÁRIA"
        )
        municipio = self.cliente_atual.nome_municipio or "MUNICÍPIO"
        objetivo = self.objetivos_modelos.get(
            self.combo_modelos.get(),
            "contestar o memorial de cálculo",
        )
        tipo_documento = self.combo_tipo_tese.get().upper()
        numero_texto = self.spin_numero_tese.get().strip()
        numero = int(numero_texto) if numero_texto.isdigit() else 1
        ano = self.combo_ano_tese.get()
        tese = f"{tipo_documento} {numero:03d}/{ano}"
        oficio = "OFÍCIO"

        return (
            template.replace("<<CONCESSIONÁRIA>>", concessionaria)
            .replace("<<TESE>>", tese)
            .replace("<<MUNICÍPIO>>", municipio)
            .replace("<<OBJETIVO>>", objetivo)
            .replace("<<OFÍCIO>>", oficio)
        )

    def _set_feedback(self, texto: str, erro: bool = False):
        """Atualiza a mensagem da barra de status."""
        cor = "#D32F2F" if erro else "gray"
        self.lbl_feedback.configure(text=texto, text_color=cor)