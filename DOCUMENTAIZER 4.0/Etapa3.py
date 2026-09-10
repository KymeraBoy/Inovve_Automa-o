import os
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfFileReader as PdfReader
    except ImportError:
        PdfReader = None


class WorkerCompilacao(QThread):
    """
    Thread secundária para executar a compilação via MiKTeX portátil
    e movimentação dos arquivos PDF sem travar a interface gráfica.
    """
    progresso = Signal(int, str)
    sucesso = Signal(str)
    erro = Signal(str, str)

    def __init__(self, texto_latex, pasta_empresa, pasta_municipio, nome_municipio, caminho_lualatex=None, caminho_miktex_bin=None):
        super().__init__()
        self.texto_latex = texto_latex
        self.pasta_empresa = pasta_empresa
        self.pasta_municipio = pasta_municipio
        self.nome_municipio = nome_municipio
        self.caminho_lualatex = caminho_lualatex
        self.caminho_miktex_bin = caminho_miktex_bin

    def limpar_texto(self, texto):
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = texto.upper()
        texto = re.sub(r'[<>:"/\\|?*]', "", texto)
        texto = re.sub(r"[^A-Z0-9 ]", "", texto)
        return re.sub(r"\s+", " ", texto).strip()

    def run(self):
        try:
            self.progresso.emit(10, "Preparando diretórios...")
            raiz_app = Path(__file__).resolve().parent
            pasta_saida = raiz_app / "SAIDA"

            try:
                pasta_saida.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                self.erro.emit("Erro de Pasta", f"Não foi possível criar a pasta SAIDA na raiz: {e}")
                return

            self.progresso.emit(25, "Localizando template LaTeX...")
            arquivos_tex = list(self.pasta_empresa.glob("*.tex"))
            if not arquivos_tex:
                self.erro.emit(
                    "Template não encontrado",
                    f"Nenhum arquivo .tex foi encontrado na pasta da empresa:\n{self.pasta_empresa}"
                )
                return

            caminho_template = arquivos_tex[0]

            self.progresso.emit(40, "Montando arquivo .tex...")
            try:
                with open(caminho_template, "r", encoding="utf-8") as f:
                    conteudo_template = f.read()
            except Exception as e:
                self.erro.emit("Erro de Leitura", f"Erro ao ler o template LaTeX da empresa: {e}")
                return

            conteudo_final = conteudo_template.replace("<<TEXTO>>", self.texto_latex)

            m_mun = self.limpar_texto(self.nome_municipio)
            nome_base = f"{m_mun} - SUMARIO"
            caminho_tex_temp = pasta_saida / f"{nome_base}.tex"

            try:
                with open(caminho_tex_temp, "w", encoding="utf-8") as f:
                    f.write(conteudo_final)
            except Exception as e:
                self.erro.emit("Erro ao Gravar TEX", f"Falha ao gerar arquivo .tex na pasta SAIDA: {e}")
                return

            self.progresso.emit(60, "Compilando documento via LuaLaTeX...")

            # Define qual executável utilizar (Portátil ou Global)
            if self.caminho_lualatex and Path(self.caminho_lualatex).exists():
                executavel_lualatex = str(self.caminho_lualatex)
            else:
                executavel_lualatex = "lualatex"

            cmd = [
                executavel_lualatex,
                "-interaction=nonstopmode",
                f"-output-directory={pasta_saida}",
                str(caminho_tex_temp)
            ]

            env = os.environ.copy()

            # Adiciona os binários do MiKTeX ao PATH para resolução de DLLs
            if self.caminho_miktex_bin and Path(self.caminho_miktex_bin).exists():
                env["PATH"] = f"{Path(self.caminho_miktex_bin).as_posix()};{env.get('PATH', '')}"

            # Define a busca de templates e imagens na pasta da empresa
            env["TEXINPUTS"] = f".;{self.pasta_empresa.as_posix()};;"

            processo = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)

            if processo.returncode != 0:
                self.erro.emit(
                    "Erro na Compilação",
                    "O LuaLaTeX encontrou um erro durante a compilação.\nConsulte o arquivo de log gerado na pasta SAIDA."
                )
                return

            self.progresso.emit(85, "Copiando PDF final...")
            pasta_anexos_mun = Path(self.pasta_municipio) / "ANEXOS"
            try:
                pasta_anexos_mun.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                self.erro.emit("Erro de Pasta", f"Não foi possível criar a pasta ANEXOS do município: {e}")
                return

            pdf_origem = pasta_saida / f"{nome_base}.pdf"
            pdf_destino = pasta_anexos_mun / f"{nome_base}.pdf"

            if not pdf_origem.exists():
                self.erro.emit("Erro no Arquivo", "O PDF não foi gerado corretamente na pasta SAIDA.")
                return

            try:
                shutil.copy2(pdf_origem, pdf_destino)
            except Exception as e:
                self.erro.emit("Erro ao Copiar PDF", f"Não foi possível copiar o PDF para a pasta ANEXOS: {e}")
                return

            self.progresso.emit(95, "Limpando arquivos temporários...")
            extensoes_temp = [".aux", ".log", ".tex", ".out", ".toc"]
            for ext in extensoes_temp:
                arq_temp = pasta_saida / f"{nome_base}{ext}"
                if arq_temp.exists():
                    try:
                        arq_temp.unlink()
                    except OSError:
                        pass

            self.progresso.emit(100, "Concluído!")
            self.sucesso.emit(str(pdf_destino))

        except FileNotFoundError:
            self.erro.emit(
                "LuaLaTeX não encontrado",
                "O compilador do MiKTeX/LuaLaTeX não foi localizado na pasta portátil nem no PATH do sistema."
            )
        except Exception as e:
            self.erro.emit("Erro na Execução", f"Falha ao executar o processo: {e}")


