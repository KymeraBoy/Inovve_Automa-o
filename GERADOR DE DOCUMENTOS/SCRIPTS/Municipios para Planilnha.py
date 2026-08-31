import re
import pandas as pd
from pathlib import Path

def extrair_dados_tex(caminho_arquivo):
    """
    Lê um arquivo .tex e extrai todos os pares \newcommand{\chave}{valor}
    """
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    # Regex para capturar \newcommand{\nomeDoComando}{Conteudo}
    # re.DOTALL (re.S) garante que o .* capture quebras de linha (útil para a \clausula)
    padrao = r'\\newcommand\{\\([^}]+)\}\{(.*?)\}(?=\s*(?:\\newcommand|\\input|%|$))'
    
    matches = re.findall(padrao, conteudo, flags=re.DOTALL)
    
    dados_municipio = {}
    for chave, valor in matches:
        # Limpa espaços em branco ou quebras de linha nas pontas
        valor_limpo = valor.strip()
        
        # Remove comentários ao final da linha se existirem (ex: % Número do contrato)
        valor_limpo = re.sub(r'%.*$', '', valor_limpo).strip()
        
        dados_municipio[chave] = valor_limpo
        
    return dados_municipio

def tex_para_excel(pasta_origem, arquivo_saida_excel):
    pasta = Path(pasta_origem)
    arquivo_saida_excel = Path(arquivo_saida_excel)
    lista_municipios = []

    # Processa todos os arquivos .tex na pasta
    for arquivo in sorted(pasta.glob("Dados_*.tex")):
        dados = extrair_dados_tex(arquivo)
        if dados:
            # Adiciona o nome do arquivo como referência (opcional, mas muito útil)
            dados['_arquivo_origem'] = arquivo.name 
            lista_municipios.append(dados)

    if not lista_municipios:
        print("Nenhum comando encontrado ou nenhum arquivo .tex localizado.")
        return

    # Converte a lista de dicionários para um DataFrame do Pandas
    df = pd.DataFrame(lista_municipios)
    
    # Reorganiza para que '_arquivo_origem' fique como primeira coluna
    colunas = ['_arquivo_origem'] + [c for c in df.columns if c != '_arquivo_origem']
    df = df[colunas]

    # Salva em Excel
    arquivo_saida_excel.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(arquivo_saida_excel, index=False)
    print(f"Sucesso! Planilha gerada em: {arquivo_saida_excel}")
    print(f"Total de municípios processados: {len(lista_municipios)}")

# --- CONFIGURAÇÃO E EXECUÇÃO ---
if __name__ == "__main__":
    # Usa caminhos relativos ao script para funcionar em qualquer máquina.
    scripts_dir = Path(__file__).resolve().parent
    base_dir = scripts_dir.parent

    PASTA_COM_TEX = base_dir / "MUNICIPIOS"
    PLANILHA_SAIDA = scripts_dir / "Planilha_Municipios.xlsx"

    tex_para_excel(PASTA_COM_TEX, PLANILHA_SAIDA)