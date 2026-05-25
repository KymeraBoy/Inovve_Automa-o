import re


from texter_utils import (Index, Index_duplo, Linha, Apagar_linhas, Juntar,
                          Linha_para_Vetor, Justificar, formatar_e_alinhar_tabela,
                          normalizar_tipo_fornecimento,
                          marcadores, fornecimento)


def index_sigla_isolada(texto, sigla):
    padrao = re.compile(rf"^\s*{re.escape(sigla)}\s*$")
    return [i for i, linha in enumerate(texto.splitlines()) if padrao.match(linha)]


def _extrair_matriz_info_geral(texto):
    info = ["UNIDADE:", "FORNECIMENTO:", "CLASSIFICAÇÃO:", "DESTINO:", "DADOS_DE_MEDIÇÃO:"]
    info = [termo for termo in info if termo in texto]
    vetor = []

    for i in range(0, len(info)):
        for e in range(1, len(Linha_para_Vetor(texto, Index(texto, info[i])[0]))):
            vetor.append(Linha_para_Vetor(texto, Index(texto, info[i])[0])[e])
            if info[i] == "DESTINO:":
                vetor = vetor[:6] + [" ".join(vetor[6:])]
            if info[i] == "DADOS_DE_MEDIÇÃO:":
                vetor = vetor[:8]

    return vetor


def _extrair_linha_historico(texto):
    index = Index(texto, "HISTÓRICO_DE_CONSUMO:")
    if not index:
        return []

    info = ["UNIDADE:", "FORNECIMENTO:", "CLASSIFICAÇÃO:", "DESTINO:", "DADOS_DE_MEDIÇÃO:"]
    info = [termo for termo in info if termo in texto]
    if not info:
        return []

    vetor = ["SEM_UC"]

    for i in range(index[0] + 1, index[0] + 13):
        linha = Linha_para_Vetor(texto, i)
        if len(linha) == 1:
            linha.append("UNK")
        vetor.append((linha[0], linha[1]))

    return vetor


def _extrair_uc_documento(texto, filename=None):
    if filename:
        padrao_nome = re.search(r"_(\d+)-(\d+)-(\d+)_L\d+_Poppler", filename, flags=re.IGNORECASE)
        if padrao_nome:
            return f"{padrao_nome.group(1)}/{padrao_nome.group(2)}-{padrao_nome.group(3)}"

    padrao_texto = re.search(r"\b(\d+)/(\d+)-(\d+)\b", texto)
    if padrao_texto:
        return f"{padrao_texto.group(1)}/{padrao_texto.group(2)}-{padrao_texto.group(3)}"

    padrao_nome_simples = re.search(r"_(\d+)/(\d+)-(\d+)_", filename or "")
    if padrao_nome_simples:
        return f"{padrao_nome_simples.group(1)}/{padrao_nome_simples.group(2)}-{padrao_nome_simples.group(3)}"

    return "SEM_UC"


def _extrair_referencia_documento(texto, filename=None):
    if filename:
        padrao_nome = re.search(r"_([A-Z]{3})[-_/](\d{4})_", filename, flags=re.IGNORECASE)
        if padrao_nome:
            mes = padrao_nome.group(1).upper()
            ano = padrao_nome.group(2)
            return f"{mes}/{ano[-2:]}" if len(ano) == 4 else f"{mes}/{ano}"

        padrao_nome_2 = re.search(r"_([A-Z]{3})[-_/](\d{2,4})_", filename, flags=re.IGNORECASE)
        if padrao_nome_2:
            mes = padrao_nome_2.group(1).upper()
            ano = padrao_nome_2.group(2)
            return f"{mes}/{ano[-2:]}" if len(ano) == 4 else f"{mes}/{ano}"

    padrao_texto = re.search(r"\b([A-Z]{3})\s*/\s*(\d{2,4})\b", texto, flags=re.IGNORECASE)
    if padrao_texto:
        mes = padrao_texto.group(1).upper()
        ano = padrao_texto.group(2)
        return f"{mes}/{ano[-2:]}" if len(ano) == 4 else f"{mes}/{ano}"

    return "SEM_REFERENCIA"


