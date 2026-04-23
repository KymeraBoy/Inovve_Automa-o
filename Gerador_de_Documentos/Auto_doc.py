import os
import json

# Vetor de concessionárias
concessionarias = [
    {'nome': 'CELPE', 'linha': ' \\textbf{À COMPANHIA DE ELETRICIDADE DO ESTADO DE PERNAMBUCO (CELPE) – CNPJ: 10.835.932/0001-08}'}
]

# Vetores para elaboração da linha de assunto

tipos_de_cobranca_indevida = [
    "Ausência Benefício Tarifário",
    "Ausência de atualização de demanda",
    "Ausência de medição",
    "Ausência parcela DIC/2",
    "Ausência parcela DIC/2 no TOI censo",
    "Bandeira tarifária TOI censo",
    "CNR x Follow UP",
    "Condominios TOI censo",
    "Consumo atípico",
    "Custo de disponibilidade",
    "Defesa TOI censo",
    "Defesa TOI comum",
    "Descumprimento REH 2590/2019",
    "Duplicidade no faturamento",
    "Duplicidade no pagamento",
    "Enquadramento AES",
    "Enquadramento AES já corrigido",
    "Enquadramento IP",
    "Enquadramento IP censo",
    "Enquadramento IP já corrigido",
    "Faturamento a maior IP estimada",
    "Faturamento por média",
    "ICMS na demanda de ultrapassagem",
    "ICMS sobre a demanda não utilizada",
    "IP estimada",
    "IR",
    "Isenção ICMS",
    "Lâmpadas acesas 24h",
    "Limites territoriais",
    "Perdas a quente",
    "Perdas de transformação",
    "Perdas nos reatores",
    "Perdas nos reatores TOI censo",
    "QIP divergente com a fatura",
    "Quantidade de reatores",
    "Relés fotoelétricos",
    "Tarifa B4A",
    "Taxa de administração CIP",
    "UC não pertencente ao município"
]

tipos_de_solicitacao = [
    "Copia",
    "Devolução",
    "Documento",
    "Histórico",
    "Informação",
    "Alteração cadastral",
    "Comprovante de devolução",    
    "Inclusão na lista de e-mail",    
    "Memorial de cálculo",
    "Reabertura de protocolo na Aneel",
    "Sistema de informação geográfica"
]

copia = [
    "Contrato",
    "Faturas",
    "Levantamento cadastral IP",
    "Contrato da IP",
    "Contrato de convênio CIP"
]

devolucao = [
    "10 anos",
    "Dobro"
]

documento = [
    "Prédios Públicos",
    "Relatório de dívidas",
    "Relatório de pagamentos de TOI",
    "Relatórios de pagamentos",
    "Documentos e informações"
]

historico = [
    "B4A",
    "Demandas"
]

informacao = [
    "Censo",
    "Contratos de parcelamentos",
    "Dados da CIP",
    "Faturamento IP",
    "Fatura",
    "QIP",
    "Taxa adm CIP",
    "TOI",
    "Indicadores de qualidade"
]

fluxo_administrativo = {
    "pergunta": "Qual a natureza do documento?",
        "opcoes": {
            "Cobrança indevida": {
                "pergunta": "Especifique o tipo de cobrança indevida:",
                "opcoes": tipos_de_cobranca_indevida
            },
            "Contestação": {
                "pergunta": "Especifique o tipo de contestação:",
                "opcoes": ["Cobrança Indevida", "Memorial de calculo"]
            },
            "Solicitação": {
                "pergunta": "Especifique o tipo de solicitação:",
                "opcoes": tipos_de_solicitacao
            },
            "Descumprimento de prazos comerciais": {
                "pergunta": "Detalhes:",
                "opcoes": ["Detalhe 1", "Detalhe 2"]  # Placeholder
            },
            "Devolução incorreta de cobrança indevida": {
                "pergunta": "Detalhes:",
                "opcoes": ["Detalhe 1", "Detalhe 2"]  # Placeholder
            },
            "Questionamentos relatório de dívidas": {
                "pergunta": "Detalhes:",
                "opcoes": ["Detalhe 1", "Detalhe 2"]  # Placeholder
            }
        }
    
    
}

