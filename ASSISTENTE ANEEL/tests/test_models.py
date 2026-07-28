import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from models import ClienteMunicipio


def test_obter_campo_tel_representante():
    cliente = ClienteMunicipio(
        nome_municipio='Teste',
        estado='PB',
        cnpj='123',
        telefone='999',
        email='a@b',
        empresa_responsavel='RUDA',
        caminho_arquivo='x',
    )

    assert cliente.obter_campo('TEL_REPRESENTANTE') == '88981154459'
