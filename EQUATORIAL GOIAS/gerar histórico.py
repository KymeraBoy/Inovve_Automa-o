import re
import pandas as pd
from pathlib import Path

def extrair_dados_fatura(texto):
    """
    Localiza cada consumo faturado no relatório e busca para trás no texto 
    o identificador mais próximo (Unidade Consumidora ou Instalação).
    """
    resultados = []

    # Padrão para localizar a linha de Consumo
    padrao_consumo = re.compile(r'Consumo\s+([\d\.]+,\d{2})', re.IGNORECASE)

    # Busca a Referência Geral no cabeçalho do arquivo (fallback)
    ref_geral_match = re.search(r'REFERÊNCIA:\s*(\d{2}/\d{4})', texto, re.IGNORECASE)
    ref_geral = ref_geral_match.group(1) if ref_geral_match else "N/A"

    # Itera sobre todas as ocorrências de Consumo encontradas no arquivo
    for match in padrao_consumo.finditer(texto):
        pos_consumo = match.start()
        consumo_str = match.group(1)
        consumo_num = float(consumo_str.replace('.', '').replace(',', '.'))

        # Pega todo o texto do início do arquivo até a posição deste consumo
        texto_anterior = texto[:pos_consumo]

        # Busca todas as ocorrências prévias de UC e Instalação
        matches_uc = list(re.finditer(r'UNIDADE CONSUMIDORA:\s*([\d\.-]+)', texto_anterior, re.IGNORECASE))
        matches_inst = list(re.finditer(r'Instalação:\s*(\d+)', texto_anterior, re.IGNORECASE))

        ult_uc = matches_uc[-1] if matches_uc else None
        ult_inst = matches_inst[-1] if matches_inst else None

        pos_uc = ult_uc.start() if ult_uc else -1
        pos_inst = ult_inst.start() if ult_inst else -1

        identificador = None
        tipo_identificador = None

        # Identifica qual tag apareceu mais próxima (imediatamente antes) do consumo
        if pos_uc > pos_inst:
            identificador = ult_uc.group(1).strip()
            tipo_identificador = "UC"
        elif pos_inst > pos_uc:
            identificador = ult_inst.group(1).strip()
            tipo_identificador = "Instalação"

        # Busca a Mês de Referência mais próximo do consumo
        matches_ref = list(re.finditer(r'Referência:\s*(\d{2}/\d{4})', texto_anterior, re.IGNORECASE))
        if matches_ref:
            referencia = matches_ref[-1].group(1)
        else:
            referencia = ref_geral

        # Adiciona aos resultados se encontrou um identificador válido
        if identificador:
            resultados.append({
                "Identificador": identificador,
                "Tipo Identificador": tipo_identificador,
                "Consumo (kWh)": consumo_num,
                "Mês de Referência": referencia
            })

    return resultados


def processar_faturas_na_pasta_do_script():
    """
    Lê todos os arquivos .txt presentes na própria pasta e gera a planilha Excel.
    """
    pasta = Path(__file__).resolve().parent
    arquivos_txt = list(set(pasta.glob('*.txt')).union(set(pasta.glob('*.TXT'))))

    if not arquivos_txt:
        print("Nenhum arquivo .txt encontrado na pasta do script.")
        return

    todos_resultados = []

    for arquivo in arquivos_txt:
        try:
            with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()

            faturas = extrair_dados_fatura(conteudo)
            for fatura in faturas:
                fatura['Arquivo Origem'] = arquivo.name
                todos_resultados.append(fatura)

        except Exception as e:
            print(f"Erro ao processar {arquivo.name}: {e}")

    if todos_resultados:
        df = pd.DataFrame(todos_resultados)

        # Remove eventuais duplicatas exatas se houver
        df = df.drop_duplicates(subset=['Arquivo Origem', 'Identificador', 'Consumo (kWh)', 'Mês de Referência'])

        colunas = [
            'Arquivo Origem',
            'Identificador',
            'Tipo Identificador',
            'Consumo (kWh)',
            'Mês de Referência'
        ]
        df = df[colunas]

        caminho_excel = pasta / "Relatorio_Consumo_Faturas.xlsx"
        df.to_excel(caminho_excel, index=False)
        print(f"Sucesso! Relatório gerado com {len(df)} registro(s) em:\n{caminho_excel}")
    else:
        print("Nenhum dado extraído.")


if __name__ == "__main__":
    processar_faturas_na_pasta_do_script()