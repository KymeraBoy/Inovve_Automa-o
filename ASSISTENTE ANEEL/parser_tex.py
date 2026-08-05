"""
Módulo de Parsing TeX.
Responsável por ler os arquivos .tex e extrair variáveis via Expressões Regulares.
"""


from pathlib import Path
import re
from config import CONCESSIONARIA_ESTADO_MAP, PREAMBULO_EMPRESA_MAP
from models import ClienteMunicipio


class TexParser:
    """Parser para arquivos de configuração cadastral em formato LaTeX."""

    # Padrões Regex pré-compilados para maior performance
    REGEX_INPUT = re.compile(
        r"\\input\{.*?/([^/]+\.tex)\}", re.IGNORECASE
    )
    REGEX_NOME = re.compile(
        r"\\newcommand\{\\nomeMunicipio\}\{(.*?)\}", re.IGNORECASE
    )
    REGEX_CNPJ = re.compile(
        r"\\newcommand\{\\cnpjMunicipio\}\{(.*?)\}", re.IGNORECASE
    )
    REGEX_TELEFONE = re.compile(
        r"\\newcommand\{\\telefone\}\{(.*?)\}", re.IGNORECASE
    )
    REGEX_EMAIL = re.compile(
        r"\\newcommand\{\\email\}\{(.*?)\}", re.IGNORECASE
    )
    REGEX_EMPRESA = re.compile(
        r"\\newcommand\{\\empresaResponsavel\}\{(.*?)\}", re.IGNORECASE
    )

    REGEX_PREAMBULO_COMANDO = re.compile(
        r"\\(?:providecommand|newcommand)\{\\(?P<nome>[A-Za-z]+)\}\{(?P<valor>.*?)\}",
        re.IGNORECASE,
    )

    COMANDOS_EMPRESA = {
        "representante_nome": {"RepresentanteEmpresa"},
        "representante_email": {"EmailEmpresa", "emailEmpresa"},
        "representante_cnpj": {"CNPJEmpresa"},
        "representante_telefone": {"TelefoneEmpresa"},
    }

    @classmethod
    def _extrair_comando_preambulo(cls, content: str, nomes: set[str]) -> str:
        for match in cls.REGEX_PREAMBULO_COMANDO.finditer(content):
            if match.group("nome") in nomes:
                return match.group("valor").strip()
        return ""

    @classmethod
    def _carregar_dados_empresa(cls, empresa_responsavel: str) -> dict:
        empresa = empresa_responsavel.upper().strip()
        preambulo_path = PREAMBULO_EMPRESA_MAP.get(empresa)

        if not preambulo_path or not preambulo_path.exists():
            return {
                "representante_nome": "",
                "representante_cnpj": "",
                "representante_email": "",
                "representante_telefone": "",
            }

        try:
            content = preambulo_path.read_text(encoding="utf-8")
        except Exception:
            return {
                "representante_nome": "",
                "representante_cnpj": "",
                "representante_email": "",
                "representante_telefone": "",
            }

        return {
            campo: cls._extrair_comando_preambulo(content, nomes)
            for campo, nomes in cls.COMANDOS_EMPRESA.items()
        }

    @classmethod
    def parse_file(cls, filepath: Path) -> ClienteMunicipio:
        """
        Lê um arquivo .tex e constrói a instância de ClienteMunicipio.
        Gera ValueError caso algum campo essencial esteja ausente.
        """
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception as e:
            raise IOError(
                f"Não foi possível ler o arquivo '{filepath.name}': {e}"
            )

        # Extração das variáveis via Regex
        match_input = cls.REGEX_INPUT.search(content)
        match_nome = cls.REGEX_NOME.search(content)
        match_cnpj = cls.REGEX_CNPJ.search(content)
        match_tel = cls.REGEX_TELEFONE.search(content)
        match_email = cls.REGEX_EMAIL.search(content)
        match_empresa = cls.REGEX_EMPRESA.search(content)

        # Validação de campos obrigatórios
        erros = []
        if not match_nome:
            erros.append("\\nomeMunicipio")
        if not match_cnpj:
            erros.append("\\cnpjMunicipio")
        if not match_tel:
            erros.append("\\telefone")
        if not match_email:
            erros.append("\\email")
        if not match_input:
            erros.append("\\input (Concessionária/Estado)")

        if erros:
            raise ValueError(
                f"Campos ausentes no arquivo: {', '.join(erros)}"
            )

        # Resolução do Estado a partir do nome da concessionária no \input
        nome_arquivo_conc = match_input.group(1)
        estado = CONCESSIONARIA_ESTADO_MAP.get(
            nome_arquivo_conc, "Estado Desconhecido"
        )

        # Se não encontrar \empresaResponsavel no .tex, assume string vazia
        empresa_resp = match_empresa.group(1).strip() if match_empresa else ""
        dados_empresa = cls._carregar_dados_empresa(empresa_resp)

        return ClienteMunicipio(
            nome_municipio=match_nome.group(1).strip(),
            estado=estado,
            cnpj=match_cnpj.group(1).strip(),
            telefone=match_tel.group(1).strip(),
            email=match_email.group(1).strip(),
            empresa_responsavel=empresa_resp,
            caminho_arquivo=str(filepath),
            concessionaria=nome_arquivo_conc.replace(".tex", "").replace("_", " "),
            representante_nome=dados_empresa["representante_nome"],
            representante_cnpj=dados_empresa["representante_cnpj"],
            representante_email=dados_empresa["representante_email"],
            representante_telefone=dados_empresa["representante_telefone"],
        )