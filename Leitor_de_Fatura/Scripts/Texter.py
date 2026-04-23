# ============================================================== #
#     BIBLIOTECAS 
# ============================================================== #

import os
import re
import math
from pdf2image import convert_from_path
import numpy as np
import cv2
import sys
import pandas as pd
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from collections import defaultdict

# ============================================================== #
# CONFIGURAÇÕES
# ============================================================== #

PATH_INPUT          = "Faturas_Poppler" 
PATH_OUTPUT         = "Faturas_Texter" 
CABECALHO_PADRAO    = "RELATORIO DE FATURA - SISTEMA INTEGRALAISER\n" + ("=" * 50) + "\n"
headers = [ "\nTABELA DA FATURA AGRUPADA\nVALORES DA FATURA\tTOTAL MEDIDO\tVALORES (R$)",   # TABELA DA FATURA AGRUPADA
            "\nTRIBUTOS\tBASE CALC (R$)\tALÍQUOTA(%)\tVALOR(R$)",                           # TABELA DE TRIBUTOSS
            "\nMÊS/ANO\tCONSUMO FATURADO\tDIAS\tTIPOS DE FATURAMENTO",                      # TABELA HISTÓRICO DE CONSUMO
            "\nItens de Fatura\tUnid\tQuant\tPreço unit com tributos (R$)\tValor (R$)\tPIS/COFINS\tBase Calc ICMS (R$)\tAlíquota ICMS\tICMS\tTarifa unit (R$)",  # TABELA DA DESCRIÇÃO DO FATURAMENTO
            "\nGRUPO\tEMISSÃO\tUNIDADE CONSUMIDORA\tVENCIMENTO\tTOTAL A PAGAR\tCPF/CNPJ"    # CABEÇALHO DA FATURA AGRUPADA
]
marcadores = ["DESTINO","MÊS_ANO","UNIDADE","CLASSIFICAÇÃO","FORNECIMENTO","HISTÓRICO_DE_CONSUMO","DADOS_DO_FATURAMENTO","TABELA_DE_TRIBUTOS","INDICADORES_DE_QUALIDADE","DADOS_DE_MEDIÇÃO"]
fornecimento = ["MONOFASICO","BIFASICO","TRIFASICO"]
matriz = []
historico = []
consumo = []

# ============================================================== #
# FUNÇÕES
# ============================================================== #

# Funções de interface
def salvar_arquivo(caminho, conteudo):
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(conteudo)
def carregar_arquivo(caminho):
    with open(caminho, 'r', encoding='utf-8') as f:
        return f.read()

# Funções de setup do programa
def Justificar(texto, inicio=None, fim=None):
    linhas = texto.splitlines(keepends=True)

    # Se nenhum intervalo for passado → aplica no texto inteiro
    if inicio is None and fim is None:
        linhas = [linha.lstrip() for linha in linhas]
        return "".join(linhas)

    # Segurança de limites
    inicio = max(0, inicio)
    fim = len(linhas) if fim is None else min(len(linhas), fim)

    for i in range(inicio, fim):
        linhas[i] = linhas[i].lstrip()

    return "".join(linhas)
def Etiquetar(texto):
    if texto is None:
        return texto
    linhas = texto.splitlines(keepends=True)

    # Inserções fixas
    linhas.insert(0, "CAPA\n\n")
    if len(linhas) >= 5:
        linhas.insert(5, "\nFATURA AGRUPADA\n\n")
    else:
        linhas.append("\nFATURA AGRUPADA\n\n")

    gatilho = "CLASSIFICAÇÃO DA UNIDADE CONSUMIDORA"
    contador = 0
    resultado = []

    for linha in linhas:
        if gatilho in linha:
            contador += 1
            marcador = f"\nFATURA INDIVIDUAL {contador}\n\n"
            resultado.append(marcador)
        if "CONSUMO / kWh" in linha:
            resultado.append("\nTABELA HISTÓRICO DE CONSUMO\n")         # Etiqueta da tabela de histórico de consumo
        if "TRIBUTOS     BASE"in linha:
            resultado.append("\nTABELA DE TRIBUTOS\n")                  # Etiqueta da tabela de tributos
        if "DESCRIÇÃO DO FATURAMENTO" in linha:
            resultado.append("\nTABELA DE DESCRIÇÃO DO FATURAMENTO\n")  # Etiqueta da tabela de descrição do faturamento
        if "EQUIPAMENTOS DE MEDIÇÃO E CONSUMO NO PERIODO" in linha:
            resultado.append("\nTABELA DE EQUIPAMENTO DE MEDIÇÃO\n")    # Etiqueta da tabela de equipamento de medição
        resultado.append(linha)

    return "".join(resultado)

