import re
import unicodedata
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

try:
    from pypdf import PdfWriter
except ImportError:
    try:
        from PyPDF2 import PdfMerger as PdfWriter
    except ImportError:
        PdfWriter = None


class Etapa2(QWidget):
    """
    Segunda etapa do Documentaizer: Montagem dos Anexos (PDF).
    """

    anexos_gerados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.nome_municipio = ""
        self.pasta_municipio = ""
        self.pasta_empresa = None

        self.estrutura_anexos = []

        self.criar_interface()

    def criar_interface(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(10, 10, 10, 10)
        self.layout_principal.setSpacing(8)

        # TÍTULO
        self.titulo = QLabel("ETAPA 2 - MONTAGEM DOS ANEXOS")
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

        # ÁREA DE VISUALIZAÇÃO COM ROLAGEM
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.StyledPanel)

        self.container_scroll = QWidget()
        self.layout_scroll = QVBoxLayout(self.container_scroll)
        self.layout_scroll.setSpacing(10)
        self.layout_scroll.setAlignment(Qt.AlignTop)

        self.scroll_area.setWidget(self.container_scroll)
        self.layout_principal.addWidget(self.scroll_area, 1)

        # BOTÃO DE GERAÇÃO DOS ANEXOS (VERDE ESCURO)
        self.botao_gerar = QPushButton("GERAR ANEXOS (PDF)")
        self.botao_gerar.setMinimumHeight(40)
        self.botao_gerar.setStyleSheet(
            """
            QPushButton {
                background-color: #1e7e34;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #155724;
            }
            QPushButton:pressed {
                background-color: #0b2e13;
            }
            """
        )
        self.botao_gerar.clicked.connect(self.gerar_anexos_pdf)

        self.layout_principal.addWidget(self.botao_gerar)

    def set_pasta_municipio(self, pasta):
        self.pasta_municipio = pasta
        self.atualizar_estrutura()

    def set_dados(self, nome_municipio, pasta_empresa):
        self.nome_municipio = nome_municipio.strip()
        self.pasta_empresa = pasta_empresa
        self.atualizar_estrutura()

    @staticmethod
    def int_para_romano(numero):
        """
        Converte um número inteiro para algarismos romanos.
        """
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
    def limpar_texto(texto):
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(
            c for c in texto if not unicodedata.combining(c)
        )
        texto = texto.upper()
        texto = re.sub(r'[<>:"/\\|?*]', "", texto)
        texto = re.sub(r"[^A-Z0-9 ]", "", texto)
        return re.sub(r"\s+", " ", texto).strip()

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

    def atualizar_estrutura(self):
        for i in reversed(range(self.layout_scroll.count())):
            widget = self.layout_scroll.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.estrutura_anexos.clear()

        m_mun = self.limpar_texto(self.nome_municipio) if self.nome_municipio else "MUNICIPIO"
        mapa_mun = self.mapear_arquivos_municipio()
        mapa_emp = self.mapear_arquivos_empresa()

        # -------------------------------------------------------------
        # TIPO I - INSTRUMENTOS PROCURATORIOS
        # -------------------------------------------------------------
        nome_anexo_1 = f"{m_mun} - ANEXO I - INSTRUMENTOS PROCURATORIOS.pdf"
        docs_1 = [
            ("Procuração", mapa_mun["PROCURACAO"]),
            ("Relatório de Assinaturas da Procuração", mapa_mun["RELATORIO_PROCURACAO"]),
            ("Kit Prefeito", mapa_mun["KIT_PREFEITO"]),
            ("Contrato Social da Empresa", mapa_emp["CONTRATO_SOCIAL"]),
            ("Documento do Representante", mapa_emp["REPRESENTANTE"]),
        ]
        self.estrutura_anexos.append((nome_anexo_1, docs_1))

        # -------------------------------------------------------------
        # TIPO II - DOCUMENTOS CONTRATUAIS
        # -------------------------------------------------------------
        nome_anexo_2 = f"{m_mun} - ANEXO II - DOCUMENTOS CONTRATUAIS.pdf"
        docs_2 = [
            ("Contrato", mapa_mun["CONTRATO"]),
            ("Relatório de Assinaturas do Contrato", mapa_mun["RELATORIO_CONTRATO"]),
            ("Publicação do Contrato", mapa_mun["PUBLICACAO_CONTRATO"]),
        ]
        self.estrutura_anexos.append((nome_anexo_2, docs_2))

        # -------------------------------------------------------------
        # TIPO III - ADITIVOS (NUMERAÇÃO EM ALGARISMOS ROMANOS)
        # -------------------------------------------------------------
        aditivos_ordenados = sorted(mapa_mun["ADITIVOS"].keys(), key=lambda x: int(x) if x.isdigit() else 0)

        for num_str in aditivos_ordenados:
            num = int(num_str) if num_str.isdigit() else 1
            num_anexo_int = num + 2  # Aditivo 1 -> 3 (III), Aditivo 2 -> 4 (IV)...
            num_anexo_romano = self.int_para_romano(num_anexo_int)

            nome_anexo_3 = f"{m_mun} - ANEXO {num_anexo_romano} - ADITIVO {num}.pdf"

            item_aditivo = mapa_mun["ADITIVOS"][num_str]
            docs_3 = [
                (f"Aditivo {num}", item_aditivo["ADITIVO"]),
                (f"Relatório de Assinaturas do Aditivo {num}", item_aditivo["RELATORIO"]),
                (f"Publicação do Aditivo {num}", item_aditivo["PUBLICACAO"]),
            ]
            self.estrutura_anexos.append((nome_anexo_3, docs_3))

        for nome_anexo, docs in self.estrutura_anexos:
            card = self.criar_card_anexo(nome_anexo, docs)
            self.layout_scroll.addWidget(card)

    def criar_card_anexo(self, nome_anexo, documentos):
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(
            """
            QFrame {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 6px;
            }
            """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        label_titulo = QLabel(nome_anexo)
        label_titulo.setStyleSheet("font-weight: bold; color: #003366;")
        layout.addWidget(label_titulo)

        for desc, arq_path in documentos:
            label_doc = QLabel()
            if arq_path and arq_path.exists():
                label_doc.setText(f"  ✓ {desc}: {arq_path.name}")
                label_doc.setStyleSheet("color: #1e7e34;")
            else:
                label_doc.setText(f"  ✗ {desc}: (FALTANDO)")
                label_doc.setStyleSheet("color: #d9534f;")

            layout.addWidget(label_doc)

        return card

    def gerar_anexos_pdf(self):
        if PdfWriter is None:
            QMessageBox.critical(
                self,
                "Erro",
                "A biblioteca 'pypdf' não está instalada.\nExecute: pip install pypdf"
            )
            return

        if not self.pasta_municipio:
            QMessageBox.warning(
                self,
                "Atenção",
                "Selecione a pasta do município antes de gerar os anexos."
            )
            return

        # Define a pasta ANEXOS dentro do diretório do município
        pasta_destino = Path(self.pasta_municipio) / "ANEXOS"
        
        # Cria a pasta caso ela não exista
        try:
            pasta_destino.mkdir(parents=True, exist_ok=True)
        except OSError as erro:
            QMessageBox.critical(
                self,
                "Erro ao criar diretório",
                f"Não foi possível criar a pasta 'ANEXOS': {erro}"
            )
            return

        anexos_criados = 0

        for nome_anexo, docs in self.estrutura_anexos:
            writer = PdfWriter()
            arquivos_adicionados = 0

            for desc, arq_path in docs:
                if arq_path and arq_path.exists():
                    try:
                        writer.append(str(arq_path))
                        arquivos_adicionados += 1
                    except Exception as e:
                        print(f"Erro ao ler {arq_path}: {e}")

            if arquivos_adicionados > 0:
                caminho_saida = pasta_destino / nome_anexo
                try:
                    with open(caminho_saida, "wb") as f_out:
                        writer.write(f_out)
                    anexos_criados += 1
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Erro ao salvar",
                        f"Não foi possível salvar {nome_anexo}: {e}"
                    )

        if anexos_criados > 0:
            QMessageBox.information(
                self,
                "Sucesso",
                f"{anexos_criados} anexo(s) foram gerados com sucesso na pasta ANEXOS!"
            )
            self.anexos_gerados.emit()
        else:
            QMessageBox.warning(
                self,
                "Aviso",
                "Nenhum documento VÁLIDO foi encontrado para compor os anexos."
            )