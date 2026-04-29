import re

from texter_utils import (Index, Index_duplo, Linha, Apagar_linhas, Juntar,
                          Linha_para_Vetor, Justificar, formatar_e_alinhar_tabela,
                          normalizar_tipo_fornecimento,
                          marcadores, fornecimento, aba_info_geral, aba_historico_consumo)


def index_sigla_isolada(texto, sigla):
    padrao = re.compile(rf"^\s*{re.escape(sigla)}\s*$")
    return [i for i, linha in enumerate(texto.splitlines()) if padrao.match(linha)]

# ============================================================== #
# EXECUÇÃO - ENERGISA
# ============================================================== #

def format_energisa(texto, filename=None):
    # IDENTIFICADOR DE LAYOUT
    layout = None
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

    # FORMAÇÃO DA MATRIZ DE IDENTIFICAÇÃO
    # Essa é a primeira aba da planilha que será gerada, e tem como ojetivo servir de guia de UCs do município além de facilitar a análise de Enquadramento.

    
    info = ["UNIDADE:","FORNECIMENTO:","CLASSIFICAÇÃO:","DESTINO:"]
    vetor = []

    for i in range(0, len(info)):
        for e in range(1, len(Linha_para_Vetor(texto, Index(texto, info[i])[0]))):
            vetor.append(Linha_para_Vetor(texto, Index(texto, info[i])[0])[e])

    if len(vetor) > 6:
        vetor = vetor[:6] + [" ".join(vetor[6:])]
    if any(linha[0] == vetor[0] for linha in aba_info_geral) == False:
        aba_info_geral.append(vetor)
    
    aba_historico_consumo
    vetor = []
    index = Index(texto,"HISTÓRICO_DE_CONSUMO:")
    vetor.append(Linha_para_Vetor(texto,Index(texto,info[0])[0])[1])
    for i in range(index[0]+1,index[0]+13):
        linha = Linha_para_Vetor(texto,i)
        if len(linha) == 1:
            linha.append("UNK")
        vetor.append((linha[0],linha[1]))
    aba_historico_consumo.append(vetor)
    return texto