# Funções de manipulação específicas
def Index(texto, termo):
    # Essa função encontra todos os index de linhaas contendo um termo e lista elas em um vetor
    linhas = texto.splitlines()
    indices = []

    for i, linha in enumerate(linhas):
        if termo in linha:
            indices.append(i)

    return indices
def Linha(texto,index,remover_pos=None,adicionar_itens=None,trocar_pos=None,linhas_brancas_antes=0):

    if texto is None:
        return texto

    linhas = texto.splitlines()

    if index < 0 or index >= len(linhas):
        return texto

    linha = linhas[index]

    # Prefixar quebras de linha antes (como você definiu)
    if linhas_brancas_antes > 0:
        linha = ("\n" * linhas_brancas_antes) + linha

    # Separar por tabulação
    vetor = linha.split("\t")

    # --- REMOVER POSIÇÕES ---
    if remover_pos:
        for pos in sorted(remover_pos, reverse=True):
            if 0 <= pos < len(vetor):
                vetor.pop(pos)

    # --- ADICIONAR ITENS ---
    if adicionar_itens:
        for pos, valor in adicionar_itens:
            if 0 <= pos <= len(vetor):
                vetor.insert(pos, valor)

    # --- TROCAR POSIÇÕES ---
    if trocar_pos is not None:
        for pos_antiga, pos_nova in trocar_pos:
            if (
                isinstance(pos_antiga, int) and
                isinstance(pos_nova, int) and
                0 <= pos_antiga < len(vetor)
            ):
                item = vetor.pop(pos_antiga)

                # Ajuste caso o item tenha sido removido antes da nova posição
                if pos_antiga < pos_nova:
                    pos_nova -= 1

                if pos_nova < 0:
                    pos_nova = 0
                if pos_nova > len(vetor):
                    pos_nova = len(vetor)

                vetor.insert(pos_nova, item)

    # Reconstruir linha
    nova_linha = "\t".join(vetor)

    # Atualizar no texto
    linhas[index] = nova_linha

    return "\n".join(linhas)
def Apagar_linhas(texto, indices=None, intervalo=None, apenas_vazias=False):
    """
    Remove linhas de um texto com base em uma lista de índices ou um intervalo.
    
    :param texto: String contendo o texto original.
    :param indices: Lista de inteiros representando os índices das linhas a remover.
    :param intervalo: Tupla (inicio, fim) representando o intervalo inclusivo de linhas.
    :param apenas_vazias: Se True, remove apenas se a linha estiver vazia/espaços.
    :return: Texto modificado.
    """
    linhas = texto.splitlines()
    set_indices_remover = set()

    # 1. Definir quais índices estão na mira para remoção
    if indices:
        set_indices_remover.update(indices)
    
    if intervalo:
        inicio, fim = intervalo
        set_indices_remover.update(range(inicio, fim + 1))

    novas_linhas = []

    for i, linha in enumerate(linhas):
        # Se a linha está marcada para remoção
        if i in set_indices_remover:
            # Se a opção 'apenas_vazias' estiver ativa, só remove se não houver conteúdo
            if apenas_vazias:
                if linha.strip(): # Se a linha tiver conteúdo, ela fica
                    novas_linhas.append(linha)
                # Caso contrário (vazia), ela não entra na lista (é removida)
            else:
                # Se não for apenas vazias, remove incondicionalmente (não adiciona)
                continue
        else:
            # Linhas fora do alvo sempre permanecem
            novas_linhas.append(linha)

    # 4. Retornar o texto com as alterações
    # Preserva a quebra de linha final se existia no original
    resultado = "\n".join(novas_linhas)
    if texto.endswith("\n") and not resultado.endswith("\n"):
        resultado += "\n"
        
    return resultado
