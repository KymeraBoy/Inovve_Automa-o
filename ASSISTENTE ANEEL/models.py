"""
Módulo de Modelos de Dados.
Representa a entidade principal do módulo cadastral.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ClienteMunicipio:
    """Representa os dados cadastrais extraídos de um município/cliente."""

    nome_municipio: str
    estado: str
    cnpj: str
    telefone: str
    email: str
    empresa_responsavel: str
    caminho_arquivo: str
    concessionaria: str = ""
    representante_nome: str = ""
    representante_cnpj: str = ""
    representante_email: str = ""
    representante_telefone: str = ""

    @property
    def nome_formatado(self) -> str:
        """Retorna o nome padronizado para preenchimento na ANEEL."""
        return f"Prefeitura Municipal de {self.nome_municipio} - {self.estado}"

    @property
    def telefone_representante(self) -> str:
        """Mapeia o telefone do representante conforme a empresa responsável."""
        if self.representante_telefone:
            return self.representante_telefone

        empresa = self.empresa_responsavel.upper().strip()

        # Lógica condicional da empresa
        if empresa == "RUDA":
            return "88981154459"

        # Caso futuramente adicione outras empresas, basta acrescentar aqui:
        # elif empresa == "OUTRA_EMPRESA":
        #     return "88900000000"

        return ""  # Valor padrão/vazio caso a empresa não seja reconhecida
    
    def obter_campo(self, campo: str) -> Optional[str]:
        """Retorna dinamicamente o valor de um campo baseado na chave."""
        mapa_campos = {
            "NOME": self.nome_formatado,
            "CNPJ": self.cnpj,
            "TELEFONE": self.telefone,
            "EMAIL": self.email,
            "NOME_REPRESENTANTE": self.representante_nome,
            "NOME_DO_REPRESENTANTE": self.representante_nome,
            "REPRESENTANTE": self.representante_nome,
            "CNPJ_REPRESENTANTE": self.representante_cnpj,
            "CNPJ_DO_REPRESENTANTE": self.representante_cnpj,
            "EMAIL_REPRESENTANTE": self.representante_email,
            "EMAIL_DO_REPRESENTANTE": self.representante_email,
            "TEL_REPRESENTANTE": self.telefone_representante,
            "TELEFONE_REPRESENTANTE": self.telefone_representante,
        }
        return mapa_campos.get(campo.upper())