import re
from pathlib import Path
from pypdf import PdfReader

def modificar_template_tex(substituicoes: dict[str, str]) -> None:
    """
    Modifica um arquivo .tex substituindo placeholders de forma segura.
    
    :param caminho_template: Caminho para o arquivo .tex original.
    :param caminho_saida: Caminho onde o novo arquivo .tex será salvo.
    :param substituicoes: Dicionário onde a chave é o placeholder e o valor é o texto novo.
                          Ex: {"<<EMPRESA>>": "RUDA", "% <<ADITIVOS>>": "\\item ..."}
    """
    caminho_template = Path(r"C:\Users\Usuário 1\Documents\Inovve_Automação\01 - UTILITÁRIOS\Documentaiser\Sumario.tex")
    caminho_saida = Path(r"C:\Users\Usuário 1\Documents\Inovve_Automação\01 - UTILITÁRIOS\Documentaiser\Resultado.tex")
    
    # 1. Lê o conteúdo do template em UTF-8
    conteudo = caminho_template.read_text(encoding="utf-8")
    
    # 2. Aplica cada substituição do dicionário
    for placeholder, valor_novo in substituicoes.items():
        # re.escape garante que caracteres como <<, >>, % ou [ ] sejam tratados como texto puro na busca
        padrao_busca = re.escape(placeholder)
        
        # O lambda garante que o valor_novo (mesmo cheio de barras do LaTeX) seja tratado como texto puro
        conteudo = re.sub(padrao_busca, lambda match: valor_novo, conteudo)
        
    # 3. Salva o resultado no arquivo de saída
    caminho_saida.write_text(conteudo, encoding="utf-8")

def calcular_paginas_acumuladas(paginas_anexos: list[int]) -> list[int]:
    # 1. Cria uma nova lista adicionando o número 1 no começo
    vetor_com_inicio = [1] + paginas_anexos
    
    # 2. Transforma o vetor fazendo a soma acumulada
    vetor_acumulado = []
    soma_atual = 0
    
    for termo in vetor_com_inicio:
        soma_atual += termo
        vetor_acumulado.append(soma_atual)
        
    return vetor_acumulado

def contar_paginas_pdf(caminho_pdf: str | Path) -> int:
    """
    Abre um arquivo PDF de forma rápida e retorna o número total de páginas.
    """
    # Garante que o caminho seja tratado corretamente pelo pathlib
    caminho = Path(caminho_pdf)
    
    # Se o arquivo não existir, evita erros e avisa
    if not caminho.exists():
        print(f"Erro: O arquivo {caminho.name} não foi encontrado.")
        return 0
        
    # Abre o leitor de PDF e pega o tamanho do vetor de páginas
    reader = PdfReader(caminho)
    return len(reader.pages)

print(contar_paginas_pdf(r"C:\Users\Usuário 1\OneDrive\PASTA ENERGIA 1\PARCEIROS\Municípios Thamires e Ruda\Paraíba\Aguiar\Documentos\Contratuais\documentaiser_export\AGUIAR - ANEXO I - INSTRUMENTOS PROCURATÓRIOS.pdf"))

[PROC, RAS_PROC, KIT]
[CRT, RAS_CRT,PUB_CRT]
[ADT_XX, RAS_ADT_XX, PUB_ADT_XX]




pags_anexo_i    = [1, 1, 1, 1]
pags_anexo_ii   = [1, 3, 2]
vetor_de_aditivos = [
    [1, 2],       # 1º Aditivo (tamanho 3: não tem validação)
    [1, 3, 4]    # 2º Aditivo (tamanho 4: tem validação)
]

pags_anexo_i    = calcular_paginas_acumuladas(pags_anexo_i)
pags_anexo_ii   = calcular_paginas_acumuladas(pags_anexo_ii)
vetor_de_aditivos = [calcular_paginas_acumuladas(aditivo) for aditivo in vetor_de_aditivos]

# Formação do Anexo I
if len(pags_anexo_i) in [5, 6]:
    paginas = iter(pags_anexo_i)      
    rel_ass_procuracao = fr"\item Validação das assinaturas \dotfill {next(paginas)}" if len(pags_anexo_i) == 6 else ""
    anexo_i = fr"""\textbf{{Anexo I -- Instrumentos procuratórios \dotfill 1}}
\begin{{enumerate}}
    \item Procuração \dotfill {next(paginas)} 
    {rel_ass_procuracao}
    \item Kit prefeito \dotfill {next(paginas)}
    \item Contrato Social da Empresa \dotfill {next(paginas)} 
    \item Documento de Identificação do Representante \dotfill {next(paginas)} 
\end{{enumerate}}"""
else:
    print("Quantidade de documentos do anexo 1 não válida.")

# Formação do Anexo II
if len(pags_anexo_ii) in [3, 4]:
    paginas = iter(pags_anexo_ii)    
    pg_contrato = next(paginas)    
    linha_valida_contrato = fr"    \item Validação das assinaturas \dotfill {next(paginas)}" if len(pags_anexo_ii) == 4 else ""    
    pg_publicacao = next(paginas)
    anexo_ii = fr"""\textbf{{Anexo II -- Documentos contratuais \dotfill 1}}
\begin{{enumerate}}
    \item Contrato \dotfill {pg_contrato}
{linha_valida_contrato}
    \item Publicação do Contrato em Diário Oficial \dotfill {pg_publicacao}
\end{{enumerate}}"""
else:
    print("Quantidade de documentos do anexo 2 não válida.")

# Formação dos Anexos de Aditivos
def to_roman(n):
    romanos = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII'}
    return romanos.get(n, str(n))

aditivos_acumulados_latex = ""

for idx, pags_aditivo in enumerate(vetor_de_aditivos, start=3):
    
    if len(pags_aditivo) in [3, 4]:
        paginas = iter(pags_aditivo)
        
        # 1. Dados de identificação do aditivo atual
        romano = to_roman(idx)       # III, IV, V...
        num_aditivo = idx - 2        # 1, 2, 3... (Se começa no índice 3, 3-2 = 1º Aditivo)
        
        pg_termo = next(paginas)        
        # 3. Condicional para a linha de validação de assinatura do aditivo
        linha_valida_aditivo = fr"    \item Validação das assinaturas do {num_aditivo}º Aditivo \dotfill {next(paginas)}" if len(pags_aditivo) == 4 else ""
        
        # pg_publicacao = next(paginas)
        
        # 4. Monta o bloco deste aditivo e adiciona na string acumuladora
        bloco_aditivo = fr"""\textbf{{Anexo {romano} -- {num_aditivo}º Termo Aditivo \dotfill 1}}
\begin{{enumerate}}
    \item {num_aditivo}º Aditivo \dotfill {pg_termo}
    {linha_valida_aditivo}
    \item Publicação do {num_aditivo}º Aditivo em Diário Oficial \dotfill {next(paginas)}
\end{{enumerate}}

"""
        aditivos_acumulados_latex += bloco_aditivo
        
    else:
        print(fr"Quantidade de documentos do aditivo (Anexo {to_roman(idx)}) não válida.")

modificadores = {
    "<<ANEXO I>>":              anexo_i,
    "<<ANEXO II>>":             anexo_ii,
    "<<ANEXO DE ADITIVOS>>":    aditivos_acumulados_latex,
    "<<EMPRESA>>":              "RUDA"
}
modificar_template_tex(modificadores)