def Juntar(texto, selecao, destino=None):
    if texto is None:
        return texto

    linhas = texto.splitlines(keepends=True)
    total = len(linhas)

    # --- Normalizar seleção ---
    if isinstance(selecao, int):
        indices = [selecao]

    elif isinstance(selecao, tuple) and len(selecao) == 2:
        inicio, fim = selecao
        if inicio > fim:
            inicio, fim = fim, inicio
        indices = list(range(inicio, fim + 1))

    elif isinstance(selecao, list):
        indices = selecao[:]

    else:
        return texto

    # Filtrar índices válidos
    indices = sorted(set(i for i in indices if 0 <= i < total))
    if not indices:
        return texto

    # --- Combinar conteúdo ---
    partes = [linhas[i].rstrip("\n") for i in indices]
    nova_linha = "\t".join(partes) + "\n"

    # --- Definir destino padrão ---
    if destino is None:
        destino = indices[0]

    # --- Remover linhas originais ---
    for i in reversed(indices):
        del linhas[i]

    # Ajustar destino após remoções
    removidos_antes = sum(1 for i in indices if i < destino)
    destino -= removidos_antes

    if destino < 0:
        destino = 0
    if destino > len(linhas):
        destino = len(linhas)

    # --- Inserir nova linha ---
    linhas.insert(destino, nova_linha)

    return "".join(linhas)
def formatar_tabela_complexa(texto, index_inicio, index_fim):
    # 1. Receber o intervalo e separar o texto
    linhas_originais = texto.splitlines()
    intervalo = linhas_originais[index_inicio : index_fim + 1]
    antes = linhas_originais[:index_inicio]
    depois = linhas_originais[index_fim + 1:]

    if not intervalo:
        return texto

    # 3. Transformar em matriz (cada caractere é um elemento)
    max_len = max(len(l) for l in intervalo)
    matriz_chars = [list(linha.ljust(max_len)) for linha in intervalo]

    # 4. Identificar colunas compostas unicamente por espaços vazios
    colunas_vazias = []
    for j in range(max_len):
        if all(matriz_chars[i][j] == " " for i in range(len(matriz_chars))):
            colunas_vazias.append(j)

    # 5. Substituir colunas vazias por "\t"
    novas_linhas = []
    for i in range(len(matriz_chars)):
        linha_str = ""
        j = 0
        while j < max_len:
            if j in colunas_vazias:
                linha_str += "\t"
                while j + 1 < max_len and (j + 1) in colunas_vazias:
                    j += 1
            else:
                linha_str += matriz_chars[i][j]
            j += 1
        novas_linhas.append(linha_str)

    # 6 e 7. Regras de "0" entre tabs e eliminação de espaços adjacentes
    processadas = []
    for linha in novas_linhas:
        linha = re.sub(r' +(?=\t)', '', linha)
        linha = re.sub(r'(?<=\t) +', '', linha)
        
        while "\t \t" in linha or "\t\t" in linha.replace(" ", ""):
             if re.search(r'\t +\t', linha):
                 linha = re.sub(r'\t +\t', '\t0\t', linha)
             elif "\t\t" in linha:
                 linha = linha.replace("\t\t", "\t0\t")
             else:
                 break
        processadas.append(linha)

    # 8 e 9. Vetores e exclusão de elementos vazios
    vetores_limpos = []
    for l in processadas:
        v = l.split('\t')
        v_limpo = [elem for elem in v if elem != ""]
        vetores_limpos.append(v_limpo)

    # 10. Equalizar tamanho dos vetores com "0"
    max_elementos = max(len(v) for v in vetores_limpos) if vetores_limpos else 0
    for v in vetores_limpos:
        while len(v) < max_elementos:
            v.append("0")

    # --- NOVA REGRA: Exclusão de colunas onde todos os termos são "0" ---
    indices_para_excluir = []
    if max_elementos > 0:
        for j in range(max_elementos):
            # Verifica se em todas as linhas o elemento no índice j é "0"
            coluna_toda_zero = all(vetores_limpos[i][j] == "0" for i in range(len(vetores_limpos)))
            if coluna_toda_zero:
                indices_para_excluir.append(j)

    # Remove os itens de trás para frente para não bagunçar os índices durante a remoção
    for i in range(len(vetores_limpos)):
        for indice in reversed(indices_para_excluir):
            vetores_limpos[i].pop(indice)

    # Reconstrução final do documento
    intervalo_final = ["\t".join(v) for v in vetores_limpos]
    return "\n".join(antes + intervalo_final + depois)
