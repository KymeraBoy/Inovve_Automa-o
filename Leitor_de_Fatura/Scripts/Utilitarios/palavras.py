from collections import Counter

def remover_palavras_repetidas_entre_vetores(lista_de_vetores):
    # Conta em quantos vetores cada palavra aparece
    contador = Counter()

    for vetor in lista_de_vetores:
        # usa set pra não contar repetido dentro do mesmo vetor
        palavras_unicas = set(vetor)
        contador.update(palavras_unicas)

    # filtra os vetores
    novos_vetores = []

    for vetor in lista_de_vetores:
        filtrado = [palavra for palavra in vetor if contador[palavra] == 1]
        novos_vetores.append(filtrado)

    return novos_vetores


# Exemplo de uso
vetores = [
   ['a', 'abr', 'acesso', 'ag', 'ago', 'aliq', 'alínea', 'apolonio', 'apresentaçâo', 'aracaju', 'art', 'atenção', 'atraso', 'automático', 'autorização', 'baixa', 'barbosa', 'base', 'beneficiário', 'br', 'c', 'cadastre', 'calc', 'cep', 'chave', 'classificação', 'cnpj', 'cofins', 'com', 'consulta', 'consulte', 'conta', 'contate', 'contingência', 'convencional', 'cpf', 'código', 'da', 'data', 'de', 'dez', 'dfe', 'disp', 'disponível', 'distrib', 'distribuição', 'do', 'documento', 'débito', 'em', 'emissâo', 'emitido', 'encargo', 'energia', 'energisa', 'est', 'esta', 'fatura', 'faturamento', 'faturas', 'fev', 'fica', 'fiscal', 'fornecimento', 'gov', 'https', 'icms', 'iluminação', 'inacio', 'inciso', 'insc', 'item', 'itens', 'iv', 'jan', 'jul', 'jun', 'kwh', 'lim', 'local', 'mai', 'mar', 'max', 'min', 'mtc', 'município', 'média', 'mínimo', 'n', 'no', 'nominal', 'nota', 'nov', 'o', 'out', 'paga', 'pagador', 'pagamento', 'para', 'partir', 'pasep', 'pela', 'pendente', 'pinhao', 'pis', 'portal', 'prefeitura', 'preço', 'problemas', 'pública', 'quant', 'r', 'rani', 'ref', 'residencial', 'responsabilidade', 'ricms', 'roteiro', 'rs', 'rua', 'sa', 'sales', 'se', 'sergipe', 'set', 'seu', 'sistema', 'sua', 'svrs', 'série', 'tarifa', 'tensão', 'tipo', 'total', 'tributos', 'unid', 'unit', 'uso', 'utilizando', 'valor', 'vencimento', 'volts', 'é'],
   ['a', 'abr', 'adequado', 'ag', 'ago', 'alíq', 'anterior', 'atual', 'baixa', 'banc', 'base', 'calc', 'cep', 'classificação', 'cnpj', 'cofins', 'com', 'compra', 'conjunto', 'conta', 'contratada', 'convencional', 'cpf', 'código', 'da', 'de', 'dez', 'dias', 'dic', 'dicri', 'diretos', 'distribuição', 'dmic', 'do', 'dom', 'domicílio', 'e', 'elétrica', 'encargos', 'endereço', 'energia', 'energisa', 'ent', 'entrega', 'est', 'fatura', 'faturamento', 'fev', 'fic', 'fiscal', 'icms', 'impostos', 'insc', 'jan', 'jul', 'jun', 'k', 'kwh', 'leitura', 'ligação', 'limite', 'mai', 'mar', 'matrícula', 'mtc', 'média', 'mínimo', 'nota', 'nov', 'out', 'outros', 'pagar', 'pela', 'pis', 'ponta', 'quantidade', 'r', 'rani', 'referência', 'roteiro', 'rua', 's', 'serviço', 'serviços', 'set', 'setoriais', 'tarifa', 'tensão', 'total', 'transmissão', 'tributos', 'valor', 'vencimento'],
]

resultado = remover_palavras_repetidas_entre_vetores(vetores)

for i, v in enumerate(resultado):
    print(f"Vetor {i+1}: {v}")