def _extrair_cliente_e_endereco(texto):
    linhas = texto.splitlines()
    marcadores = (
        "Grupo/Subgp.",
        "Grupo/Subgp.:",
        "GRUPO/SUBGRP.",
        "Classificação:",
        "CLASSIFICAÇÃO:",
        "LIGAÇÃO:",
    )

    limite = len(linhas)
    for indice, linha in enumerate(linhas):
        if any(marcador in linha for marcador in marcadores):
            limite = indice
            break

    bloco = [linha.strip() for linha in linhas[:limite] if linha.strip()]
    bloco = [linha for linha in bloco if linha not in {"\f"}]

    cliente = bloco[0] if len(bloco) >= 1 else ""
    endereco = bloco[1] if len(bloco) >= 2 else ""

    return cliente, endereco


def _extrair_numero_medidor(texto):
    padroes = (
        r"\b(?:N[ºo\.]?\s*do\s*Medidor|N[ºo\.]?\s*MEDIDOR|MEDIDOR|Medidor|MATR[ÍI]CULA)\s*:\s*(.+)$",
    )

    for linha in texto.splitlines():
        for padrao in padroes:
            match = re.search(padrao, linha, flags=re.IGNORECASE)
            if not match:
                continue

            valor_bruto = match.group(1).strip()
            if not valor_bruto:
                continue

            valor = re.split(r"\s+(?:Emiss[ãa]o|DOM\.?|REFER[ÊE]NCIA|Roteiro|Classe|Grupo|CNPJ|CPF|Insc\.?|Matr[íi]cula)\b", valor_bruto, maxsplit=1, flags=re.IGNORECASE)[0].strip()
            valor = valor.split()[0].strip() if valor else ""

            if valor and re.search(r"\d", valor):
                return valor

    return ""

# ============================================================== #
# EXECUÇÃO - ENERGISA
# ============================================================== #

