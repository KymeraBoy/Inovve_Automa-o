"""
Módulo de Configuração Global.
Centraliza caminhos de diretórios, dicionários de mapeamento e constantes.
"""

from pathlib import Path

# Caminho absoluto da pasta de municípios
MUNICIPIOS_DIR = Path(
    r"C:\Users\Usuário 1\Documents\Inovve_Automação\Gerador_de_Documentos\MUNICIPIOS"
)

# Mapeamento de arquivos de concessionária para o Estado correspondente
CONCESSIONARIA_ESTADO_MAP = {
    "COELBA.tex": "Bahia",
    "ENERGISA_MATO_GROSSO_DO_SUL.tex": "Mato Grosso do Sul",
    "ENERGISA_PARAIBA.tex": "Paraíba",
    "EQUATORIAL_GOIAS.tex": "Goiás",
    "NEOENERGIA_PERNAMBUCO.tex": "Pernambuco",
    "NEOENERGIA_RIO_GRANDE_DO_NORTE.tex": "Rio Grande do Norte",
}

# Configurações visuais da GUI
APP_TITLE = "Assistente de Preenchimento ANEEL"
APP_GEOMETRY = "500x800"
THEME_MODE = "Dark"
COLOR_THEME = "blue"