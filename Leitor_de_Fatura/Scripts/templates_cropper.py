def recortes(coords):
    coords = tuple(valor * 2.83 for valor in coords)
    return [coords[0], coords[1], coords[0] + coords[2], coords[1] + coords[3]]

# DICIONARIO DE TEMPLATES: coordenadas de corte para cada modelo de fatura
TEMPLATES = {
    "ENEL": {
        "RESUMO": [
            recortes((5.29, 19.41, 81.19, 15.88)),    # DADOS_DO_CLIENTE
            recortes((5.29, 35.65, 135.90, 70.60)),   # VALORES_DO_FATURAMENTO
            recortes((84.72, 213.55, 17.65, 10.59)),  # GRUPO
            recortes((88.25, 19.41, 54.71, 15.88)),   # DATAS
            recortes((142.96, 19.41, 63.54, 75.89)),  # VALORES
        ],
        "INDIVIDUAL_FRENTE": [
            recortes((15.88, 24.71, 52.95, 8.82)),    # CLASSIFICACAO_DO_CLIENTE
            recortes((69.89, 24.36, 26.47, 8.82)),    # TIPO_DE_FORNECIMENTO
            recortes((98.13, 24.71, 97.07, 8.82)),    # DATAS_DE_LEITURA
            recortes((69.89, 36.00, 26.47, 20.47)),   # UNIDADE_CONSUMIDORA
            recortes((15.88, 57.89, 80.83, 8.82)),    # TOTAL_A_PAGAR
            recortes((15.88, 34.59, 52.95, 20.47)),   # LOCALIZACAO
            recortes((123.54, 109.07, 33.53, 35.30)), # TRIBUTOS
            recortes((158.14, 109.07, 37.06, 38.83)), # CONSUMO
            recortes((15.18, 109.42, 106.95, 82.95)), # DADOS_DO_FATURAMENTO
        ],
    },
    "ENERGISA": {
        "LAYOUT_1": [
            recortes((0, 0, 69, 32)),      # DOMICILIO, CLIENTE, SUBGRUPO, CLASSE, MEDIDOR E FORNECIMENTO
            recortes((0, 38, 130, 177)),   # BLOCO PRINCIPAL
            recortes((0, 216, 76, 37)),    # INDICADORES DE QUALIDADE
            recortes((76, 216, 54, 37)),   # COMPOSICAO DO CONSUMO
            recortes((0, 252, 97, 40)),    # ATENCAO
            recortes((97, 252, 33, 40)),   # FATURAS EM ATRASO
            recortes((0, 294, 130, 40)),   # DADOS FISCAIS
        ],
        "LAYOUT_2": [
            recortes((0, 0, 82.81, 31)),            # MUNICIPIO, CLASSIFICACAO E FASES
            recortes((66.50, 19.78, 56.73, 12)),    # UNIDADE CONSUMIDORA
            recortes((7.54, 40, 56.61, 26.49)),     # REFERENCIA E VALOR DA FATURA
            recortes((65, 40, 56.61, 26.49)),       # VENCIMENTO E CONSUMO
            recortes((0, 68, 127, 25)),             # SITUACAO DE DEBITOS
            recortes((65, 158, 63, 35)),            # COMPOSICAO DO CONSUMO
            recortes((0, 158.55, 33.82, 30.41)),    # HISTORICO DE CONSUMO
            recortes((33.82, 162.41, 30.41, 20)),   # DADOS DE MEDICAO
            recortes((0, 96.56, 130.23, 57.47)),    # DADOS DO FATURAMENTO
            recortes((0, 196.23, 100.22, 12.41)),   # INDICADORES DE QUALIDADE
            recortes((0, 208, 130, 56)),            # ATENCAO
            recortes((0, 267, 130, 56)),            # DADOS FISCAIS
        ],
        "LAYOUT_3": [
            recortes((0, 0, 67, 33)),               # MUNICIPIO, CNPJ, MEDIDOR, FORNECIMENTO E CLASSE
            recortes((0, 40, 62, 28)),              # REFERENCIA E VALOR DA FATURA
            recortes((62, 40, 62, 28)),             # VENCIMENTO E CONSUMO
            recortes((0, 70, 130, 27)),             # SITUACAO DE DEBITOS
            recortes((65.55, 20.02, 56.36, 12)),    # UNIDADE CONSUMIDORA
            recortes((65, 161, 64, 34)),            # COMPOSICAO DO CONSUMO
            recortes((0, 161.76, 33.37, 31.24)),    # HISTORICO DE CONSUMO
            recortes((34.31, 165.47, 30.57, 21.04)),# DADOS DE MEDICAO
            recortes((0, 98.08, 130.06, 58.31)),    # DADOS DO FATURAMENTO
            recortes((0, 199.80, 98.91, 12.51)),    # INDICADORES DE QUALIDADE
            recortes((0, 212, 130, 56)),            # ATENCAO
            recortes((0, 322, 130, 50)),            # DADOS FISCAIS
        ],
        "LAYOUT_4": [
            recortes((13.38, 18, 118, 22)),   # DOMICILIO DE ENTREGA
            recortes((13.38, 39, 118, 9)),    # CLASSIFICACAO E FORNECIMENTO
            recortes((13.38, 52, 67, 30)),    # CLIENTE
            recortes((13.38, 82, 102, 13)),   # MES/ANO, VENCIMENTO E VALOR
            recortes((13.38, 96, 175, 20)),   # INFORMACOES
            recortes((0, 115, 150, 77)),      # ITENS DA FATURA
            recortes((0, 191, 111, 21)),      # DADOS DE MEDICAO
            recortes((0, 211, 188, 56)),      # DADOS FISCAIS
            recortes((132, 18, 56, 30)),      # APRESENTACAO
            recortes((116, 50, 72, 14)),      # DATAS DE LEITURA
            recortes((80, 64, 35, 19)),       # CODIGO DO CLIENTE E INSTALACAO
            recortes((150, 115, 40, 19)),     # IMPOSTOS
            recortes((150, 136, 40, 54)),     # HISTORICO DE CONSUMO
            recortes((111, 190, 77, 21)),     # RESERVADO AO FISCO
        ],
        "LAYOUT_4_VERSO": [
            recortes((12, 6, 106, 46)),     # ATENCAO
            recortes((12, 54, 43, 49)),     # INDICADORES DE QUALIDADE
            recortes((12, 102, 52, 56)),    # COMPOSICAO DO CONSUMO
            recortes((120, 6, 67, 46)),     # SITUACAO DE DEBITOS
            recortes((56, 54, 130, 49)),    # CONSUMO DOS ULTIMOS 13 MESES
            recortes((65, 102, 122, 56)),   # ESTRUTURA DO CONSUMO
        ],
        "LAYOUT_5": [
            recortes((9, 15, 102, 75)),      # DOMICILIO DE ENTREGA E CLIENTE
            recortes((115, 58, 51, 12)),     # UNIDADE CONSUMIDORA
            recortes((9, 89, 42, 35)),       # VALOR, REFERENCIA E CNPJ
            recortes((52, 89, 50, 35)),      # VENCIMENTO, CONSUMO E RESERVADO AO FISCO
            recortes((100, 89, 83, 21)),     # SITUACAO DE DEBITOS
            recortes((100, 110, 93, 14)),    # DATAS DE EMISSAO/APRESENTACAO/PROXIMA LEITURA
            recortes((9, 123, 173, 80)),     # DESCRITIVO
            recortes((9, 204, 173, 71)),     # INFORMACOES FISCAIS
        ],
        "LAYOUT_5_VERSO": [
            recortes((12, 6, 100, 46)),     # ATENCAO
            recortes((12, 54, 41, 49)),     # INDICADORES DE QUALIDADE
            recortes((12, 102, 48.5, 56)),  # COMPOSICAO DO CONSUMO
            recortes((110, 6, 67, 46)),     # CANAL DE CONTATO
            recortes((52, 54, 130, 49)),    # CONSUMO DOS ULTIMOS 13 MESES
            recortes((60, 102, 122, 56)),   # ESTRUTURA DO CONSUMO
        ],
        "LAYOUT_6": [
            recortes((10, 0, 60, 34)),       # DOMICILIO DE ENTREGA
            recortes((68, 0, 78, 34)),       # CLIENTE
            recortes((10, 39, 184, 19)),     # REFERENCIA/APRESENTACAO/PROXIMA LEITURA/UC
            recortes((10, 60, 184, 81)),     # DEMONSTRATIVO
            recortes((10, 142, 62, 43)),     # COMPOSICAO DO CONSUMO
            recortes((69, 142, 121, 43)),    # VENCIMENTO, TOTAL E RESERVADO AO FISCO
            recortes((10, 190, 184, 76)),    # DADOS FISCAIS
        ],
        "LAYOUT_6_VERSO": [
            recortes((10, 0, 69, 51)),      # CANAL DE CONTATO
            recortes((10, 55, 128, 48)),    # CONSUMO DOS ULTIMOS 12 MESES
            recortes((10, 108, 129, 48)),   # ESTRUTURA DO CONSUMO
            recortes((76, 0, 32, 51)),      # FATURAS EM ATRASO
            recortes((109, 0, 74, 51)),     # ATENCAO
            recortes((139, 102, 42, 55)),   # INDICADORES DE QUALIDADE
        ],
        "LAYOUT_7": [
            recortes((5.44, 34.34, 73.51, 27)),       # MUNICIPIO
            recortes((7.64, 64.12, 102, 7.43)),       # REFERENCIA, VENCIMENTO E TOTAL
            recortes((81.11, 38.22, 41.62, 20)),      # UNIDADE CONSUMIDORA E CODIGO DA INSTALACAO
            recortes((6.40, 24.01, 71.29, 6.40)),     # CLASSIFICACAO
            recortes((77.58, 24.01, 44.96, 6.40)),    # TIPO DE FORNECIMENTO
            recortes((0, 109, 130, 37)),              # INFORMACOES
            recortes((0, 147, 130, 15)),              # DATAS DE LEITURA
            recortes((3.51, 165.50, 123.06, 47.08)),  # DADOS DO FATURAMENTO
            recortes((64.15, 214.88, 59.24, 21.64)),  # TRIBUTOS
            recortes((7.05, 249.74, 116.15, 17.65)),  # DADOS DE MEDICAO
            recortes((14.01, 218.48, 43.10, 30.04)),  # HISTORICO DE CONSUMO
            recortes((67, 236, 60, 10)),              # RESERVADO AO FISCO
            recortes((0, 266, 130, 26)),              # SITUACAO DE DEBITOS
            recortes((0, 292, 130, 47)),              # DADOS FISCAIS
        ],
        "LAYOUT_7_VERSO": [
            recortes((0, 0, 100, 100)), # FILL
        ],
    },
    "NEOENERGIA": {
        "TESTE": [
            recortes((5.68, 7.88, 198.99, 6)),
            recortes((35, 80, 130, 10)),
        ],
        "AGRUPADA": [
            recortes((6.00, 42.85, 83.94, 39.92)),    # DADOS DO CLIENTE
            recortes((164.70, 71.90, 30.96, 11.22)),  # MES DE REFERENCIA
            recortes((165.02, 43.03, 30.92, 27.89)),  # CODIGO DA CONTA COMPARTILHADA
        ],
        "INDIVIDUAL_NEW": [
            recortes((4.94, 24.71, 69.89, 22.94)),    # DADOS E ENDERECO (VARIAVEL)
            recortes((5, 48, 25, 7)),                 # MES DE REFERENCIA (CONSTANTE)
            recortes((74.83, 26.83, 27.89, 19.06)),   # CODIGO (CONSTANTE)
            recortes((4.94, 54.71, 68.83, 7.06)),     # CLASSIFICACAO (CONSTANTE)
            recortes((130,56,5,75)),                  # FORNECIMENTO (CONSTANTE)
            recortes((5,161,115,20)),                 # MEDIDOR
            recortes((159.90, 106.60, 44.83, 52.95)), # HISTORICO DE CONSUMO
            recortes((5,82,154,78)),                  # ITENS DA FATURA
        ],
        "INDIVIDUAL_OLD": [
            recortes((162.02, 33.89, 27.89, 27.89)),  # CODIGO (CONSTANTE)
            recortes((3.88, 33.89, 73.77, 19.06)),    # DADOS (VARIAVEL)
            recortes((3.88, 54.36, 74.13, 18.36)),    # ENDERECO
            recortes((79.77, 62.83, 109.78, 9.88)),   # CLASSIFICACAO (CONSTANTE)
            recortes((153.90, 134.49, 35.30, 52.95)), # HISTORICO DE CONSUMO
            recortes((103.00, 192.49, 24.17, 15.45)), # CONSUMO
            recortes((4,90,92,82)), # ITENS DA FATURA
            recortes((4,254,115,11)), # DADOS DE COBRANÇA
        ],
    },
}
