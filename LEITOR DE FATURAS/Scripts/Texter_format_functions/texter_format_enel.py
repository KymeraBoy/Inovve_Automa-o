import re

from texter_utils import (Index, Index_duplo, Linha, Apagar_linhas, Juntar,
                          Linha_para_Vetor, Justificar, Etiquetar,
                          formatar_tabela_complexa, alinhar_tabela_por_tabs, headers)

# ============================================================== #
# EXECUÇÃO - ENEL
# ============================================================== #

def enel_1(texto, filename=None):
    texto = Etiquetar(texto)                    # Coloca as estiquetas para usarmos como referência

    # FORMATANDO TODAS AS TABELAS
    # TABELA DA FATURA AGRUPADA
    agrupada    = Index(texto,"FATURA AGRUPADA")    
    grupo       = Index(texto, "Grupo")
    print(grupo)
    texto = formatar_tabela_complexa(texto,agrupada[0]+2,grupo[0]-1)
    texto = Linha(texto,agrupada[0]+1,None,[(1,headers[0])])            # Insere o Cabeçalho
    texto = alinhar_tabela_por_tabs(texto,agrupada[0]+2,grupo[0]+1)     # Alinha as colunas
    
    # TABELAS DAS FATURAS INDIVIDUAIS
    # TABELA DE TRIBUTOS
    tributos    = Index(texto,"TABELA DE TRIBUTOS")
    for i in range(0,len(tributos)):
        tributos = Index(texto,"TABELA DE TRIBUTOS")                        # Atualiza o index
        texto = Apagar_linhas(texto,[tributos[i]+1,tributos[i]+2])          # Apaga o cabeçalho antigo
        texto = formatar_tabela_complexa(texto,tributos[i]+1,tributos[i]+3) # Formata a tabela
        texto = Linha(texto,tributos[i],None,[(1,headers[1])])              # Insere o cabeçalho novo
        texto = alinhar_tabela_por_tabs(texto,tributos[i]+1,tributos[i]+4)  # Alinha a tabela

    # TABELA HISTÓRICO DE CONSUMO
    consumo = Index(texto,"TABELA HISTÓRICO DE CONSUMO") 
    for i in range(0,len(consumo)):
        consumo = Index(texto,"TABELA HISTÓRICO DE CONSUMO")                    # Atualiza o index
        texto = Apagar_linhas(texto,[consumo[i]+1,consumo[i]+2,consumo[i]+3])   # Apaga o cabeçalho antigo
        texto = formatar_tabela_complexa(texto,consumo[i]+1,consumo[i]+13)      # Formata a tabela
        texto = Linha(texto,consumo[i],None,[(1,headers[2])])                   # Insere o cabeçalho novo
        texto = alinhar_tabela_por_tabs(texto,consumo[i]+1,consumo[i]+14)       # Alinha a tabela

    # TABELA DESCRIÇÃO DO FATURAMENTO
    descricao = Index(texto,"TABELA DE DESCRIÇÃO DO FATURAMENTO")
    for i in range(0,len(descricao)):
        descricao = Index(texto,"TABELA DE DESCRIÇÃO DO FATURAMENTO")       # Atualiza o index
        texto = Apagar_linhas(texto,[descricao[i]+1,descricao[i]+3])        # Apaga parte do cabeçalho antigo
        medicao = Index(texto,"TABELA DE EQUIPAMENTO DE MEDIÇÃO")           # Atualiza o index de referência do final da tabela
        texto = formatar_tabela_complexa(texto,descricao[i]+1,medicao[i]-2) # Formata a tabela
        texto = Apagar_linhas(texto,[descricao[i]+1])                       # Apaga o restante do cabeçalho antigo
        texto = Linha(texto,descricao[i],None,[(1,headers[3])])             # Insere o cabeçalho novo
        texto = alinhar_tabela_por_tabs(texto,descricao[i]+1,medicao[i]-1)  # Alinha a tabela

    # TABELA DE EQUIPAMENTO DE MEDIÇÃO
    medicao = Index(texto,"TABELA DE EQUIPAMENTO DE MEDIÇÃO")               
    texto = re.sub(r' {2,}', "\t", texto)                                   # Por ser de linha única temos que deixar por último
    for i in range(0, len(medicao)):
        medicao = Index(texto,"TABELA DE EQUIPAMENTO DE MEDIÇÃO")           # Atualiza o index
        texto = Apagar_linhas(texto,[medicao[i]+1])                         # Apaga o cabeçalho antigo
        temp = texto.splitlines()                                           # Divide o texto em linhas
        if medicao[i]+2 < len(temp)-1:                                      # Verifica se é a ultima tabela do texto
            if Linha_para_Vetor(texto,medicao[i]+3)[0] != "" :              # Verifica se ocorreu sobreposição na fatura
                texto = Juntar(texto,[medicao[i]+2,medicao[i]+3],None)      # Corrige a sobreposição
        texto = alinhar_tabela_por_tabs(texto,medicao[i]+1,medicao[i]+2)    # Alinha a tabela
    
    # FORMATAÇÃO DO RESTANTE   
    # CAPA
    capa = Index(texto,"CAPA")
    texto = Juntar(texto,(capa[0]+2,capa[0]+5),None)                    # Põe todas as informações da capa em uma linha única
    texto = Linha(texto,capa[0]+1,None,[(0,"\nDADOS DO CLIENTE")],None) # Insere a etiqueta 

    # FATURA AGRUPADA 
    agrupada    = Index(texto,"AGRUPADA")                                   # Salvar o Index da fatura agruapada
    texto = Linha(texto,agrupada[0]+1,None,None,None,1)                     # Cria uma linha para mandar as informações para antes da tabela
    grupo = Index(texto,"Grupo")                                            
    texto = Apagar_linhas(texto,[grupo[0]+3])                               # Apaga a UC que vem repetida
    individual = Index(texto,"INDIVIDUAL")
    texto = Juntar(texto,(grupo[0]+4,individual[0]-2),None)                 # Junta todas as UCs filhas em uma unica linha
    texto = Juntar(texto,(grupo[0],grupo[0]+3),agrupada[0]+2)               # Junta todas as informações apos a tabela e manda pra antes dela
    texto = Linha(texto,agrupada[0]+1,None,[(0,headers[4])],None)           # Insere o cabeçalho
    texto = Linha(texto,agrupada[0]+2,None,[(6,"CONCESSIONÁRIA")],None)     # Adiciona ao cabeçalho mais um elemento
    texto = Linha(texto,agrupada[0]+3,None,[(6,"ENEL")],None)               # Carimba de qual concessionaria é a fatura
    texto = alinhar_tabela_por_tabs(texto,agrupada[0]+2,agrupada[0]+3)      # Alinha a tabela
    
    # FATURA INDIVIDUAL
    individual = Index(texto,"FATURA INDIVIDUAL")
    print(f"Quantidade de UCs: {len(individual)}")  # Mostra quantas faturas individuais cada agrupadamento tem
    for i in range(0,len(individual)):
        individual = Index(texto,"FATURA INDIVIDUAL")   # Atualiza o index da fatura individual
        print(f"Progresso:{i+1} de {len(individual)}")  # Mostra o Progresso

        texto = Juntar(texto,[individual[i]+2,individual[i]+5,individual[i]+11,individual[i]+13],None)  # Cabeçalho de identificação
        texto = Juntar(texto,[individual[i]+3,individual[i]+5,individual[i]+10,individual[i]+11],None)  # Dados de identificação
        texto = Juntar(texto,[individual[i]+5,individual[i]+9],None)                                    # Cabeçalho de datas e valores
        texto = Juntar(texto,[individual[i]+7,individual[i]+9],None)                                    # Dados de datas e valores

        trib = Index(texto,"TABELA DE TRIBUTOS")
        texto = Juntar(texto,(individual[i]+9,trib[i]-3),None)                                          # Cliente e endereço
        texto = Juntar(texto,[individual[i]+3,individual[i]+10],None)                                   # Colocando o CNPJ no lugar certo

        texto = Apagar_linhas(texto,[individual[i]+6])
        texto = Apagar_linhas(texto,[individual[i]+7])

        texto = Linha(texto,individual[i]+2,None,[(4,"CPF/CNPJ")],None)                                 # Insere no cabeçalho
        texto = Linha(texto,individual[i]+6,[0],None,None)                                              # Apaga elemento indesejado na linha de dados
        texto = Linha(texto,individual[i]+5,None,[(6,"EMISSÃO")],None)                                  # Insere no cabeçalho
        texto = Linha(texto,individual[i]+6,None,[(6,Linha_para_Vetor(texto,individual[i]+6)[1])],None) # Data de emissão igual a de leitura vale apenass para a ENEL

        texto = alinhar_tabela_por_tabs(texto,individual[i]+2,individual[i]+3)
        texto = alinhar_tabela_por_tabs(texto,individual[i]+5,individual[i]+6)

        texto = Linha(texto,individual[i]+1,None,[(0,"\nIDENTIFICAÇÃO")],None)
        texto = Linha(texto,individual[i]+5,None,[(1,"\n\nDATAS E VALORES")],None)
        texto = Linha(texto,individual[i]+9,None,[(10,"\n\nCLIENTE E ENDEREÇO")],None)

    return texto