def alinhar_tabela_por_tabs(texto, index_inicio, index_fim):
    linhas = texto.splitlines()
    # Isolar o intervalo e preservar o restante do documento
    antes = linhas[:index_inicio]
    intervalo = linhas[index_inicio : index_fim + 1]
    depois = linhas[index_fim + 1:]

    # Transformar o intervalo em matriz, separando por '\t'
    matriz = [linha.split('\t') for linha in intervalo]
    
    if not matriz:
        return texto

    num_colunas = max(len(linha) for linha in matriz)
    
    # Identificar o "tab stop" alvo para cada coluna
    # O alvo deve ser o próximo múltiplo de 8 após o maior elemento da coluna
    alvos_tab_stop = []
    for j in range(num_colunas):
        max_largura = 0
        for i in range(len(matriz)):
            if j < len(matriz[i]):
                max_largura = max(max_largura, len(matriz[i][j]))
        
        # Próximo múltiplo de 8. Se max for 15, alvo é 16. Se for 16, alvo é 24.
        alvo = ((max_largura // 8) + 1) * 8
        alvos_tab_stop.append(alvo)

    # Aplicar o alinhamento inserindo a quantidade correta de '\t'
    for i in range(len(matriz)):
        for j in range(len(matriz[i])):
            # Não alinhar a última coluna da linha (evita tabs inúteis no fim)
            if j < len(matriz[i]) - 1:
                elemento = matriz[i][j]
                largura_atual = len(elemento)
                alvo_da_coluna = alvos_tab_stop[j]
                
                # O cursor para no múltiplo de 8 anterior à largura atual
                posicao_cursor_atual = (largura_atual // 8) * 8
                
                # Calcula quantos saltos de 8 são necessários para chegar no alvo
                tabs_necessarios = (alvo_da_coluna - posicao_cursor_atual) // 8
                
                matriz[i][j] = elemento + ('\t' * tabs_necessarios)

    # Recompor o texto
    intervalo_formatado = ["".join(linha) for linha in matriz]
    return "\n".join(antes + intervalo_formatado + depois)


def Linha_para_Vetor(texto, index):
    linhas = texto.splitlines()
    return re.split(r'\t+', linhas[index].strip())
def Index_duplo(texto, termo_1,termo_2):
    mon = Index(texto, termo_1)
    tri = Index(texto, termo_2)
    fase = sorted(mon+tri)
    return fase
def formatar_e_alinhar_tabela(texto, index_inicio, index_fim):
    linhas_originais = texto.splitlines()
    intervalo = linhas_originais[index_inicio : index_fim + 1]
    antes = linhas_originais[:index_inicio]
    depois = linhas_originais[index_fim + 1:]

    if not intervalo:
        return texto

    # Etapa 1: converter colunas vazias em tabs
    max_len = max(len(l) for l in intervalo)
    matriz_chars = [list(linha.ljust(max_len)) for linha in intervalo]

    colunas_vazias = []
    for j in range(max_len):
        if all(matriz_chars[i][j] == " " for i in range(len(matriz_chars))):
            colunas_vazias.append(j)

    novas_linhas = []
    for i in range(len(matriz_chars)):
        linha_str = ""
        j = 0
        while j < max_len:
            if j in colunas_vazias:
                linha_str += "\t"
                while j + 1 < max_len and (j + 1) in colunas_vazias:
                    j += 1
            else:
                linha_str += matriz_chars[i][j]
            j += 1
        novas_linhas.append(linha_str)

    # Etapa 2: limpar espaços e preencher lacunas com "0"
    processadas = []
    for linha in novas_linhas:
        linha = re.sub(r' +(?=\t)', '', linha)
        linha = re.sub(r'(?<=\t) +', '', linha)

        while "\t \t" in linha or "\t\t" in linha.replace(" ", ""):
            if re.search(r'\t +\t', linha):
                linha = re.sub(r'\t +\t', '\t0\t', linha)
            elif "\t\t" in linha:
                linha = linha.replace("\t\t", "\t0\t")
            else:
                break
        processadas.append(linha)

    vetores_limpos = []
    for l in processadas:
        v = l.split('\t')
        v_limpo = [elem for elem in v if elem != ""]
        vetores_limpos.append(v_limpo)

    max_elementos = max(len(v) for v in vetores_limpos) if vetores_limpos else 0
    for v in vetores_limpos:
        while len(v) < max_elementos:
            v.append("0")

    indices_para_excluir = []
    if max_elementos > 0:
        for j in range(max_elementos):
            if all(vetores_limpos[i][j] == "0" for i in range(len(vetores_limpos))):
                indices_para_excluir.append(j)

    for i in range(len(vetores_limpos)):
        for indice in reversed(indices_para_excluir):
            vetores_limpos[i].pop(indice)

    # Etapa 3: alinhar por tabs
    matriz = vetores_limpos
    if not matriz:
        return "\n".join(antes + depois)

    num_colunas = max(len(linha) for linha in matriz)

    alvos_tab_stop = []
    for j in range(num_colunas):
        max_largura = 0
        for i in range(len(matriz)):
            if j < len(matriz[i]):
                max_largura = max(max_largura, len(matriz[i][j]))

        alvo = ((max_largura // 8) + 1) * 8
        alvos_tab_stop.append(alvo)

    for i in range(len(matriz)):
        for j in range(len(matriz[i])):
            if j < len(matriz[i]) - 1:
                elemento = matriz[i][j]
                largura_atual = len(elemento)
                alvo_da_coluna = alvos_tab_stop[j]
                posicao_cursor_atual = (largura_atual // 8) * 8
                tabs_necessarios = (alvo_da_coluna - posicao_cursor_atual) // 8
                matriz[i][j] = elemento + ('\t' * tabs_necessarios)

    intervalo_formatado = ["".join(linha) for linha in matriz]
    return "\n".join(antes + intervalo_formatado + depois)

def normalizar_tipo_fornecimento(texto):
    if texto is None:
        return texto

    # Padroniza sem acento e no masculino para evitar variações de OCR/layout.
    texto = re.sub(r'\bMONOF[ÁA]SIC[AO]\b', 'MONOFASICO', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\bBIF[ÁA]SIC[AO]\b', 'BIFASICO', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\bTRIF[ÁA]SIC[AO]\b', 'TRIFASICO', texto, flags=re.IGNORECASE)

    return texto

# ============================================================== #
# EXECUÇÃO
# ============================================================== #

def enel_1(texto):
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
    if any(linha[0] == vetor[0] for linha in matriz) == False:
        matriz.append(vetor)
    
    consumo
    vetor = []
    index = Index(texto,"HISTÓRICO_DE_CONSUMO:")
    vetor.append(Linha_para_Vetor(texto,Index(texto,info[0])[0])[1])
    for i in range(index[0]+1,index[0]+13):
        linha = Linha_para_Vetor(texto,i)
        if len(linha) == 1:
            linha.append("UNK")
        vetor.append((linha[0],linha[1]))
    consumo.append(vetor)
    return texto

def format_qip(texto,filename=None):
    texto = texto.replace('\ufeff', '')         # Retira os caracteres invisivéis provenientes da extração do PDF
    texto = Apagar_linhas(texto,None,(0,len(texto.splitlines())),True)
    texto = Apagar_linhas(texto,[17,34,51])
    texto = Justificar(texto)
    
    texto = re.sub(r' {2,}', "\t", texto)
    texto = Linha(texto,0,None,[(1,"\nTipo da Lâmpada\tCódigo Lâmpada\tPotência (W)\tPerda Reator (W)\tPerda Relé (W)\tPotência Total (W)\tQuantidade de Lâmpadas\tConsumo Estimado (kWh)")])
    texto = Apagar_linhas(texto,[2])
    texto = alinhar_tabela_por_tabs(texto,1,len(texto.splitlines())-1)

    linhas = texto.splitlines()    
    # 1. Pegamos a primeira linha e dividimos pelos espaços
    partes = linhas[0].split() # Ex: ['LUCENA', '01', '2014']
    
    if len(partes) >= 3:
        mes_num = partes[-2] # Pega o '01'
        ano_longo = partes[-1] # Pega o '2014'
        
        # 2. Mapeamento rápido de número para abreviação
        meses_map = {
            "01": "JAN", "02": "FEV", "03": "MAR", "04": "ABR",
            "05": "MAI", "06": "JUN", "07": "JUL", "08": "AGO",
            "09": "SET", "10": "OUT", "11": "NOV", "12": "DEZ"
        }
        
        # 3. Formata: Mês abreviado / final do ano (os últimos 2 dígitos)
        nova_data = f"{meses_map.get(mes_num, 'INV')}/{ano_longo[-2:]}"
        
        # Substitui apenas a primeira linha
        linhas[0] = nova_data
    texto = "\n".join(linhas)
    texto = re.sub(r'([a-zA-Zá-úÁ-Ú]) (\d)', r'\1\t\2', texto)

    texto=texto.replace(',','')
    texto=texto.replace('.',',')
    


    

    
    

    

    return texto


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
        if not any(sub[0] == chave for sub in matriz):
            matriz.append(vetor)
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

# MAPEAMENTO DAS FUNÇÕES DE FORMATAÇÃO
FORMATADORES = {
    "ENEL": format_enel,
    "ENERGISA": format_energisa,
    "NEOENERGIA":format_neoenergia,    
    "QIP":format_qip,
}

# ORQUESTRADOR
def texter_orchestrator():
    if not os.path.exists(PATH_OUTPUT):
        os.makedirs(PATH_OUTPUT)

    # 1. Seleção de Subpasta
    subfolders = [f for f in os.listdir(PATH_INPUT) if os.path.isdir(os.path.join(PATH_INPUT, f))]
    print("\n--- SELEÇÃO DE PASTA (ORIGEM: POPPLER) ---")
    for i, folder in enumerate(subfolders):
        print(f"{i} - {folder}")
    
    f_choice = int(input("Índice da pasta: "))
    selected_subfolder = subfolders[f_choice]
    
    src_dir = os.path.join(PATH_INPUT, selected_subfolder)
    # Regra: Trocar "Poppler" por "Texter" no nome da pasta
    dst_dir_name = selected_subfolder.replace("Poppler", "Texter")
    dst_dir = os.path.join(PATH_OUTPUT, dst_dir_name)
    
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    # 2. Seleção de Formatação
    print("\n--- QUAL FORMATAÇÃO APLICAR? ---")
    formatos = list(FORMATADORES.keys())
    for i, nome in enumerate(formatos):
        print(f"{i} - {nome}")
    fmt_choice = int(input("Índice do formato: "))
    print(fmt_choice)
    funcao_formatadora = FORMATADORES[formatos[fmt_choice]]

    # 3. Escopo de Execução
    print("\n--- MODO DE EXECUÇÃO ---")
    print("1 - Todos os documentos da subpasta")
    print("2 - Apenas um documento específico")
    mode = input("Escolha a opção: ")

    files = [f for f in os.listdir(src_dir) if f.lower().endswith('.txt')]

    if mode == "2":
        global consumo
        for i, f in enumerate(files):
            print(f"{i} - {f}")
        file_choice = int(input("Índice do arquivo: "))
        files = [files[file_choice]]

    # 4. Processamento
    for file_name in files:
        input_path = os.path.join(src_dir, file_name)
        # Regra: Trocar nome do arquivo
        output_name = file_name.replace("Poppler", "Texter")
        output_path = os.path.join(dst_dir, output_name)
        
        print(f"Formatando: {file_name}...")
        
        conteudo_bruto = carregar_arquivo(input_path)
        conteudo_formatado = funcao_formatadora(conteudo_bruto, file_name)
        
        salvar_arquivo(output_path, conteudo_formatado) 



    # 5. Análises
    if fmt_choice == 1:
        # 5.1 Área da MATRIZ DE IDENTIFICAÇÃO
        colunas_base_identificacao = ["UNIDADE", "FORNECIMENTO", "NÍVEL DE TENSÃO", "CÓDIGO", "CLASSIFICAÇÃO", "DESTINO", "ENDEREÇO"]
        max_colunas_identificacao = max((len(linha) for linha in matriz), default=0)

        cabecalho_identificacao = []
        for i in range(max_colunas_identificacao):
            if i < len(colunas_base_identificacao):
                cabecalho_identificacao.append(colunas_base_identificacao[i])
            elif i == max_colunas_identificacao - 1:
                cabecalho_identificacao.append("COMPLEMENTO")
            else:
                cabecalho_identificacao.append(f"CAMPO_{i+1}")

        identificacao = [cabecalho_identificacao] + matriz if max_colunas_identificacao > 0 else []

        # 5.2 Área da MATRIZ DE CONSUMO
        grupos = defaultdict(list)
        for linha in consumo:
            chave = linha[0]
            grupos[chave].extend(linha[1:])

        consumo_agrupado = []
        for chave, valores in grupos.items():
            consumo_agrupado.append([chave] + valores)

        meses = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
            "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
            "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
        }

        def parse_data(data_str):
            mes, ano = data_str.split("/")
            mes = mes.strip().upper()
            ano = re.sub(r"\D", "", ano)

            if len(ano) == 0:
                raise ValueError(f"Ano inválido em: {data_str}")

            return (2000 + int(ano), meses[mes])

        def transformar(matriz_consumo):
            datas = set()
            for linha in matriz_consumo:
                for d, _ in linha[1:]:
                    datas.add(d)

            datas_ordenadas = sorted(datas, key=parse_data)

            resultado = []
            resultado.append(["DATA"] + datas_ordenadas)

            for linha in matriz_consumo:
                id_ = linha[0]
                mapa = {d: v for d, v in linha[1:]}

                nova_linha = [id_]
                for d in datas_ordenadas:
                    nova_linha.append(mapa.get(d, "UNK"))

                resultado.append(nova_linha)

            return resultado

        consumo_tratado = transformar(consumo_agrupado)

        # 5.3 Formação da planilha (cada matriz em uma aba)
        df_identificacao = pd.DataFrame(identificacao)
        df_consumo = pd.DataFrame(consumo_tratado)

        nome_planilha = os.path.basename(os.path.normpath(dst_dir)).replace("Texter", "Analaiser") + ".xlsx"
        arquivo = os.path.join(dst_dir, nome_planilha)

        with pd.ExcelWriter(arquivo, engine="openpyxl") as writer:
            df_identificacao.to_excel(writer, sheet_name="Identificacao", index=False, header=False)
            df_consumo.to_excel(writer, sheet_name="Consumo", index=False, header=False)

        # 5.4 Formatação visual da planilha
        from openpyxl import load_workbook

        wb = load_workbook(arquivo)

        # Estilos base
        fonte_padrao   = Font(name="Verdana", size=8)
        fonte_cabecalho= Font(name="Verdana", size=8, bold=True)
        alinhamento    = Alignment(horizontal="center", vertical="center")
        borda_fina     = Side(style="thin")
        borda          = Border(left=borda_fina, right=borda_fina, top=borda_fina, bottom=borda_fina)
        fill_claro     = PatternFill(fill_type="solid", fgColor="FFFFFF")
        fill_escuro    = PatternFill(fill_type="solid", fgColor="DCE6F1")  # azul claro alternado

        def formatar_aba(ws, cabecalho=True, alternado=False):
            # Ajuste de largura por coluna
            for col in ws.columns:
                col_letter = get_column_letter(col[0].column)
                largura_max = 0
                for cell in col:
                    if cell.value is not None:
                        largura_max = max(largura_max, len(str(cell.value)))
                ws.column_dimensions[col_letter].width = max(largura_max + 2, 8)

            # Formatação célula a célula
            for row_idx, row in enumerate(ws.iter_rows(), start=1):
                eh_cabecalho = (row_idx == 1 and cabecalho)
                for cell in row:
                    cell.font      = fonte_cabecalho if eh_cabecalho else fonte_padrao
                    cell.alignment = alinhamento
                    cell.border    = borda
                    if alternado and not eh_cabecalho:
                        cell.fill = fill_escuro if row_idx % 2 == 0 else fill_claro
                    elif eh_cabecalho:
                        cell.fill = fill_claro

        formatar_aba(wb["Identificacao"], cabecalho=True, alternado=True)
        formatar_aba(wb["Consumo"],       cabecalho=True, alternado=False)

        wb.save(arquivo)


    if fmt_choice == 2:
        # ANALISADOR NEOENERGIA (CELPE)
        agrupados = defaultdict(list)
        global historico
        consumo
        for v in historico:
            chave = v[0]
            agrupados[chave].extend(v[1:])  # junta os valores
            resultado = [[k] + valores for k, valores in agrupados.items()]    
        historico = [[v[0]] + list(set(v[1:])) for v in resultado]
        meses = [tupla[0] for subvetor in historico for tupla in subvetor if isinstance(tupla, tuple)]
        meses = list(set(meses))
        ordem_meses = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
            "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
            "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
        }
        meses = sorted(
            meses,
            key=lambda x: (int(x[3:]), ordem_meses[x[:3]])
        )
        meses_index = {mes: i for i, mes in enumerate(meses)}
        resultado = []
        resultado.append(meses)
        resultado[0].insert(0,"UCs")
        for subvetor in historico:
            chave = subvetor[0]
            # inicializa com zeros (um para cada mês)
            valores = ["UNK"] * len(meses)
            # percorre as tuplas do subvetor
            for item in subvetor[1:]:
                if isinstance(item, tuple):
                    mes, valor = item
                    if mes in meses_index:
                        idx = meses_index[mes]
                        valores[idx] = valor
            resultado.append([chave] + valores)
            historico = resultado

        # CONSUMO
        for v in consumo:
            chave = v[0]
            agrupados[chave].extend(v[1:])  # junta os valores
            resultado = [[k] + valores for k, valores in agrupados.items()]    
        consumo = [[v[0]] + list(set(v[1:])) for v in resultado]
        meses = [tupla[0] for subvetor in consumo for tupla in subvetor if isinstance(tupla, tuple)]
        meses = list(set(meses))
        ordem_meses = {
            "JAN": 1, "FEV": 2, "MAR": 3, "ABR": 4,
            "MAI": 5, "JUN": 6, "JUL": 7, "AGO": 8,
            "SET": 9, "OUT": 10, "NOV": 11, "DEZ": 12
        }
        meses = sorted(
            meses,
            key=lambda x: (int(x[3:]), ordem_meses[x[:3]])
        )
        meses_index = {mes: i for i, mes in enumerate(meses)}
        resultado = []
        resultado.append(meses)
        resultado[0].insert(0,"UCs")
        for subvetor in consumo:
            chave = subvetor[0]
            # inicializa com zeros (um para cada mês)
            valores = ["UNK"] * len(meses)
            # percorre as tuplas do subvetor
            for item in subvetor[1:]:
                if isinstance(item, tuple):
                    mes, valor = item
                    if mes in meses_index:
                        idx = meses_index[mes]
                        valores[idx] = valor
            resultado.append([chave] + valores)
            consumo = resultado

        df = pd.DataFrame(matriz)    
        df.to_excel(os.path.join(dst_dir, "enquadramentos.xlsx"), index=False, header=False)
        df = pd.DataFrame(historico)
        df.to_excel(os.path.join(dst_dir, "historico.xlsx"), index=False, header=False)
        df = pd.DataFrame(consumo)
        df.to_excel(os.path.join(dst_dir, "consumo.xlsx"), index=False, header=False)

if __name__ == "__main__":
    texter_orchestrator()