def percorrer_fluxo(fluxo):
    if 'pergunta' in fluxo:
        if isinstance(fluxo['opcoes'], list):
            opcoes = fluxo['opcoes']
            print(fluxo['pergunta'])
            for i, op in enumerate(opcoes, 1):
                print(f"{i}. {op}")
            opcao = input("Digite o número da opção: ").strip()
            if opcao.isdigit() and 1 <= int(opcao) <= len(opcoes):
                choice = opcoes[int(opcao) - 1]
                return [choice]
            else:
                return []
        else:  # opcoes is dict
            print(fluxo['pergunta'])
            opcoes = list(fluxo['opcoes'].keys())
            for i, op in enumerate(opcoes, 1):
                print(f"{i}. {op}")
            opcao = input("Digite o número da opção: ").strip()
            if opcao.isdigit() and 1 <= int(opcao) <= len(opcoes):
                choice = opcoes[int(opcao) - 1]
                sub = fluxo['opcoes'][choice]
                if isinstance(sub, dict) and 'pergunta' in sub:
                    sub_result = percorrer_fluxo(sub)
                    return [choice] + sub_result if sub_result else []
                elif isinstance(sub, list):
                    if sub:
                        print("Escolha a subopção:")
                        for i, s in enumerate(sub, 1):
                            print(f"{i}. {s}")
                        sub_op = input("Digite o número: ").strip()
                        if sub_op.isdigit() and 1 <= int(sub_op) <= len(sub):
                            return [choice, sub[int(sub_op) - 1]]
                        else:
                            return []
                    else:
                        return [choice]
                else:
                    return [choice]
            else:
                return []
    return []

def escolher_opcoes():
    print("Opções disponíveis:")
    print("1. Requerimento")
    print("2. Reclamação")
    print("3. Relatório de pagamento")
    opcao = input("Digite o número da opção desejada: ").strip()
    if opcao == "1":
        tipo = "requerimento"
    elif opcao == "2":
        tipo = "reclamação"
    elif opcao == "3":
        tipo = "relatório de pagamento"
    else:
        print("Opção inválida.")
        return None, None, None, None, None, None, None
    
    municipio = input("Digite o município: ").strip()
    municipio = municipio.upper()
    
    while True:
        contagem = input("Digite a contagem do documento: ").strip()
        if contagem.isdigit() and 1 <= len(contagem) <= 3:
            contagem = contagem.zfill(3)
            break
        else:
            print("Número inválido. Digite um número de 1 a 3 dígitos.")
    
    if tipo == "reclamação":
        uc = input("Digite o número da unidade consumidora: ").strip()
        uc_line = f"\\noindent \\textbf{{UNIDADE CONSUMIDORA: {uc}}}"
    elif tipo == "requerimento":
        incluir_uc = input("Deseja incluir a unidade consumidora? (s/n): ").strip().lower()
        if incluir_uc == "s":
            uc = input("Digite o número da unidade consumidora: ").strip()
            uc_line = f"\\noindent \\textbf{{UNIDADE CONSUMIDORA: {uc}}}"
        else:
            uc = ""
            uc_line = ""
    else:
        uc = ""
        uc_line = ""
    
    print("Concessionárias disponíveis:")
    for i, conc in enumerate(concessionarias, 1):
        print(f"{i}. {conc['nome']}")
    opcao_conc = input("Digite o número da concessionária: ").strip()
    if opcao_conc.isdigit() and 1 <= int(opcao_conc) <= len(concessionarias):
        conc_escolhida = concessionarias[int(opcao_conc) - 1]
        concessionaria_linha = conc_escolhida['linha']
    else:
        print("Opção inválida.")
        return None, None, None, None, None, None, None
    
    # Elaboração da linha de assunto percorrendo o fluxo administrativo
    if tipo == "relatório de pagamento":
        assunto = "RELATÓRIO DE PAGAMENTO"
    else:
        result = percorrer_fluxo(fluxo_administrativo)
        if result:
            assunto = f"{tipo.upper()} – {' – '.join([r.title() for r in result])}" + (' – UC ' + uc if uc else '')
        else:
            print("Seleção cancelada.")
            return None, None, None, None, None, None, None
    
    return tipo, municipio, contagem, uc, uc_line, concessionaria_linha, assunto

