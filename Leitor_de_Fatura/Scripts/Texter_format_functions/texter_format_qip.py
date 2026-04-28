import re

from texter_utils import (Apagar_linhas, Justificar, Linha,
                          alinhar_tabela_por_tabs, Linha_para_Vetor)

# ============================================================== #
# EXECUÇÃO - QIP
# ============================================================== #

def format_qip(texto, filename=None):
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