def enel_2(texto, filename=None):
    # ETIQUETAÇÃO
    index = Index(texto,"  ")                                                                           # para etiquetação da fatura agrupada
    texto = Linha(texto,index[0]-1,None,[(1,"\nCAPA\n\nDADOS DO CLIENTE\n\nFATURA AGRUPADA\n")],None) # Insere as primeira etiquetas do texto
    fase = Index_duplo(texto,"MONOFÁSICO","TRIFÁSICO")                                  # Para etiquetação das faturas individuais
    for i in range(0,len(fase)):
        fase = Index_duplo(texto,"MONOFÁSICO","TRIFÁSICO")                              # Atualizamos o index
        texto = Linha(texto, fase[i]-2,None,None,None,1)                                # Adicionamos uma linha onde sera inserido a etiqueta
        texto = Linha(texto, fase[i]-2,None,[(0,f"\nFATURA INDIVIDUAL {i+1}\n")],None)  # Insere a etiqueta com nmumeração

    #  CAPA
    # 1. O texto de capa varia entre 3 e 4 linhas, por isso vamoss usar os primeiros 2 espaços consecutivos como marcador de inicio da tabela de dados do faturamento, já que eles não vão aparecer nas informações da capa
    texto = Juntar(texto,(0,index[0]-1),index[0]+3)                                                   # Junta todas as informações da capa em umaa única linha

    # FATURA AGRUPADA
    # 2. Já temos a etiquta do inicio da fatura agrupada, o que fica faltando é a do final, para isso vamos usar como referência o tipo de fornecimento que sempre vai aparecer e com apenas duas variações
    agrupada    = Index(texto, "FATURA AGRUPADA")
    grupo       = Index(texto, "Grupo")
    individual  = Index(texto, "FATURA INDIVIDUAL")

    texto = formatar_tabela_complexa(texto,agrupada[0]+2,grupo[0]-1)    # Formata a tabela da fatura agrupada
    texto = Juntar(texto,(grupo[0]+5,individual[0]-2),None)             # Junta todas as UCs em umaa linha
    texto = Apagar_linhas(texto,[grupo[0]+3])                           # Apaga UC repetida
    texto = Juntar(texto,(grupo[0],grupo[0]+3),agrupada[0]+1)           # Junta todas as informações da fatura agrupada em uma linha
    
    texto = Linha(texto,agrupada[0],None,[(1,"\n\nGRUPO\tEMISSÃO\tUNIDADE\tCONSUMIDORA\tVENCIMENTO\tTOTAL A PAGAR\tCPF/CNPJ\tCONCESSIONÁRIA")],None)
    texto = Linha(texto,agrupada[0]+3,None,[(4,"ENEL"),],None)                          # Carimba de qual concessionaria é a fatura
    texto = Linha(texto,agrupada[0]+4,None,[(0,headers[0]),],None)   # Carimba de qual concessionaria é a fatura

    # FATURA INDIVIDUAL
    for i in range(0,len(individual)):
        individual  = Index(texto, "FATURA INDIVIDUAL")
        pis         = Index(texto, "PIS/PASEP")
        cons        = Index(texto, "MÊS/ANO      CONSUMO")
        desc        = Index(texto, "Itens de Fatura")
        med         = Index_duplo(texto, "EQUIPAMENTOS DE MEDIÇÃO E CONSUMO NO PERIODO","TABELA DE EQUIPAMENTO DE MEDIÇÃO")

        # TABELA DE MEDIÇÃO
        texto = Linha(texto,med[i],None,[(1,"\n\nTABELA DE EQUIPAMENTO DE MEDIÇÃO")])
        texto = Apagar_linhas(texto,[med[i]])                   # Apaga o titulo antigo
        temp = texto.splitlines()                               # Divide o texto em linhas
        if med[i]+3 < len(temp)-1:                              # Verifica se é a ultima tabela do texto
            if Linha_para_Vetor(texto,med[i]+4)[0] != "" :      # Verifica se ocorreu sobreposição na fatura
                texto = Juntar(texto,[med[i]+3,med[i]+4],None)  # Corrige a sobreposição

        # TABELA DESCRIÇÃO DO FATURAMENTO
        texto = Apagar_linhas(texto,[desc[i]+1])                   # Apaga erro de extração
        texto = formatar_tabela_complexa(texto,desc[i]+1,med[i]-2)
        texto = Linha(texto,desc[i],None,[(1,"\n\nTABELA DE DESCRIÇÃO DO FATURAMENTO")])
        texto = Linha(texto,desc[i]+2,None,[(1,headers[3])])
        texto = Apagar_linhas(texto,[desc[i]])                   # Apaga cabeçalho antigo

        # TABELA HISTÓRICO DE CONSUMO
        texto = Linha(texto,cons[0],None,[(1,"\n\nTABELA HISTÓRICO DE CONSUMO")])
        texto = Apagar_linhas(texto,[cons[0],cons[0]+3])                            # Apaga cabeçalho antigo
        texto = Linha(texto,cons[0]+1,None,[(1,headers[2])])                        # Insere o cabeçalho novo

        # TABELA DE TRIBUTOS
        texto = Linha(texto,pis[i]-1,None,[(1,"\n\nTABELA DE TRIBUTOS"+headers[1])])

        # IDENTIFICAÇÃO
        texto = Juntar(texto,[individual[i]+2,individual[i]+4,individual[i]+6,individual[i]+7,pis[i]-1],None) # Dados de identificação
        texto = Juntar(texto,(individual[i]+6,pis[i]-5),None) 
        texto = Juntar(texto,(individual[i]+4,individual[i]+5),None) 

        texto = Linha(texto,individual[i]+4,None,[(2,"\n\nCLIENTE E ENDEREÇO")])
        texto = Linha(texto,individual[i]+3,None,[(1,"\n\nDATAS E VALORES\nLEITURA ANTERIOR\tLEITURA ATUAL\tNº DE DIAS\tPRÓXIMA LEITURA\tMÊS/ANO\tVENCIMENTO\tEMISSÃO\tTOTAL A PAGAR")])
        texto = Linha(texto,individual[i]+1,None,[(0,"\nIDENTIFICAÇÃO\nCLASSIFICAÇÃO DA UNIDADE CONSUMIDORA\tTIPO DE FORNECIMENTO\tUNIDADE CONSUMIDORA\tNO DO CLIENTE\tCPF/CNPJ")])

    texto = re.sub(r' {2,}', "\t", texto)                                   # Por ser de linha única temos que deixar por último

    for i in range(0,len(individual)):
        individual  = Index(texto, "FATURA INDIVIDUAL")
        tribs       = Index(texto, "TABELA DE TRIBUTOS")
        cons        = Index(texto, "TABELA HISTÓRICO DE CONSUMO")
        desc        = Index(texto, "TABELA DE DESCRIÇÃO DO FATURAMENTO")
        med         = Index(texto, "TABELA DE EQUIPAMENTO DE MEDIÇÃO")

        texto = Linha(texto,individual[i]+9,None,[(6,Linha_para_Vetor(texto,individual[i]+9)[1])],None) # Data de emissão igual a de leitura vale apenass para a ENEL


        texto = alinhar_tabela_por_tabs(texto,individual[i]+3,individual[i]+5)
        texto = alinhar_tabela_por_tabs(texto,individual[i]+7,individual[i]+8)
        texto = alinhar_tabela_por_tabs(texto,tribs[i]+1,tribs[i]+4)
        texto = alinhar_tabela_por_tabs(texto,cons[i]+1,cons[i]+14)
        texto = alinhar_tabela_por_tabs(texto,desc[i]+1,med[i]-2)
        texto = alinhar_tabela_por_tabs(texto,med[i]+1,med[i]+2)

    return texto