# Uso da função
tipo, municipio, contagem, uc, uc_line, concessionaria_linha, assunto = escolher_opcoes()
if tipo and municipio and contagem is not None and uc is not None and uc_line is not None and concessionaria_linha and assunto:
    # Caminho para o arquivo LaTeX template
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ler banco de dados
    database_file = os.path.join(script_dir, 'Database.tex')
    with open(database_file, 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    if municipio in database:
        dados_municipio = database[municipio]
        estado = dados_municipio.get('estado', '')
        endereco = dados_municipio.get('endereco', '')
        prefeito = dados_municipio.get('prefeito', '')
        cnpj = dados_municipio.get('cnpj', '')
        contrato = dados_municipio.get('contrato', '')
    else:
        estado = endereco = prefeito = cnpj = 'NÃO ENCONTRADO'
    
    if tipo == "relatório de pagamento":
        template_file = os.path.join(script_dir, 'Relatorio_Malta.tex')
    else:
        template_file = os.path.join(script_dir, 'template.tex')
    output_file = os.path.join(script_dir, 'documento.tex')
    
    # Cria um nome de arquivo seguro a partir do assunto
    safe_assunto = assunto.replace(' – ', ' - ')
    # Retira o prefixo textual do tipo do assunto ao montar safe_assunto
    if safe_assunto.upper().startswith('RECLAMAÇÃO'):
        safe_assunto = safe_assunto[len('RECLAMAÇÃO'):].strip(' -')
    elif safe_assunto.upper().startswith('REQUERIMENTO'):
        safe_assunto = safe_assunto[len('REQUERIMENTO'):].strip(' -')
    for ch in '<>:"/\|?*':
        safe_assunto = safe_assunto.replace(ch, '')
    safe_assunto = safe_assunto.strip()
    safe_assunto = safe_assunto.capitalize()

    ano = str(__import__('datetime').datetime.now().year)
    if tipo == 'reclamação':
        prefix = 'REC'
    elif tipo == 'requerimento':
        prefix = 'REQ'
    else:
        prefix = 'REL'
    # Conectar os três primeiros termos com _ (prefix + contagem + ano)
    output_file_name = f"{prefix}_{contagem}_{ano} - {safe_assunto}.tex"
    output_file = os.path.join(script_dir, output_file_name)

    # Ler template e substituir
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('<<TIPO_DOC>>', tipo.upper())
    content = content.replace('<<MUNICIPIO>>', municipio.upper())
    content = content.replace('<<CONTAGEM>>', contagem)
    content = content.replace('<<UC_LINE>>', uc_line)
    content = content.replace('<<CONCESSIONARIA>>', concessionaria_linha)
    content = content.replace('<<ASSUNTO>>', assunto)
    content = content.replace('<<ESTADO>>', estado)
    content = content.replace('<<ENDERECO>>', endereco)
    content = content.replace('<<PREFEITO>>', prefeito)
    content = content.replace('<<CNPJ>>', cnpj)
    content = content.replace('<<CONTRATO>>', contrato)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Tipo de documento: {tipo.upper()}")
    print(f"Município: {municipio.upper()}")
    print(f"Contagem: {contagem}")
    print(f"Arquivo gerado: {output_file}")
    
    if tipo == "requerimento":
        print("Gerando requerimento...")
        # Código adicional para requerimento
    elif tipo == "reclamação":
        print("Gerando reclamação...")
        # Código adicional para reclamação
    elif tipo == "relatório de pagamento":
        print("Gerando relatório de pagamento...")
