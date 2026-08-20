import re

# ============================================================== #
# CONSTANTES
# ============================================================== #

headers = [ "\nTABELA DA FATURA AGRUPADA\nVALORES DA FATURA\tTOTAL MEDIDO\tVALORES (R$)",   # TABELA DA FATURA AGRUPADA
            "\nTRIBUTOS\tBASE CALC (R$)\tALÍQUOTA(%)\tVALOR(R$)",                           # TABELA DE TRIBUTOSS
            "\nMÊS/ANO\tCONSUMO FATURADO\tDIAS\tTIPOS DE FATURAMENTO",                      # TABELA HISTÓRICO DE CONSUMO
            "\nItens de Fatura\tUnid\tQuant\tPreço unit com tributos (R$)\tValor (R$)\tPIS/COFINS\tBase Calc ICMS (R$)\tAlíquota ICMS\tICMS\tTarifa unit (R$)",  # TABELA DA DESCRIÇÃO DO FATURAMENTO
            "\nGRUPO\tEMISSÃO\tUNIDADE CONSUMIDORA\tVENCIMENTO\tTOTAL A PAGAR\tCPF/CNPJ"    # CABEÇALHO DA FATURA AGRUPADA
]
marcadores = ["DESTINO","MÊS_ANO","UNIDADE","CLASSIFICAÇÃO","FORNECIMENTO","HISTÓRICO_DE_CONSUMO","DADOS_DO_FATURAMENTO","TABELA_DE_TRIBUTOS","INDICADORES_DE_QUALIDADE","DADOS_DE_MEDIÇÃO"]
fornecimento = ["MONOFASICO","BIFASICO","TRIFASICO"]

# ============================================================== #
# ESTADO COMPARTILHADO
# ============================================================== #

aba_info_geral = []
aba_historico_consumo = []
historico = []


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
