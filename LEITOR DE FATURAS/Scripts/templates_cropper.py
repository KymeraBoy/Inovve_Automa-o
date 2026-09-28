def recortes(coords):
    coords = tuple(valor * 2.83 for valor in coords)
    return [coords[0], coords[1], coords[0] + coords[2], coords[1] + coords[3]]

# DICIONARIO DE TEMPLATES: coordenadas de corte para cada modelo de fatura
TEMPLATES = {
    "ENEL": {
        "RESUMO": [
            [14.9707, 54.9303, 244.7384, 99.8707],     # DADOS_DO_CLIENTE
            [14.9707, 100.8895, 399.5657, 300.6895],   # VALORES_DO_FATURAMENTO
            [239.7576, 604.3465, 289.7081, 634.3161],  # GRUPO
            [249.7455, 54.9303, 404.5713, 99.8707],    # DATAS
            [404.5868, 54.9303, 584.4066, 269.6993],   # VALORES
        ],
        "INDIVIDUAL_FRENTE": [
            [44.9404, 69.9293, 194.7889, 94.8889],     # CLASSIFICACAO_DO_CLIENTE
            [197.7887, 68.9388, 272.7081, 93.8988],    # TIPO_DE_FORNECIMENTO
            [277.7079, 69.9293, 552.4161, 94.8889],    # DATAS_DE_LEITURA
            [197.7887, 101.88, 272.7081, 159.8099],    # UNIDADE_CONSUMIDORA
            [44.9404, 163.8287, 273.6893, 188.7887],   # TOTAL_A_PAGAR
            [44.9404, 97.8897, 194.7889, 155.8197],    # LOCALIZACAO
            [349.6182, 308.6681, 444.5081, 408.5661],  # TRIBUTOS
            [447.5362, 308.6681, 552.4162, 418.5569],  # CONSUMO
            [42.9594, 309.6586, 345.6279, 544.4221],   # DADOS_DO_FATURAMENTO
        ],
    },
    "ENERGISA": {
        "L1": [
            [0.0, 0.0, 195.27, 90.56],                 # DOMICILIO, CLIENTE, SUBGRUPO, CLASSE, MEDIDOR E FORNECIMENTO
            [0.0, 107.54, 367.9, 608.51],              # BLOCO PRINCIPAL
            [0.0, 611.28, 215.08, 716.01],             # INDICADORES DE QUALIDADE
            [215.08, 611.28, 367.9, 716.01],           # COMPOSICAO DO CONSUMO
            [0.0, 713.16, 274.51, 826.36],             # ATENCAO
            [274.51, 713.16, 367.9, 826.36],            # FATURAS EM ATRASO
            [0.0, 832.02, 367.9, 945.22],              # DADOS FISCAIS
        ],
        "L2": [
            [0.0, 0.0, 234.3523, 87.73],               # MUNICIPIO, CLASSIFICACAO E FASES
            [188.195, 55.9774, 348.7409, 89.9374],     # UNIDADE CONSUMIDORA
            [21.3382, 113.2, 181.5345, 188.1167],      # REFERENCIA E VALOR DA FATURA
            [183.95, 113.2, 344.1463, 188.1167],       # VENCIMENTO E CONSUMO
            [0.0, 192.44, 359.41, 263.25],             # SITUACAO DE DEBITOS
            [183.95, 447.14, 362.24, 546.29],          # COMPOSICAO DO CONSUMO
            [0.0, 448.6965, 95.7106, 534.7568],        # HISTORICO DE CONSUMO
            [95.7106, 459.6203, 181.7709, 516.2203],   # DADOS DE MEDICAO
            [0.0, 273.2648, 368.5511, 435.8949],       # DADOS DO FATURAMENTO
            [0.0, 555.3309, 283.6226, 590.4512],       # INDICADORES DE QUALIDADE
            [0.0, 588.64, 367.9, 747.12],              # ATENCAO
            [0.0, 755.61, 367.9, 914.09],              # DADOS FISCAIS
        ],
        "L3": [
            [0.0, 0.0, 189.61, 93.39],                 # MUNICIPIO, CNPJ, MEDIDOR, FORNECIMENTO E CLASSE
            [0.0, 113.2, 175.46, 192.54],              # REFERENCIA E VALOR DA FATURA
            [175.46, 113.2, 350.92, 192.54],           # VENCIMENTO E CONSUMO
            [0.0, 198.1, 367.9, 274.51],               # SITUACAO DE DEBITOS
            [185.5065, 56.6566, 345.0063, 90.6166],    # UNIDADE CONSUMIDORA
            [183.95, 455.63, 365.07, 551.95],          # COMPOSICAO DO CONSUMO
            [0.0, 457.7808, 94.4371, 546.1908],        # HISTORICO DE CONSUMO
            [97.0973, 468.2801, 183.6102, 527.8201],   # DADOS DE MEDICAO
            [0.0, 277.5664, 368.0698, 442.6937],       # DADOS DO FATURAMENTO
            [0.0, 565.434, 279.9153, 600.8373],        # INDICADORES DE QUALIDADE
            [0.0, 599.96, 367.9, 758.44],              # ATENCAO
            [0.0, 911.26, 367.9, 1052.7],              # DADOS FISCAIS
        ],
        "L4": [
            [37.8654, 50.94, 372.1354, 113.22],        # DOMICILIO DE ENTREGA
            [37.8654, 110.37, 372.1354, 135.84],       # CLASSIFICACAO E FORNECIMENTO
            [37.8654, 147.16, 227.4254, 232.06],       # CLIENTE
            [37.8654, 232.06, 326.5254, 268.85],       # MES/ANO, VENCIMENTO E VALOR
            [37.8654, 271.68, 533.2154, 328.28],       # INFORMACOES
            [0.0, 325.45, 424.5, 543.36],              # ITENS DA FATURA
            [0.0, 540.53, 314.13, 599.96],             # DADOS DE MEDICAO
            [0.0, 597.13, 532.04, 755.61],             # DADOS FISCAIS
            [373.56, 50.94, 532.04, 135.84],           # APRESENTACAO
            [328.28, 141.5, 532.04, 181.12],           # DATAS DE LEITURA
            [226.4, 181.12, 325.45, 234.89],           # CODIGO DO CLIENTE E INSTALACAO
            [424.5, 325.45, 537.7, 379.22],            # IMPOSTOS
            [424.5, 384.88, 537.7, 537.7],             # HISTORICO DE CONSUMO
            [314.13, 537.7, 532.04, 597.13],           # RESERVADO AO FISCO
        ],
        "L4_VERSO": [
            [33.96, 16.98, 333.94, 147.16],            # ATENCAO
            [33.96, 152.82, 155.65, 291.49],           # INDICADORES DE QUALIDADE
            [33.96, 288.66, 181.12, 447.14],           # COMPOSICAO DO CONSUMO
            [339.6, 16.98, 529.21, 147.16],            # SITUACAO DE DEBITOS
            [158.48, 152.82, 526.38, 291.49],          # CONSUMO DOS ULTIMOS 13 MESES
            [183.95, 288.66, 529.21, 447.14],          # ESTRUTURA DO CONSUMO
        ],
        "L5": [
            [25.47, 42.45, 314.13, 254.7],             # DOMICILIO DE ENTREGA E CLIENTE
            [325.45, 164.14, 469.78, 198.1],           # UNIDADE CONSUMIDORA
            [25.47, 251.87, 144.33, 350.92],           # VALOR, REFERENCIA E CNPJ
            [147.16, 251.87, 288.66, 350.92],          # VENCIMENTO, CONSUMO E RESERVADO AO FISCO
            [283.0, 251.87, 517.89, 311.3],            # SITUACAO DE DEBITOS
            [283.0, 311.3, 546.19, 350.92],            # DATAS DE EMISSAO/APRESENTACAO/PROXIMA LEITURA
            [25.47, 348.09, 515.06, 574.49],           # DESCRITIVO
            [25.47, 577.32, 515.06, 778.25],           # INFORMACOES FISCAIS
        ],
        "L5_VERSO": [
            [33.96, 16.98, 316.96, 147.16],            # ATENCAO
            [33.96, 152.82, 150.0, 291.49],            # INDICADORES DE QUALIDADE
            [33.96, 288.66, 171.215, 447.14],          # COMPOSICAO DO CONSUMO
            [311.3, 16.98, 500.91, 147.16],            # CANAL DE CONTATO
            [147.16, 152.82, 515.06, 291.49],          # CONSUMO DOS ULTIMOS 13 MESES
            [169.8, 288.66, 515.06, 447.14],           # ESTRUTURA DO CONSUMO
        ],
        "L6": [
            [28.3, 0.0, 198.1, 96.22],                 # DOMICILIO DE ENTREGA
            [192.44, 0.0, 413.18, 96.22],              # CLIENTE
            [28.3, 110.37, 548.83, 164.14],            # REFERENCIA/APRESENTACAO/PROXIMA LEITURA/UC
            [28.3, 169.8, 548.83, 399.03],             # DEMONSTRATIVO
            [28.3, 401.86, 203.76, 523.55],            # COMPOSICAO DO CONSUMO
            [195.27, 401.86, 537.7, 523.55],           # VENCIMENTO, TOTAL E RESERVADO AO FISCO
            [28.3, 537.7, 548.83, 752.78],             # DADOS FISCAIS
        ],
        "L6_VERSO": [
            [28.3, 0.0, 223.57, 144.33],               # CANAL DE CONTATO
            [28.3, 155.65, 390.54, 291.49],            # CONSUMO DOS ULTIMOS 12 MESES
            [28.3, 305.64, 393.37, 441.48],            # ESTRUTURA DO CONSUMO
            [215.08, 0.0, 305.64, 144.33],             # FATURAS EM ATRASO
            [308.47, 0.0, 517.89, 144.33],             # ATENCAO
            [393.37, 288.66, 512.23, 444.31],          # INDICADORES DE QUALIDADE
        ],
        "L7": [
            [15.3952, 97.1822, 223.4185, 173.5622],    # MUNICIPIO
            [21.6212, 181.4596, 310.2812, 202.4865],   # REFERENCIA, VENCIMENTO E TOTAL
            [229.5413, 108.1626, 347.3269, 164.7626],  # UNIDADE CONSUMIDORA E CODIGO DA INSTALACAO
            [18.112, 67.9483, 219.8627, 86.0683],      # CLASSIFICACAO
            [219.5514, 67.9483, 346.7882, 86.0683],    # TIPO DE FORNECIMENTO
            [0.0, 308.47, 367.9, 413.18],              # INFORMACOES
            [0.0, 415.99, 367.9, 458.46],              # DATAS DE LEITURA
            [9.9333, 468.365, 358.2929, 601.5014],     # DADOS DO FATURAMENTO
            [181.5445, 608.1104, 349.1937, 669.3412],  # TRIBUTOS
            [19.9515, 706.7642, 348.656, 756.7187],    # DADOS DE MEDICAO
            [39.6483, 618.2984, 161.6263, 703.3116],   # HISTORICO DE CONSUMO
            [189.61, 667.88, 359.41, 696.18],          # RESERVADO AO FISCO
            [0.0, 752.78, 367.9, 826.36],              # SITUACAO DE DEBITOS
            [0.0, 826.36, 367.9, 959.37],              # DADOS FISCAIS
        ],
        "L7_VERSO": [
            [0.0, 0.0, 283.0, 283.0],                  # FILL
        ],
    },
    "NEOENERGIA": {
        "TESTE": [
            [16.0744, 22.3004, 579.2161, 39.2804],
            [99.05, 226.4, 467.0, 254.7],
        ],
        "AGRUPADA": [
            [16.98, 121.2655, 254.5302, 234.3391],     # DADOS DO CLIENTE
            [466.101, 203.477, 553.7178, 235.2294],    # MES DE REFERENCIA
            [467.0066, 121.7749, 554.5102, 200.7242],  # CODIGO DA CONTA COMPARTILHADA
        ],
        "INDIVIDUAL_NEW": [
            [13.9802, 69.9293, 211.7689, 134.8495],    # DADOS E ENDERECO (VARIAVEL)
            [14.15, 135.84, 84.9, 155.65],             # MES DE REFERENCIA (CONSTANTE)
            [211.7689, 75.9289, 290.6976, 129.8589],   # CODIGO (CONSTANTE)
            [13.9802, 154.8293, 208.7689, 174.8093],   # CLASSIFICACAO (CONSTANTE)
            [368.55, 158.48, 580.85, 172.63],          # FORNECIMENTO (CONSTANTE)
            [14.15, 455.63, 339.6, 512.23],            # MEDIDOR
            [291.49, 455.63, 339.6, 512.23],           # CONSUMO
            [452.517, 301.678, 579.3859, 451.5285],    # HISTORICO DE CONSUMO
            [14.15, 232.06, 450.57, 452.8],            # ITENS DA FATURA
        ],
        "INDIVIDUAL_OLD": [
            [458.5166, 95.9087, 537.4453, 174.8087],   # CODIGO (CONSTANTE)
            [10.9804, 95.9087, 219.7508, 149.8287],    # DADOS (VARIAVEL)
            [10.9804, 153.8388, 220.7683, 205.7988],   # ENDERECO
            [225.7491, 177.8089, 536.4263, 205.7695],  # CLASSIFICACAO (CONSTANTE)
            [11.32, 718.82, 336.77, 749.95],           # DADOS DE COBRANÇA           
            [11.32, 254.7, 271.68, 486.76],            # ITENS DA FATURA
            [291.49, 544.9165, 339.6, 588.7815],       # CONSUMO
            [435.537, 380.6067, 535.436, 530.4552],    # HISTORICO DE CONSUMO 
        ],
    },
}