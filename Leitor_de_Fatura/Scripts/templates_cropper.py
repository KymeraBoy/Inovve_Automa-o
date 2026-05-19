def recortes(coords):
    coords = tuple(valor * 2.83 for valor in coords)
    return [coords[0], coords[1], coords[0] + coords[2], coords[1] + coords[3]]

# DICIONARIO DE TEMPLATES: coordenadas de corte para cada modelo de fatura
TEMPLATES = {
    "ENEL": {
        "RESUMO": [
            recortes((5.29, 19.41, 81.19, 15.88)),      # DADOS_DO_CLIENTE
            recortes((5.29, 35.65, 135.90, 70.60)),     # VALORES_DO_FATURAMENTO
            recortes((84.72, 213.55, 17.65, 10.59)),    # GRUPO
            recortes((88.25, 19.41, 54.71, 15.88)),     # DATAS
            recortes((142.96, 19.41, 63.54, 75.89))     # VALORES
        ],
        "INDIVIDUAL_FRENTE": [
            recortes((15.88, 24.71, 52.95, 8.82)),      # CLASSIFICACAO_DO_CLIENTE
            recortes((69.89, 24.36, 26.47, 8.82)),      # TIPO_DE_FORNECIMENTO
            recortes((98.13, 24.71, 97.07, 8.82)),      # DATAS_DE_LEITURA
            recortes((69.89, 36.00, 26.47, 20.47)),     # UNIDADE_CONSUMIDORA
            recortes((15.88, 57.89, 80.83, 8.82)),      # TOTAL_A_PAGAR
            recortes((15.88, 34.59, 52.95, 20.47)),     # LOCALIZACAO
            recortes((123.54, 109.07, 33.53, 35.30)),   # TRIBUTOS
            recortes((158.14, 109.07, 37.06, 38.83)),   # CONSUMO
            recortes((15.18, 109.42, 106.95, 82.95)),   # DADOS_DO_FATURAMENTO
        ]
    },
    "ENERGISA": {
        "LAYOUT_1": [
            recortes((2.98, 6.24, 81.14, 8.53)),        # MUNICIPIO
            recortes((4.39, 40.11, 29.71, 11.74)),      # MES DE REFERENCIA
            recortes((4.39, 53.58, 121.44, 6.03)),      # UNDADE CONSUMIDORA
            recortes((2.40, 17.80, 66.19, 6.15)),       # CLASSIFICACAO E NUMERO DE FASES
            recortes((2.40, 189.30, 123.11, 14.83)),    # HISTORICO DE CONSUMO
            recortes((2.40, 100.56, 123.11, 9.79)),     # DADOS DE MEDICAO
            recortes((2.40, 111.86, 125.11, 66.34)),    # DADOS DO FATURAMENTO
        ],
        "LAYOUT_2": [
            recortes((0, 0, 82.81, 11.89)),             # MUNICIPIO
            recortes((7.54, 55.52, 56.61, 11.49)),      # MES DE REFERENCIA
            recortes((66.50, 19.78, 56.73, 12)),        # UNDADE CONSUMIDORA
            recortes((0, 20.62, 65.71, 7.12)),          # CLASSIFICACAO E NUMERO DE FASES
            recortes((0, 158.55, 33.82, 30.41)),        # HISTORICO DE CONSUMO
            recortes((33.82, 162.41, 30.41, 20)),       # DADOS DE MEDICAO
            recortes((0, 96.56, 130.23, 57.47)),        # DADOS DO FATURAMENTO
            recortes((58.59, 196.23, 41.63, 12.41)),    # INDICADORES DE QUALIDADE
        ],
        "LAYOUT_3": [
            recortes((0, 0, 83.37, 11.58)),             # MUNICIPIO
            recortes((7.59, 56.98, 56.36, 12)),         # MES DE REFERENCIA
            recortes((65.55, 20.02, 56.36, 12)),        # UNDADE CONSUMIDORA
            recortes((0, 20.58, 64.89, 6.77)),          # CLASSIFICACAO E NUMERO DE FASES
            recortes((0, 161.76, 33.37, 31.24)),        # HISTORICO DE CONSUMO
            recortes((34.31, 165.47, 30.57, 21.04)),    # DADOS DE MEDICAO
            recortes((0, 98.08, 130.06, 58.31)),        # DADOS DO FATURAMENTO
            recortes((58.77, 199.80, 40.14, 12.51)),    # INDICADORES DE QUALIDADE
        ],
        "LAYOUT_4": [
            recortes((16.13, 53.95, 64.15, 18.73)),     # MUNICIPIO
            recortes((15.74, 83.23, 32.96, 9.00)),      # MES DE REFERENCIA
            recortes((81.19, 60.78, 33.36, 9.74)),      # UNDADE CONSUMIDORA
            recortes((16.13, 41.90, 54.32, 7.97)),      # CLASSIFICACAO
            recortes((70.45, 41.90, 30, 7.97)),         # N DE FASES
            recortes((14.85, 192.35, 85.12, 20.26)),    # DADOS DE MEDICAO
            recortes((9.04, 116.35, 139.92, 75.20)),    # DADOS DO FATURAMENTO
            recortes((150.30, 116.28, 39.86, 19.16)),   # TRIBUTOS
        ],
        "LAYOUT_4_VERSO": [
            recortes((12.61, 52.47, 42.27, 21.88)),     # INDICADORES DE QUALIDADE
            recortes((55.60, 53.21, 132.28, 45.36)),    # HISTORICO DE CONSUMO
        ],
        "LAYOUT_5": [
            recortes((16.13, 17.98, 96.41, 55.99)),     # MUNICIPIO
            recortes((13.80, 100.29, 35.86, 8)),        # MES DE REFERENCIA
            recortes((115.69, 58.86, 50, 9.15)),        # UNDADE CONSUMIDORA
            recortes((10.38, 123.25, 172.65, 80.39)),   # DADOS DO FATURAMENTO
        ],
        "LAYOUT_5_VERSO": [
            recortes((53.58, 54.69, 123.40, 45.33)),    # HISTORICO DE CONSUMO
            recortes((12.61, 52.47, 40, 21.88)),        # INDICADORES DE QUALIDADE
        ],
        "LAYOUT_6": [
            recortes((70.45, 0, 74.72, 16.50)),         # MUNICIPIO
            recortes((10.89, 44.50, 41.60, 14)),        # MES DE REFERENCIA
            recortes((143.06, 44.50, 41.60, 14)),       # UNDADE CONSUMIDORA
            recortes((12.84, 16.32, 58.55, 5.47)),      # CLASSIFICACAO
            recortes((71.19, 21.60, 28.96, 2.72)),      # N DE FASES
            recortes((11.37, 60.67, 174.77, 80.83)),    # DESCRICAO DO FATURAMENTO
        ],
        "LAYOUT_6_VERSO": [
            recortes((13.55, 61.10, 104.06, 40.17)),    # HISTORICO DE CONSUMO
            recortes((138.93, 102.84, 46.97, 29.05)),   # INDICADORES DE QUALIDADE
        ],
        "LAYOUT_7": [
            recortes((5.44, 34.34, 73.51, 15.67)),      # MUNICIPIO
            recortes((7.64, 64.12, 35.03, 7.43)),       # MES DE REFERENCIA
            recortes((81.11, 38.22, 41.62, 9.13)),      # UNDADE CONSUMIDORA
            recortes((6.40, 24.01, 71.29, 6.40)),       # CLASSIFICACAO
            recortes((77.58, 24.01, 44.96, 6.40)),      # TIPO DE FORNECIMENTO
            recortes((3.51, 166.50, 123.06, 45.08)),    # DADOS DO FATURAMENTO
            recortes((64.15, 214.88, 59.24, 21.64)),    # TRIBUTOS
            recortes((7.05, 249.74, 116.15, 14.65)),    # DADOS DE MEDICAO
            recortes((14.01, 218.48, 43.10, 30.04)),    # HISTORICO DE CONSUMO
        ],
        "LAYOUT_7_VERSO": [
            recortes((0, 0, 100, 100)),                 # FILL
        ]
    },
    "NEOENERGIA": {
        "TESTE": [
            recortes((5.68,7.88,198.99,6)),
            recortes((35,80,130,10))
        ],
        "AGRUPADA": [
            recortes((6.00, 42.85, 83.94, 39.92)),      # DADOS DO CLIENTE
            recortes((164.70, 71.90, 30.96, 11.22)),    # MES DE REFERENCIA
            recortes((165.02, 43.03, 30.92, 27.89)),    # CODIGO DA CONTA COMPARTILHADA
        ],
        "INDIVIDUAL_NEW": [
            recortes((4.94, 24.71, 69.89, 22.94)),      # DADOS E ENDERECO (VARIAVEL)
            recortes((5, 48, 25, 7)),     # MÊS DE REFERENCIA (CONSTANTE)
            recortes((74.83, 26.83, 27.89, 19.06)),     # CODIGO (CONSTANTE)
            recortes((4.94, 54.71, 68.83, 7.06)),       # CLASSIFICACAO (CONSTANTE)
            recortes((159.90, 106.60, 44.83, 52.95)),   # HISTORICO DE CONSUMO
            recortes((103.00, 160.85, 16.98, 19.98)),   # CONSUMO
        ],
        "INDIVIDUAL_OLD": [
            recortes((162.02, 33.89, 27.89, 27.89)),    # CODIGO (CONSTANTE)
            recortes((3.88, 33.89, 73.77, 19.06)),      # DADOS (VARIAVEL)
            recortes((3.88, 54.36, 74.13, 18.36)),      # ENDERECO
            recortes((79.77, 62.83, 109.78, 9.88)),     # CLASSIFICACAO (CONSTANTE)
            recortes((153.90, 134.49, 35.30, 52.95)),   # HISTORICO DE CONSUMO
            recortes((103.00, 192.49, 24.17, 15.45)),   # CONSUMO
        ]
    }   
}