class Etapa3(QWidget):
    """
    Terceira etapa do Documentaizer:
    Geração do Sumário em LaTeX e Compilação em PDF via LuaLaTeX.
    """

    pdf_gerado = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.nome_municipio = ""
        self.sigla_uf = ""
        self.empresa_selecionada = ""
        self.pasta_municipio = ""
        self.pasta_empresa = None
        self.caminho_lualatex = None
        self.caminho_miktex_bin = None

        self.texto_latex_gerado = ""
        self.worker = None

        self.criar_interface()

    def criar_interface(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(10, 10, 10, 10)
        self.layout_principal.setSpacing(8)

        # TÍTULO
        self.titulo = QLabel("ETAPA 3 - GERAÇÃO DO SUMÁRIO")
        self.titulo.setAlignment(Qt.AlignCenter)
        self.titulo.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
            }
            """
        )
        self.layout_principal.addWidget(self.titulo)

        # PRÉ-VISUALIZAÇÃO DO SUMÁRIO
        self.label_preview = QLabel("Pré-visualização do Sumário:")
        self.label_preview.setStyleSheet("font-weight: bold;")
        self.layout_principal.addWidget(self.label_preview)

        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        
        self.text_preview.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_preview.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.text_preview.setStyleSheet(
            """
            QTextEdit {
                background-color: #ffffff;
                color: #212529;
                font-family: Arial, sans-serif;
                font-size: 13px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 10px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            """
        )
        self.layout_principal.addWidget(self.text_preview, 1)

        # BARRA E RÓTULO DE PROGRESSO
        self.label_status_progresso = QLabel("")
        self.label_status_progresso.setStyleSheet("font-size: 12px; color: #555555;")
        self.label_status_progresso.setAlignment(Qt.AlignCenter)
        self.label_status_progresso.hide()
        self.layout_principal.addWidget(self.label_status_progresso)

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setRange(0, 100)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(True)
        self.barra_progresso.setStyleSheet(
            """
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0056b3;
                border-radius: 3px;
            }
            """
        )
        self.barra_progresso.hide()
        self.layout_principal.addWidget(self.barra_progresso)

        # BOTÃO DE COMPILAÇÃO E GERAÇÃO DO PDF
        self.botao_gerar_pdf = QPushButton("GERAR SUMÁRIO (PDF)")
        self.botao_gerar_pdf.setMinimumHeight(40)
        self.botao_gerar_pdf.setStyleSheet(
            """
            QPushButton {
                background-color: #0056b3;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #004085;
            }
            QPushButton:pressed {
                background-color: #002752;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            """
        )
        self.botao_gerar_pdf.clicked.connect(self.compilar_latex_para_pdf)
        self.layout_principal.addWidget(self.botao_gerar_pdf)

    def set_dados(self, municipio, uf, empresa, pasta_municipio, pasta_empresa, caminho_lualatex=None, caminho_miktex_bin=None):
        self.nome_municipio = municipio.strip()
        self.sigla_uf = uf.strip().upper()
        self.empresa_selecionada = empresa.strip()
        self.pasta_municipio = pasta_municipio
        self.pasta_empresa = Path(pasta_empresa) if pasta_empresa else None
        self.caminho_lualatex = caminho_lualatex
        self.caminho_miktex_bin = caminho_miktex_bin

        self.gerar_codigo_sumario()

    @staticmethod
    def int_para_romano(numero):
        val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        syb = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        romano = ""
        i = 0
        while numero > 0:
            for _ in range(numero // val[i]):
                romano += syb[i]
                numero -= val[i]
            i += 1
        return romano

    @staticmethod
    def int_para_ordinal(numero):
        return f"{numero}º"

    def contar_paginas_pdf(self, caminho_arquivo):
        if not caminho_arquivo or not Path(caminho_arquivo).exists():
            return 0
        try:
            reader = PdfReader(str(caminho_arquivo))
            return len(reader.pages)
        except Exception as e:
            print(f"Erro ao ler páginas de {caminho_arquivo}: {e}")
            return 0

    def mapear_arquivos_municipio(self):
        mapa = {
            "PROCURACAO": None,
            "RELATORIO_PROCURACAO": None,
            "KIT_PREFEITO": None,
            "CONTRATO": None,
            "RELATORIO_CONTRATO": None,
            "PUBLICACAO_CONTRATO": None,
            "ADITIVOS": {},
        }

        if not self.pasta_municipio:
            return mapa

        pasta = Path(self.pasta_municipio)
        if not pasta.exists() or not pasta.is_dir():
            return mapa

        for arq in pasta.iterdir():
            if not arq.is_file() or arq.suffix.lower() != ".pdf":
                continue

            nome = arq.stem.upper()

            if "PROCURACAO" in nome and "RELATORIO" not in nome:
                mapa["PROCURACAO"] = arq
            elif "RELATORIO" in nome and "PROCURACAO" in nome:
                mapa["RELATORIO_PROCURACAO"] = arq
            elif "KIT PREFEITO" in nome or "KIT_PREFEITO" in nome:
                mapa["KIT_PREFEITO"] = arq
            elif "CONTRATO" in nome and "RELATORIO" not in nome and "PUBLICACAO" not in nome and "ADITIVO" not in nome:
                mapa["CONTRATO"] = arq
            elif "RELATORIO" in nome and "CONTRATO" in nome and "ADITIVO" not in nome:
                mapa["RELATORIO_CONTRATO"] = arq
            elif "PUBLICACAO" in nome and "CONTRATO" in nome and "ADITIVO" not in nome:
                mapa["PUBLICACAO_CONTRATO"] = arq
            elif "ADITIVO" in nome:
                num_match = re.search(r"ADITIVO_(\d+)", nome)
                if not num_match:
                    num_match = re.search(r"ADITIVO\s+(\d+)", nome)

                num = num_match.group(1) if num_match else "1"

                if num not in mapa["ADITIVOS"]:
                    mapa["ADITIVOS"][num] = {
                        "ADITIVO": None,
                        "RELATORIO": None,
                        "PUBLICACAO": None,
                    }

                if "RELATORIO" in nome:
                    mapa["ADITIVOS"][num]["RELATORIO"] = arq
                elif "PUBLICACAO" in nome:
                    mapa["ADITIVOS"][num]["PUBLICACAO"] = arq
                else:
                    mapa["ADITIVOS"][num]["ADITIVO"] = arq

        return mapa

    def mapear_arquivos_empresa(self):
        mapa = {
            "REPRESENTANTE": None,
            "CONTRATO_SOCIAL": None,
        }

        if not self.pasta_empresa or not self.pasta_empresa.exists():
            return mapa

        for arq in self.pasta_empresa.iterdir():
            if not arq.is_file() or arq.suffix.lower() != ".pdf":
                continue

            nome = arq.stem.upper()
            if "REPRESENTANTE" in nome or "DOCUMENTO" in nome:
                mapa["REPRESENTANTE"] = arq
            elif "CONTRATO" in nome or "SOCIAL" in nome:
                mapa["CONTRATO_SOCIAL"] = arq

        return mapa

    def gerar_codigo_sumario(self):
        if not self.nome_municipio or not self.pasta_municipio:
            self.text_preview.setHtml("<p style='color: #6c757d;'><i>Aguardando seleção de município e pasta...</i></p>")
            self.texto_latex_gerado = ""
            return

        mapa_mun = self.mapear_arquivos_municipio()
        mapa_emp = self.mapear_arquivos_empresa()

        mun_upper = self.nome_municipio.upper()
        uf_upper = self.sigla_uf.upper()

        linhas_tex = [f"\\textbf{{SUMÁRIO - {mun_upper} - {uf_upper}}}\\\\", "\\strut \\\\"]
        
        html_preview = [
            f"<h3 style='text-align: center; color: #000000; margin-bottom: 20px;'>SUMÁRIO - {mun_upper} - {uf_upper}</h3>"
        ]

        # ANEXO I - INSTRUMENTOS PROCURATÓRIOS
        docs_anexo_1 = [
            ("Procuração", mapa_mun["PROCURACAO"]),
            ("Validação das assinaturas", mapa_mun["RELATORIO_PROCURACAO"]),
            ("Kit prefeito", mapa_mun["KIT_PREFEITO"]),
            ("Contrato Social da Empresa", mapa_emp["CONTRATO_SOCIAL"]),
            ("Documento de Identificação do Representante", mapa_emp["REPRESENTANTE"]),
        ]

        linhas_tex.append("\\textbf{Anexo I -- Instrumentos procuratórios \\dotfill 1}")
        linhas_tex.append("\\begin{enumerate}")

        html_preview.append("<p style='font-weight: bold; margin-bottom: 5px; color: #000000;'>Anexo I &ndash; Instrumentos procuratórios <span style='float: right;'>1</span></p>")
        html_preview.append("<ol style='margin-top: 0px; margin-bottom: 15px; padding-left: 25px; color: #212529;'>")

        pagina_atual = 1
        for rotulo, arq_path in docs_anexo_1:
            if arq_path and arq_path.exists():
                linhas_tex.append(f"    \\item {rotulo} \\dotfill {pagina_atual}")
                html_preview.append(f"<li style='margin-bottom: 3px;'>{rotulo} <span style='letter-spacing: 2px;'>...................................................................................................</span> <b>{pagina_atual}</b></li>")
                qtd = self.contar_paginas_pdf(arq_path)
                pagina_atual += max(qtd, 1)

        linhas_tex.append("\\end{enumerate}")
        html_preview.append("</ol>")

        # ANEXO II - DOCUMENTOS CONTRATUAIS
        docs_anexo_2 = [
            ("Contrato", mapa_mun["CONTRATO"]),
            ("Validação das assinaturas", mapa_mun["RELATORIO_CONTRATO"]),
            ("Publicação do Contrato em Diário Oficial", mapa_mun["PUBLICACAO_CONTRATO"]),
        ]

        linhas_tex.append("\\textbf{Anexo II -- Documentos contratuais \\dotfill 1}")
        linhas_tex.append("\\begin{enumerate}")

        html_preview.append("<p style='font-weight: bold; margin-bottom: 5px; color: #000000;'>Anexo II &ndash; Documentos contratuais <span style='float: right;'>1</span></p>")
        html_preview.append("<ol style='margin-top: 0px; margin-bottom: 15px; padding-left: 25px; color: #212529;'>")

        pagina_atual = 1
        for rotulo, arq_path in docs_anexo_2:
            if arq_path and arq_path.exists():
                linhas_tex.append(f"    \\item {rotulo} \\dotfill {pagina_atual}")
                html_preview.append(f"<li style='margin-bottom: 3px;'>{rotulo} <span style='letter-spacing: 2px;'>...................................................................................................</span> <b>{pagina_atual}</b></li>")
                qtd = self.contar_paginas_pdf(arq_path)
                pagina_atual += max(qtd, 1)

        linhas_tex.append("\\end{enumerate}")
        html_preview.append("</ol>")

        # ANEXO III+ - TERMOS ADITIVOS
        aditivos_ordenados = sorted(mapa_mun["ADITIVOS"].keys(), key=lambda x: int(x) if x.isdigit() else 0)

        for num_str in aditivos_ordenados:
            num = int(num_str) if num_str.isdigit() else 1
            num_anexo_int = num + 2
            num_anexo_romano = self.int_para_romano(num_anexo_int)
            ord_str = self.int_para_ordinal(num)

            item_aditivo = mapa_mun["ADITIVOS"][num_str]
            docs_anexo_3 = [
                (f"{ord_str} Aditivo", item_aditivo["ADITIVO"]),
                (f"Validação das assinaturas do {ord_str} Aditivo", item_aditivo["RELATORIO"]),
                (f"Publicação do {ord_str} Aditivo em Diário Oficial", item_aditivo["PUBLICACAO"]),
            ]

            linhas_tex.append(f"\\textbf{{Anexo {num_anexo_romano} -- {ord_str} Termo Aditivo \\dotfill 1}}")
            linhas_tex.append("\\begin{enumerate}")

            html_preview.append(f"<p style='font-weight: bold; margin-bottom: 5px; color: #000000;'>Anexo {num_anexo_romano} &ndash; {ord_str} Termo Aditivo <span style='float: right;'>1</span></p>")
            html_preview.append("<ol style='margin-top: 0px; margin-bottom: 15px; padding-left: 25px; color: #212529;'>")

            pagina_atual = 1
            for rotulo, arq_path in docs_anexo_3:
                if arq_path and arq_path.exists():
                    linhas_tex.append(f"    \\item {rotulo} \\dotfill {pagina_atual}")
                    html_preview.append(f"<li style='margin-bottom: 3px;'>{rotulo} <span style='letter-spacing: 2px;'>...................................................................................................</span> <b>{pagina_atual}</b></li>")
                    qtd = self.contar_paginas_pdf(arq_path)
                    pagina_atual += max(qtd, 1)

            linhas_tex.append("\\end{enumerate}")
            html_preview.append("</ol>")

        self.texto_latex_gerado = "\n".join(linhas_tex)
        self.text_preview.setHtml("".join(html_preview))

    def compilar_latex_para_pdf(self):
        if not self.texto_latex_gerado:
            QMessageBox.warning(self, "Aviso", "Nenhum texto de sumário foi gerado para compilação.")
            return

        if not self.pasta_empresa or not self.pasta_empresa.exists():
            QMessageBox.critical(
                self,
                "Empresa não encontrada",
                "A pasta da empresa selecionada não foi localizada."
            )
            return

        # Prepara elementos visuais de progresso
        self.botao_gerar_pdf.setEnabled(False)
        self.barra_progresso.setValue(0)
        self.label_status_progresso.setText("Iniciando geração do PDF...")
        self.label_status_progresso.show()
        self.barra_progresso.show()

        # Instancia e inicia a thread WorkerCompilacao
        self.worker = WorkerCompilacao(
            texto_latex=self.texto_latex_gerado,
            pasta_empresa=self.pasta_empresa,
            pasta_municipio=self.pasta_municipio,
            nome_municipio=self.nome_municipio,
            caminho_lualatex=self.caminho_lualatex,
            caminho_miktex_bin=self.caminho_miktex_bin
        )
        self.worker.progresso.connect(self.atualizar_progresso)
        self.worker.sucesso.connect(self.compilacao_sucesso)
        self.worker.erro.connect(self.compilacao_erro)
        self.worker.start()

    def atualizar_progresso(self, valor, mensagem):
        self.barra_progresso.setValue(valor)
        self.label_status_progresso.setText(mensagem)

    def compilacao_sucesso(self, destino_pdf):
        self.finalizar_progresso()
        QMessageBox.information(
            self,
            "Sucesso",
            f"Sumário PDF gerado com sucesso!\nSalvo em: {destino_pdf}"
        )
        self.pdf_gerado.emit()

    def compilacao_erro(self, titulo, mensagem):
        self.finalizar_progresso()
        QMessageBox.critical(self, titulo, mensagem)

    def finalizar_progresso(self):
        self.botao_gerar_pdf.setEnabled(True)
        self.barra_progresso.hide()
        self.label_status_progresso.hide()