def format_enel(texto, filename=None):
    # SUBSTITUIÇÃO DE CONTEÚDOS
    texto = texto.replace("HFP", "  HFP")       # Evita que haja sobreposição do numero do medidor com o horário de medição
    texto = re.sub("CEP: ","",          texto)  # Retira indicador na mesma linha da informação
    texto = re.sub("CPF/CNPJ: ","",     texto)  # Retira indicador na mesma linha da informação
    texto = re.sub(" INSC. EST:","",    texto)  # Retira informação inutil
    texto = re.sub("Grupo","\nGrupo",   texto)  # Eu não lembro pra que isso serve
    texto = re.sub("Preço","     ",     texto)  # Isso aqui é uma gambiarra e eu não me orgulho de fazer isso

    # ORGANIZAÇÃO GERAL
    texto = Justificar(texto)                   # Retira qualquer espaçamento anterior ao começo de cada linha e linhas vazias
    texto = texto.replace('\ufeff', '')         # Retira os caracteres invisivéis provenientes da extração do PDF

    if "CLASSIFICAÇÃO DA UNIDADE CONSUMIDORA" in texto:     # Para o caso do cabeçalho da fatura ser texto rastreável
        texto = enel_1(texto, filename)

    if "CLASSIFICAÇÃO DA UNIDADE CONSUMIDORA" not in texto: # Pro caso de apenas as informações possuirem texto nativo
        texto = enel_2(texto, filename)

    return texto
