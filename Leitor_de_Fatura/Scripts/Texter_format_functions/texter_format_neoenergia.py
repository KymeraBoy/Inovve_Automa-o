import re

from texter_utils import (Index, Linha, Apagar_linhas, Juntar,
                          Linha_para_Vetor, Justificar,
                          aba_info_geral, historico, aba_historico_consumo)

# ============================================================== #
# EXECUÇÃO - NEOENERGIA
# ============================================================== #

def format_neoenergia(texto, filename=None):
    # FORMATAÇÃO INCIAL
    texto = re.sub(r' {2,}', "\t", texto)                                   # Por ser de linha única temos que deixar por último   
    linhas = texto.splitlines()
    texto = Apagar_linhas(texto,None,(0,len(linhas)),True)
    texto = Justificar(texto)

    # ISSO DEVE PERMITIR QUE EU POSSA ACHAR ESSA PARTE SEM ME CONFUNDIR COM O HISTÓRICO     
    cons = Index(texto,"CONSUMO")   
    for i in reversed(range(0,len(cons))):              # vai de tras pra frente em cada linha que tiver "CONSUMO"
            vetor = Linha_para_Vetor(texto,cons[i])     # pega o vetor dessa linha
            if vetor[0] == "CONSUMO":  # confere se ele tem apenas a palavra 
                texto = Linha(texto, cons[i], None,[(0,"APENAS O CONSUMO REGISTRADO")],None) # poe o novo titulo
                texto = Linha(texto, cons[i], [1],None,None) # apaga o antigo
                texto = Apagar_linhas(texto, [cons[i]+1]) # apga o KWH que fica logo embaixo

    # IDENTIFICAÇÃO DE LAYOUT
    if "CÓDIGO DA INSTALAÇÃO" in texto:
        # print("Layout Novo")
        # DELIMITAÇÃO DAS FATURAS INDIVIDUAIS
        fim = len(texto.splitlines())
        texto = Linha(texto,fim-1,None,[(len(Linha_para_Vetor(texto,fim-1)),"\nFIM")],None)

        cod = Index(texto,"CÓDIGO DA INSTALAÇÃO")
        for i in reversed(range(1,len(cod))):
            texto = Linha(texto,cod[i]-1,None,[(len(Linha_para_Vetor(texto,cod[i]-1)),"\nFIM\n")],None)
        # APAGANDO LINHAS DESNECESSÁRIAS
        lixo = Index(texto,"CÓDIGO DO CLIENTE")
        end = Index(texto,"ENDEREÇO:")
        for i in reversed(range(0,len(cod))):
            texto = Apagar_linhas(texto,None,(lixo[i],end[i]-1))
        end = Index(texto,"ENDEREÇO:")        
        clas = Index(texto,"CLASSIFICAÇÃO")
        for i in reversed(range(0,len(cod))):
            texto = Apagar_linhas(texto,None,(clas[i]+1,clas[i]+2))
            texto = Linha(texto,clas[i],None,[(1,"\nHISTÓRICO DO CONSUMO")],None)
            texto = Juntar(texto,(end[i]+1,clas[i]-1),None)   

        hist = Index(texto,"HISTÓRICO DO CONSUMO")
        reg = Index(texto,"REGISTRADO")
        fim = Index(texto,"FIM")
        for i in reversed(range(0,len(cod))):
            for a in range(hist[i]+1,reg[i]):                
                vetor = Linha_para_Vetor(texto,a)
                if len(vetor) == 1:
                    texto = Linha(texto,a,None,[(1,"UNK")],None)
                if len(vetor) == 2:
                    texto = Linha(texto,a,None,[(2,"UNK")],None)
    else:
        # print("Layout Antigo")
        # DELIMITAÇÃO DAS FATURAS INDIVIDUAIS
        fim = len(texto.splitlines())
        texto = Linha(texto,fim-1,None,[(len(Linha_para_Vetor(texto,fim-1)),"\nFIM")],None)
        cod = Index(texto,"Nº DA INSTALAÇÃO")
        for i in reversed(range(0,len(cod))):
            texto = Apagar_linhas(texto,None,(cod[i]-4,cod[i]-1))
        cod = Index(texto,"Nº DA INSTALAÇÃO")
        for i in reversed(range(1,len(cod))):
            texto = Linha(texto,cod[i]-1,None,[(len(Linha_para_Vetor(texto,cod[i]-1)),"\nFIM\n")],None)

        # APAGANDO LINHAS DESNECESSÁRIAS
        lixo = Index(texto,"Nº DA INSTALAÇÃO")
        end = Index(texto,"ENDEREÇO DA UNIDADE CONSUMIDORA")
        for i in reversed(range(0,len(cod))):
            texto = Apagar_linhas(texto,None,(lixo[i]+2,end[i]-1))
        end = Index(texto,"ENDEREÇO DA UNIDADE CONSUMIDORA")
        clas = Index(texto,"CLASSIFICAÇÃO")
        for i in reversed(range(0,len(cod))):
            texto = Juntar(texto,(end[i]+1,clas[i]-1),None)    
        clas = Index(texto,"CLASSIFICAÇÃO")
        hist = Index(texto,"HISTÓRICO DO CONSUMO")
        for i in reversed(range(0,len(cod))):
            texto = Juntar(texto,(clas[i]+1,hist[i]-1))
        hist = Index(texto,"HISTÓRICO DO CONSUMO")
        for i in reversed(range(0,len(cod))):
            texto = Apagar_linhas(texto,[hist[i]+1])        

        hist = Index(texto,"HISTÓRICO DO CONSUMO")
        reg = Index(texto,"APENAS O CONSUMO REGISTRADO")
        fim = Index(texto,"FIM")
        for i in reversed(range(0,len(cod))):
            for a in range(hist[i]+1,reg[i]):                
                vetor = Linha_para_Vetor(texto,a)
                if len(vetor) == 1:
                    texto = Linha(texto,a,None,[(1,"UNK")],None)
                texto = Linha(texto,a,[0],None,None)
                texto = Linha(texto,a,None,[(0,re.sub(" ","",vetor[0]))],None)                
                vetor = []            
    
    # FORMATAÇÃO FINAL
    texto = re.sub(r"Nº DA INSTALAÇÃO|CÓDIGO DA INSTALAÇÃO", "\nUNIDADE CONSUMIDORA", texto)
    texto = re.sub(r"ENDEREÇO DA UNIDADE CONSUMIDORA|ENDEREÇO:", "ENDEREÇO", texto)
    texto = re.sub("CLASSIFICAÇÃO: ", "CLASSIFICAÇÃO\n", texto)

    # ANALISE   
   
    cod  = Index(texto,"UNIDADE CONSUMIDORA")
    hist = Index(texto,"HISTÓRICO DO CONSUMO")
    reg = Index(texto,"APENAS O CONSUMO REGISTRADO")
    fim = Index(texto,"FIM")
    linhas = texto.splitlines()
    vetor = []
    
    for i in range(0, len(cod)):
        # MATRIZ
        vetor.extend(Linha_para_Vetor(texto, cod[i]+1))
        vetor.extend(Linha_para_Vetor(texto, 15))
        vetor.extend(Linha_para_Vetor(texto, cod[i]+5))
        vetor.extend(Linha_para_Vetor(texto, cod[i]+3))
        chave = vetor[0]
        if not any(sub[0] == chave for sub in aba_info_geral):
            aba_info_geral.append(vetor)
        # HISTORICO
        grab = []
        grab.extend(Linha_para_Vetor(texto, cod[i]+1))
        for a in range(hist[i]+1,reg[i]):
            grab.append((Linha_para_Vetor(texto,a)[0],Linha_para_Vetor(texto,a)[1]))        
        historico.append(grab)

        # CONSUMO
        grub = []
        grub.extend(Linha_para_Vetor(texto, cod[i]+1))
        grub.append((Linha_para_Vetor(texto,9)[0],Linha_para_Vetor(texto,reg[i]+1)[0]))        
        historico.append(grub)

        grab = []
        grub = []
        vetor = []       

    vetor = []
    
    return texto
