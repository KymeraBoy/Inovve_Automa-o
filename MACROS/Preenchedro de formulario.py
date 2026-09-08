import os
import re
import time
import pandas as pd
import pyautogui
import pyperclip

# Caminho fixo do arquivo Excel
CAMINHO_PLANILHA = r"C:\Users\Usuário 1\Documents\Inovve_Automação\GERADOR DE DOCUMENTOS\SCRIPTS\Planilha_Municipios.xlsx"

def formatar_valor(val):
    val_str = str(val).strip() if pd.notna(val) else ""
    return val_str if val_str and val_str.lower() != 'nan' else 'Não informado'

def extrair_uf(dados_mun, df_concessionarias):
    """
    Extrai a sigla do estado (UF) identificando a concessionária vinculada ao município.
    
    Busca o nome ou trechos da concessionária no texto do contrato (clausula, publicacao, etc.)
    e faz a correspondência com a aba 'Concessionárias' para retornar o 'siglaEstado'.
    """
    # Texto completo disponível sobre o município para busca da concessionária
    texto_busca = " ".join([
        str(dados_mun.get('clausula', '')),
        str(dados_mun.get('publicacao', '')),
        str(dados_mun.get('email', '')),
        str(dados_mun.get('sedePrefeitura', ''))
    ]).lower()

    if not df_concessionarias.empty:
        # 1. Busca direta por nomes/palavras-chave das concessionárias cadastradas
        for _, row in df_concessionarias.iterrows():
            nome_concessionaria = str(row.get('nomeConcessionaria', '')).strip()
            sigla_estado = str(row.get('siglaEstado', '')).strip().upper()

            if not nome_concessionaria or not sigla_estado:
                continue

            # Mapeia termos chaves para cada concessionária
            nome_clean = nome_concessionaria.lower()
            if nome_clean in texto_busca:
                return sigla_estado

        # 2. Busca por correspondência de nomes conhecidos de distribuidores
        if 'equatorial' in texto_busca and 'goiás' in texto_busca or 'goias' in texto_busca:
            return 'GO'
        elif 'neoenergia' in texto_busca and 'pernambuco' in texto_busca:
            return 'PE'
        elif 'neoenergia' in texto_busca and 'rio grande do norte' in texto_busca:
            return 'RN'
        elif 'neoenergia' in texto_busca and 'bahia' in texto_busca:
            return 'BA'
        elif 'energisa' in texto_busca and 'mato grosso do sul' in texto_busca:
            return 'MS'
        elif 'energisa' in texto_busca or 'paraíba' in texto_busca or 'paraiba' in texto_busca:
            return 'PB'

    # 3. Verificação por e-mail (.pb.gov.br, .go.gov.br, etc.)
    email = str(dados_mun.get('email', ''))
    match_email = re.search(r'\.([a-z]{2})\.gov\.br', email, re.IGNORECASE)
    if match_email:
        return match_email.group(1).upper()

    # Fallback padrão
    return 'PB'

def inserir_dado(nome_campo, texto, x, y):
    """Copia o texto, clica na coordenada, cola e aguarda o delay de 0.1s."""
    print(f"-> Preenchendo [{nome_campo}] nas coordenadas ({x}, {y})...")
    if texto and texto != 'Não informado':
        pyperclip.copy(texto)
        pyautogui.click(x, y)
        time.sleep(0.2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2) # Delay reduzido para 0.1 segundo
    else:
        print(f"   [PULADO] Informacao invalida ou ausente para [{nome_campo}]")