def format_energisa(texto, filename=None):
    # IDENTIFICADOR DE LAYOUT
    layout = None
    texto_original = texto
    if filename:
        match = re.search(r'_L([1-7])', filename)
        if match:
            layout = f"L{match.group(1)}"

    # FORMATAÇÃO INICIAL (retirar caracteres invisiveis e linhas vazias)
    texto = texto.replace('\ufeff', '')         
    texto = Apagar_linhas(texto,None,(0,len(texto.splitlines())),True)
    
    m_destino           = f"{marcadores[0]}:"
    m_mes_ano           = f"{marcadores[1]}:"
    m_unidade           = f"{marcadores[2]}:"
    m_classificacao     = f"{marcadores[3]}:"
    m_fornecimento      = f"{marcadores[4]}:"
    m_historico         = f"{marcadores[5]}:"
    m_dados_faturamento = f"{marcadores[6]}:"
    m_tabela_tributos   = f"{marcadores[7]}:"
    m_indicadores       = f"{marcadores[8]}:"
    m_dados_medicao     = f"{marcadores[9]}:"    

    # Padroniza tipos de fornecimento antes do direcionamento por layout.
    texto = normalizar_tipo_fornecimento(texto)

    # DIRECIONAMENTO POR LAYOUT
    if layout == "L1":
        # CLASSIFICAÇÃO
        texto = re.sub("Grp/Sbg: ", f"{m_classificacao}\t", texto) 
        texto = re.sub("Cls/Sbc: ", "", texto) 
        texto =Juntar(texto,[Index(texto,m_classificacao)[0],Index(texto,m_classificacao)[0]+1])

        # FORNECIMENTO        
        texto = re.sub(" MONOFASICO",   f"\n{m_fornecimento}\t"+fornecimento[0],texto)
        texto = re.sub(" BIFASICO",     f"\n{m_fornecimento}\t"+fornecimento[1],texto)
        texto = re.sub(" TRIFASICO",    f"\n{m_fornecimento}\t"+fornecimento[2],texto)

        # MÊS_ANO E UNIDADE CONSUMIDORA
        clas = Index(texto,m_classificacao)
        texto = Linha(texto, clas[0]-2,None,[(0,m_mes_ano)],None)
        texto = Linha(texto, clas[0]-1,None,[(0,m_unidade)],None)

        # DESTINO
        texto = Juntar(texto,(0,Index(texto,m_mes_ano)[0]-1))
        texto = Linha(texto,0,None,[(0,m_destino)])

        # HISTÓRICO DE CONSUMO
        forn = Index(texto,m_fornecimento)
        texto = Linha(texto,forn[0],None,[(2,f"\n\n{m_historico}")])
        texto = texto.replace("*","")

        # MEDIDOR
        lei = Index(texto,"Leitura")      
        texto = Linha(texto,lei[0],None,[(0,f"\n{m_dados_medicao}\n")])

        # DESCRIÇÃO DO FATURAMENTO
        lei = Index(texto,"Tarifa c/")      
        texto = Linha(texto,lei[0],None,[(0,f"\n{m_dados_faturamento}\n")])
        texto = re.sub(r' {2,}', "\t", texto)
        v1l1 = Linha_para_Vetor(texto,Index(texto,m_historico)[0]+1)
        linhas = texto.splitlines()
        v2l1 = linhas[Index(texto,m_historico)[0]+2].split()
        texto = Apagar_linhas(texto,[Index(texto,m_historico)[0]+1,Index(texto,m_historico)[0]+2])
        for i in range(0,len(v1l1)):
            texto = Linha(texto,Index(texto,m_historico)[0]+1+i,None,[(0,v2l1[i]+"\t"+v1l1[i]+"\n")])
            
    elif layout == "L2":
        texto = texto.replace(' v ','  ')
        # CLASSIFICAÇÃO
        texto = re.sub("Grp/Sbg:", f"{m_classificacao}\t", texto) 
        texto = re.sub("Cls/Sbc:", "", texto) 
        texto =Juntar(texto,[Index(texto,m_classificacao)[0],Index(texto,m_classificacao)[0]+1])

        # FORNECIMENTO
        texto = re.sub(" MONOFASICO",   f"\n{m_fornecimento}\t"+fornecimento[0],texto)
        texto = re.sub(" BIFASICO",     f"\n{m_fornecimento}\t"+fornecimento[1],texto)
        texto = re.sub(" TRIFASICO",    f"\n{m_fornecimento}\t"+fornecimento[2],texto)

        # MÊS_ANO E UNIDADE CONSUMIDORA
        clas = Index(texto,m_classificacao)
        texto = Linha(texto, clas[0]-2,None,[(0,m_mes_ano)],None)
        texto = Linha(texto, clas[0]-1,None,[(0,m_unidade)],None)

        # DESTINO
        texto = Juntar(texto,(0,Index(texto,m_mes_ano)[0]-1))
        texto = Linha(texto,0,None,[(0,m_destino)])

        # HISTÓRICO DE CONSUMO
        forn = Index(texto,m_fornecimento)
        texto = Linha(texto,forn[0],None,[(2,f"\n\n{m_historico}")])
        texto = texto.replace("*","")

        # MEDIDOR
        lei = Index(texto,"LEITURAS")      
        texto = Linha(texto,lei[0],None,[(0,f"\n{m_dados_medicao}\n")])
        texto = Apagar_linhas(texto,[lei[0]+2])

        # DESCRIÇÃO DO FATURAMENTO
        lei = Index(texto,"BASE CALC.")      
        texto = Linha(texto,lei[0],None,[(0,f"\n{m_dados_faturamento}\n")])

        # INDICADORES DE QUALIDADE
        qual = Index(texto,"TRIMEST.")
        texto = Linha(texto,qual[0]-1,None,[(1,f"\n\n{m_indicadores}")])

    elif layout == "L3":
        # CLASSIFICAÇÃO
        texto = re.sub("Grp/Sbg:", f"{m_classificacao}\t", texto) 
        texto = re.sub("Cls/Sbc:", "", texto) 
        texto =Juntar(texto,[Index(texto,m_classificacao)[0],Index(texto,m_classificacao)[0]+1])

        # FORNECIMENTO
        texto = re.sub(" MONOFASICO",   f"\n{m_fornecimento}\t"+fornecimento[0],texto)
        texto = re.sub(" BIFASICO",     f"\n{m_fornecimento}\t"+fornecimento[1],texto)
        texto = re.sub(" TRIFASICO",    f"\n{m_fornecimento}\t"+fornecimento[2],texto)

        # MÊS_ANO E UNIDADE CONSUMIDORA
        clas = Index(texto,m_classificacao)
        texto = Linha(texto, clas[0]-2,None,[(0,m_mes_ano)],None)
        texto = Linha(texto, clas[0]-1,None,[(0,m_unidade)],None)

        # DESTINO
        texto = Juntar(texto,(0,Index(texto,m_mes_ano)[0]-1))
        texto = Linha(texto,0,None,[(0,m_destino)])   
          
        # HISTÓRICO DE CONSUMO
        forn = Index(texto,m_fornecimento)
        texto = Linha(texto,forn[0],None,[(2,f"\n\n{m_historico}")])
        texto = texto.replace("*","")

        # MEDIDOR
        lei = Index(texto,"LEITURAS")      
        texto = Linha(texto,lei[0],None,[(0,f"\n{m_dados_medicao}\n")])
        texto = Apagar_linhas(texto,[lei[0]+2])

        # DESCRIÇÃO DO FATURAMENTO
        lei = Index(texto,"BASE CALC.")      
        texto = Linha(texto,lei[0],None,[(0,f"\n{m_dados_faturamento}\n")])

        # INDICADORES DE QUALIDADE
        qual = Index(texto,"TRIMEST.")
        texto = Linha(texto,qual[0]-1,None,[(1,f"\n\n{m_indicadores}")])

    elif layout == "L4":
        # FORMATAÇÃO CABEÇALHO (5 primeiras linhas)
        texto = Juntar(texto,(0,Index(texto,"LIGAÇÃO:")[0]-5)) 
        texto = Juntar(texto,(3,4)) 
        texto = Linha(texto,0,None,[(0,m_destino)],None)
        texto = Linha(texto,1,None,[(0,m_mes_ano)],None)
        texto = Linha(texto,2,None,[(0,m_unidade)],None)
        texto = re.sub("Classificação: ",f"{m_classificacao}\t",texto)
        texto = re.sub("LIGAÇÃO: ",f"{m_fornecimento}\t",texto)           

        # INSERINDO MARCADORES
        texto = Linha(texto,Index(texto,"DICRI")[0],None,[(1,f"\n\n{m_historico}")],None,)
        if Index(texto,"DIC  ") == []:
            texto = Linha(texto,index_sigla_isolada(texto,"DIC")[0]-1,None,[(1,f"\n\n{m_indicadores}\nLimites\tMensal\tApurado\tTrimestral\tAnual")],None,)
        else:
            texto = Linha(texto,Index(texto,"DIC ")[0]-1,None,[(1,f"\n\n{m_indicadores}\nLimites\tMensal\tApurado\tTrimestral\tAnual")],None,)
        texto = Linha(texto,Index(texto,"Tributo")[0]-1,None,[(1,f"\n\n{m_tabela_tributos}\nTributo\tBase(R$)\tAlíquota(%)\tValor(R$)")],None,)
        texto = Linha(texto,5,None,None,None,1)
        if Index(texto,"Itens da Fatura")[0] == 7:
            texto = Linha(texto,6,None,[(0,f"{m_dados_medicao}\tIP ESTIMADA\n")])
        else:
            texto = Linha(texto,6,None,[(0,m_dados_medicao)])
        texto = Linha(texto,Index(texto,m_dados_medicao[:-1])[0],None,[(2,f"\n\n{m_dados_faturamento}")],None,)

        # FORMATAÇÃO COMPLEXA       
        texto = formatar_e_alinhar_tabela(texto,Index(texto,m_indicadores[:-1])[0]+2,Index(texto,m_indicadores[:-1])[0]+5)
        texto = formatar_e_alinhar_tabela(texto,Index(texto,m_tabela_tributos[:-1])[0]+4,Index(texto,m_indicadores[:-1])[0]-2)  

        # APAGAR LINHAS INUTEIS
        texto = Apagar_linhas(texto,[Index(texto,m_tabela_tributos)[0]+2,Index(texto,m_tabela_tributos)[0]+3])

    elif layout == "L5":
        # CLASSIFICAÇÃO
        texto = re.sub("GRUPO/SUBGRP.:", f"{m_classificacao}\t", texto) 
        texto = re.sub("CLASSE/SUBCLS.: ", "", texto) 
        texto =Juntar(texto,[Index(texto,m_classificacao)[0],Index(texto,m_classificacao)[0]+1])

        # FORNECIMENTO
        ligacao = Index(texto,"LIGAÇÃO:")
        
        if fornecimento[0] in texto:
            texto = Linha(texto,ligacao[0],None,[(1,f"\n{m_fornecimento}\tMONOFASICO")],None)
        if fornecimento[1] in texto:
            texto = Linha(texto,ligacao[0],None,[(1,f"\n{m_fornecimento}\tBIFASICO")],None)
        if fornecimento[2] in texto:
            texto = Linha(texto,ligacao[0],None,[(1,f"\n{m_fornecimento}\tTRIFASICO")],None)
        texto = Apagar_linhas(texto,[ligacao[0]])

        # MÊS_ANO E UNIDADE CONSUMIDORA
        tarf = Index(texto,"TARIFA SEM TARIFA COM")
        texto = Linha(texto, tarf[0]-2,None,[(0,m_mes_ano)],None)
        texto = Linha(texto, tarf[0]-1,None,[(0,m_unidade)],None)

        # ENDEREÇO DA UNIDADE CONSUMIDORA (APAGAR)
        end = Index(texto,"ENDEREÇO DA UNIDADE CONSUMIDORA")
        mes = Index(texto,m_mes_ano)
        texto = Apagar_linhas(texto,None,(end[0],end[0]+3))

        # DESTINO
        texto = Juntar(texto,(0,Index(texto,m_classificacao)[0]-1))
        texto = Linha(texto,0,None,[(0,m_destino)])

        # MEDIDOR
        texto = re.sub("Nº DO MEDIDOR: ",f"{m_dados_medicao}\t",texto)
        med = Index(texto,m_dados_medicao)
        if med == []:
            texto = Linha(texto,Index(texto,m_unidade)[0],None,[(2,f"\n{m_dados_medicao}\tIP ESTIMADA")])            
        else:
            texto = Juntar(texto,(med[0],med[0]+1))

        # DESCRIÇÃO DO FATURAMENTO
        desc = Index(texto,"TARIFA SEM TARIFA COM")
        texto = Linha(texto,desc[0],None,[(0,f"\n{m_dados_faturamento}\n")])

        # HISTÓRICO DE CONSUMO
        tot = Index(texto,"TOTAL:")
        texto = Linha(texto,tot[0],None,[(1,f"\n\n{m_historico}")])
        texto = texto.replace("*","")

        # INDICADORES DE QUALIDADE
        qual = Index(texto,"DIC")
        texto = Linha(texto,qual[0]-1,None,[(1,f"\n\n{m_indicadores}\nLimites\tMensal\tApurado\tTrimestral\tAnual")])

    elif layout == "L6":
        # FORNECIMENTO
        texto = re.sub("LIGAÇÃO: ",f"{m_fornecimento}\t",texto)

        # CLASSIFICAÇÃO
        texto = re.sub("Grupo/Subgp.: ", f"{m_classificacao}\t", texto) 
        texto = re.sub("Classe/Subcls.: ", "", texto) 
        texto =Juntar(texto,[Index(texto,m_classificacao)[0],Index(texto,m_classificacao)[0]+1])

        # MÊS_ANO E UNIDADE CONSUMIDORA
        clas = Index(texto,m_classificacao)
        texto = Linha(texto, clas[0]-2,None,[(0,m_mes_ano)],None)
        texto = Linha(texto, clas[0]-1,None,[(0,m_unidade)],None)

        # DESTINO
        texto = Juntar(texto,(0,Index(texto,m_mes_ano)[0]-1))
        texto = Linha(texto,0,None,[(0,m_destino)])

        # DESCRIÇÃO DO FATURAMENTO
        forn = Index(texto,m_fornecimento)
        texto = Linha(texto,forn[0],None,[(2,f"\n\n{m_dados_faturamento}")])

        # HISTÓRICO DE CONSUMO
        hist = Index(texto,"HISTÓRICO DE CONSUMO (kWh)")
        texto = Linha(texto,hist[0],None,[(0,f"\n{m_historico}\n")])
        texto = Apagar_linhas(texto,[hist[0]+2,hist[0]+3])
        texto = texto.replace("*","")

        # INDICADORES DE QUALIDADE
        qual = Index(texto,"DIC MENSAL")
        texto = Linha(texto,qual[0]-1,None,[(1,f"\n\n{m_indicadores}")])

    elif layout == "L7":
        texto = texto.replace(' v ','  ')
        # CLASSIFICAÇÃO E FORNECIMENTO
        texto = re.sub("Classificação: ", f"{m_classificacao}\t", texto) 
        texto = re.sub("Tipo de Fornecimento: ", f"{m_fornecimento}\t", texto) 
        texto =Juntar(texto,[Index(texto,m_classificacao)[0],Index(texto,m_classificacao)[0]+1])

        # MÊS_ANO E UNIDADE CONSUMIDORA
        clas = Index(texto,m_classificacao)
        texto = Linha(texto, clas[0]-2,None,[(0,m_mes_ano)],None)
        texto = Linha(texto, clas[0]-1,None,[(0,m_unidade)],None)

        # DESTINO
        texto = Juntar(texto,(0,Index(texto,m_mes_ano)[0]-1))
        texto = Linha(texto,0,None,[(0,m_destino)])

        # DESCRIÇÃO DO FATURAMENTO
        forn = Index(texto,"Base Calc.")
        texto = Linha(texto,forn[0],None,[(0,f"\n{m_dados_faturamento}\n")])

        # TRIBUTOS
        pis = Index(texto, "PIS/PASEP")
        texto = Linha(texto,pis[0]-1,None,[(1,f"\n\n{m_dados_faturamento}")])

        # MEDIDOR
        lei = Index(texto,"Faturamento pela média/mínimo")      
        texto = Linha(texto,lei[0],None,[(1,f"\n\n{m_dados_medicao}")])
        
        # HISTORICO DE FATURAMENTO
        hist = Index(texto,m_dados_medicao)
        texto = Linha(texto,hist[0]+1,None,[(1,f"\n\n{m_historico}")])

    texto = re.sub(r' {2,}', "\t", texto)
    texto = re.sub(r'\*', "", texto)
    texto = texto.replace("MTC-CONVENCIONAL","")
    texto = texto.replace(' v ','  ')
    texto = texto.replace('TENSÃO / ','TENSÃO\t')

    # MATRIZES POR FATURA
    matriz_info_geral = _extrair_matriz_info_geral(texto)
    uc = _extrair_uc_documento(texto_original, filename)
    referencia = _extrair_referencia_documento(texto_original, filename)
    matriz_historico_consumo = _extrair_linha_historico(texto)
    if matriz_historico_consumo:
        matriz_historico_consumo[0] = uc

    cliente, endereco_entrega = _extrair_cliente_e_endereco(texto_original)
    numero_medidor = _extrair_numero_medidor(texto_original)

    classificacao = matriz_info_geral[4] if len(matriz_info_geral) > 4 else ""
    tipo_fornecimento = matriz_info_geral[1] if len(matriz_info_geral) > 1 else ""

    return {
        "arquivo": filename,
        "uc": uc,
        "referencia": referencia,
        "classificacao": classificacao,
        "tipo_fornecimento": tipo_fornecimento,
        "cliente": cliente,
        "endereco_entrega": endereco_entrega,
        "numero_medidor": numero_medidor,
        "info_geral": matriz_info_geral,
        "historico_consumo": matriz_historico_consumo,
        "texto": texto,
    }
