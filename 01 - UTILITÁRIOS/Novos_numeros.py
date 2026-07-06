import os
import re
import csv

def extrair_dados_txt(caminho_txt):
    try:
        # Abre o arquivo TXT em modo leitura com codificação UTF-8
        with open(caminho_txt, 'r', encoding='utf-8') as arquivo:
            texto = arquivo.read()
        
        # Remove quebras de linha excessivas e espaços duplos para garantir consistência
        texto_limpo = re.sub(r'\s+', ' ', texto)

        # Mecanismo de busca simples via Expressão Regular (Regex)
        # Busca por "Antes: Código do cliente: " seguido de números
        match_antigo = re.search(r'Antes:\s*C[óo]digo\s+do\s+[Cc]liente:\s*(\d+)', texto_limpo)
        # Busca por "Agora: Número da Unidade Consumidora: " seguido de números
        match_novo = re.search(r'Agora:\s*N[úu]mero\s+da\s+Unidade\s+Consumidora:\s*(\d+)', texto_limpo)

        num_antigo = "Não encontrado"
        num_novo = "Não encontrado"
        status_novo = "OK"

        if match_antigo:
            num_antigo = match_antigo.group(1).strip()
        
        if match_novo:
            num_novo = match_novo.group(1).strip()
            status_novo = "OK"
        else:
            status_novo = "❌ Número Novo Não Encontrado"

        return num_antigo, num_novo, status_novo

    except Exception as e:
        print(f"Erro ao ler o arquivo {os.path.basename(caminho_txt)}: {e}")
        return "Erro", "Erro", "❌ Erro de Leitura"

def processar_pasta_emails():
    # Caminhos exatos apontando para o seu OneDrive
    pasta_txt = r"C:\Users\Usuário 1\OneDrive\Desktop\Emails_PDF"
    arquivo_csv_saida = r"C:\Users\Usuário 1\OneDrive\Desktop\alteracoes_unidades_consumidoras.csv"

    if not os.path.exists(pasta_txt):
        print(f"Erro: A pasta '{pasta_txt}' não foi encontrada.")
        return

    dados_finais = []
    # Altera a busca para encontrar arquivos .txt ao invés de .pdf
    arquivos = [f for f in os.listdir(pasta_txt) if f.lower().endswith('.txt')]

    if not arquivos:
        print(f"Nenhum arquivo TXT encontrado dentro da pasta: {pasta_txt}")
        return

    print(f"Iniciando o processamento de {len(arquivos)} arquivos de texto...")

    for arquivo in arquivos:
        caminho_completo = os.path.join(pasta_txt, arquivo)
        antigo, novo, status = extrair_dados_txt(caminho_completo)
        
        dados_finais.append({
            "Nome do Arquivo": arquivo,
            "Código Antigo (Cliente)": antigo,
            "Número Novo (Unidade Consumidora)": novo,
            "Status do Número Novo": status
        })

    # Definição das colunas do CSV
    colunas = ["Nome do Arquivo", "Código Antigo (Cliente)", "Número Novo (Unidade Consumidora)", "Status do Número Novo"]
    
    try:
        # utf-8-sig garante compatibilidade perfeita com o Excel em português
        with open(arquivo_csv_saida, mode='w', newline='', encoding='utf-8-sig') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=colunas, delimiter=';')
            writer.writeheader()
            writer.writerows(dados_finais)
            
        print(f"\nSucesso total! O relatório consolidado foi salvo em:")
        print(f"-> {arquivo_csv_saida}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo CSV: {e}")

if __name__ == "__main__":
    processar_pasta_emails()