def preencher_formulario(dados):
    print("\nIniciando o preenchimento do formulario em 3 segundos...")
    print("Por favor, mantenha o foco no navegador e nao mova o mouse.")
    time.sleep(3)

    print("\n--- INICIO DA SEQUENCIA DE PREENCHIMENTO ---")

    # Selecionar modo representante
    pyautogui.click(510, 310)
    time.sleep(0.5)

    # Apertar botão OK
    pyautogui.click(1400, 1000)
    time.sleep(0.5)



    # Coordenadas do Município
    inserir_dado("Municipio - Nome Formatado", dados['mun_nome_formatado'], 600, 460)
    inserir_dado("Municipio - Telefone", dados['mun_telefone'], 600, 570)
    inserir_dado("Municipio - E-mail", dados['mun_email'], 1500, 460)
    inserir_dado("Municipio - CNPJ", dados['mun_cnpj'], 1500, 570)

    # Coordenadas da Empresa (Nome = RepresentanteEmpresa)
    inserir_dado("Empresa - Representante", dados['emp_nome'], 600, 750)
    inserir_dado("Empresa - Telefone", dados['emp_telefone'], 400, 860)
    inserir_dado("Empresa - E-mail", dados['emp_email'], 1500, 750)
    inserir_dado("Empresa - CNPJ", dados['emp_cnpj'], 1200, 860)

    pyautogui.press("pagedown")
    time.sleep(0.5)

    inserir_dado("Iluminação Pública", "Iluminação Pública", 600, 320)
    inserir_dado("Grupo Tarifário", "B", 1200, 320)
    inserir_dado("Grupo Tarifário", "Manifestar-se por falta de resposta da concessionária", 500, 820)

    pyautogui.click(500, 900) # Selecionar Endereço
    time.sleep(0.5)
    pyautogui.press("S")
    time.sleep(0.5)
    pyautogui.press("Enter")
    time.sleep(0.5)
    pyautogui.click(490, 1000) #  Selecionar E-mail
    time.sleep(0.5)

    pyautogui.press("pagedown")
    time.sleep(0.5)
    pyautogui.click(460, 930) #   Natureza do contato
    time.sleep(0.5)
    pyautogui.click(400, 800) #   Natureza do contato
    time.sleep(0.5)
    pyautogui.click(1300, 930) #   Natureza do contato
    time.sleep(0.5)
    # pyautogui.moveTo(1300, 820, duration=0.5)
    # time.sleep(0.5)
    pyautogui.click(1300, 820) #   Natureza do contato
    time.sleep(0.9)
    pyautogui.click(1300, 820) #   Natureza do contato
    time.sleep(0.5)
    pyautogui.press("pagedown")
    time.sleep(0.5)
    inserir_dado("Iluminação Pública", "Prezado Ouvidor, \nA presente reclamação é direcionada à ENERGISA PARAIBA e refere-se à RECLAMAÇÃO 002/2026, diante da ausência de resposta à solicitação previamente registrada junto à concessionária dentro do prazo estabelecido. \nRessalta-se, ainda, a necessidade de que tanto a distribuidora quanto a ANEEL observem e cumpram integralmente as disposições constantes do Parecer nº 103/2026 (ANEXO).\nDessa forma, solicita-se a atuação dessa Ouvidoria para que a ENERGISA PARAIBA apresente resposta conclusiva à reclamação, adotando as providências necessárias em estrita conformidade com o conteúdo do referido Parecer.", 500, 300)


    print("\n--- PREENCHIMENTO CONCLUIDO ---")

def consultar_e_preencher():
    if not os.path.exists(CAMINHO_PLANILHA):
        print(f"Erro: O arquivo nao foi encontrado no caminho especificado:\n{CAMINHO_PLANILHA}")
        return

    try:
        df_municipios = pd.read_excel(CAMINHO_PLANILHA, sheet_name='Municípios', dtype=str)
        df_empresas = pd.read_excel(CAMINHO_PLANILHA, sheet_name='Empresas', dtype=str)
    except Exception as e:
        print(f"Erro ao carregar a planilha: {e}")
        return

    df_municipios['nomeMunicipio'] = df_municipios['nomeMunicipio'].str.strip()
    lista_municipios = df_municipios['nomeMunicipio'].dropna().unique().tolist()
    lista_municipios.sort()

    if not lista_municipios:
        print("Erro: Nenhum municipio encontrado na aba 'Municipios'.")
        return

    print("MUNICIPOS DISPONIVEIS")
    print("-" * 40)
    for idx, mun in enumerate(lista_municipios, 1):
        print(f"[{idx}] {mun}")
    print("-" * 40)

    escolha = input("\nDigite o numero ou o nome do municipio desejado: ").strip()

    municipio_selecionado = None
    if escolha.isdigit():
        idx_num = int(escolha) - 1
        if 0 <= idx_num < len(lista_municipios):
            municipio_selecionado = lista_municipios[idx_num]
    else:
        for mun in lista_municipios:
            if mun.lower() == escolha.lower():
                municipio_selecionado = mun
                break

    if not municipio_selecionado:
        print("Erro: Opcao ou municipio invalido.")
        return

    # Extração das informações do município
    dados_mun = df_municipios[df_municipios['nomeMunicipio'] == municipio_selecionado].iloc[0]
    cod_empresa = str(dados_mun.get('empresaResponsavel', '')).strip()

    # Formatação do nome do Município para o formulário
    df_concessionarias = pd.read_excel(CAMINHO_PLANILHA, sheet_name='Concessionárias', dtype=str)
    uf = extrair_uf(dados_mun,df_concessionarias)
    nome_mun_original = formatar_valor(dados_mun.get('nomeMunicipio'))
    nome_mun_formatado = f"Prefeitura municipal de {nome_mun_original} - {uf}"

    # Busca dos dados da Empresa (usando a coluna RepresentanteEmpresa como nome)
    dados_emp = df_empresas[df_empresas['Empresa'].str.strip() == cod_empresa]
    if not dados_emp.empty:
        emp_info = dados_emp.iloc[0]
        emp_nome = emp_info.get('RepresentanteEmpresa') # Nome do representante conforme solicitado
        emp_cnpj = emp_info.get('CNPJEmpresa')
        emp_tel = emp_info.get('TelefoneEmpresa')
        emp_email = emp_info.get('EmailEmpresa')
    else:
        emp_nome = None
        emp_cnpj = None
        emp_tel = None
        emp_email = None

    # Objeto com todos os dados tratados
    dados_extraidos = {
        'mun_nome_original': nome_mun_original,
        'mun_nome_formatado': nome_mun_formatado,
        'mun_cnpj': formatar_valor(dados_mun.get('cnpjMunicipio')),
        'mun_telefone': formatar_valor(dados_mun.get('telefone')),
        'mun_email': formatar_valor(dados_mun.get('email')),
        'emp_nome': formatar_valor(emp_nome),
        'emp_cnpj': formatar_valor(emp_cnpj),
        'emp_telefone': formatar_valor(emp_tel),
        'emp_email': formatar_valor(emp_email)
    }

    print("\n" + "=" * 60)
    print(f"DADOS TRATADOS PARA O FORMULARIO: {municipio_selecionado.upper()}")
    print("=" * 60)
    print(f"Municipio Nome (Formatado): {dados_extraidos['mun_nome_formatado']}")
    print(f"Municipio CNPJ:             {dados_extraidos['mun_cnpj']}")
    print(f"Municipio Telefone:         {dados_extraidos['mun_telefone']}")
    print(f"Municipio E-mail:           {dados_extraidos['mun_email']}")
    print(f"Empresa Representante:      {dados_extraidos['emp_nome']}")
    print(f"Empresa CNPJ:               {dados_extraidos['emp_cnpj']}")
    print(f"Empresa Telefone:           {dados_extraidos['emp_telefone']}")
    print(f"Empresa E-mail:             {dados_extraidos['emp_email']}")
    print("=" * 60 + "\n")

    confirmacao = input("Deseja iniciar o preenchimento no formulario web? (S/N): ").strip().upper()
    if confirmacao == 'S':
        preencher_formulario(dados_extraidos)
    else:
        print("Operacao cancelada pelo usuario.")

if __name__ == "__main__":
    consultar_e_preencher()