import shutil
import re
import subprocess
import unicodedata
from pathlib import Path

# ============================================================
# CONFIGURAÇÃO
# ============================================================

base_dir = Path(__file__).parent
output_dir = base_dir / "Output"
dados_municipios_dir = base_dir / "Dados_Municipios"

output_dir.mkdir(exist_ok=True)

# ============================================================
# FUNÇÕES DE EXTRAÇÃO (genérica)
# ============================================================

def extrair_comando_latex(caminho_tex, nome_comando, maiuscula=False):
    """
    Extrai o valor de um comando LaTeX \\newcommand ou \\renewcommand
    
    Args:
        caminho_tex: Caminho do arquivo .tex
        nome_comando: Nome do comando (ex: 'numReclamacao', 'subrec')
        maiuscula: Se True, converte resultado para MAIÚSCULA
    
    Returns:
        Valor do comando ou None se não encontrado
    """
    try:
        with open(caminho_tex, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        match = re.search(
            rf'\\newcommand\{{\\{nome_comando}\}}\{{([^}}]*)\}}',
            conteudo
        )
        
        if match:
            valor = match.group(1)
            return valor.upper() if maiuscula else valor
        return None
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return None


# ============================================================
# FUNÇÕES DE ATUALIZAÇÃO LATEX
# ============================================================

def atualizar_newcommand_tex(caminho_tex, nome_comando, novo_valor):
    """Atualiza o valor de um \\newcommand específico no arquivo .tex"""
    try:
        with open(caminho_tex, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        padrao = r'(\\newcommand\{\\' + re.escape(nome_comando) + r'\}\{)([^}]*)(\})'

        def substituir(match):
            return f"{match.group(1)}{novo_valor}{match.group(3)}"

        novo_conteudo, alteracoes = re.subn(padrao, substituir, conteudo, count=1)

        if alteracoes == 0:
            print(f"❌ Erro: Não foi possível encontrar \\{nome_comando} em {caminho_tex.name}")
            return False

        with open(caminho_tex, 'w', encoding='utf-8') as f:
            f.write(novo_conteudo)

        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar arquivo: {e}")
        return False


def atualizar_inputs_documento(caminho_tex, arquivo_municipio, arquivo_reclamacao):
    """Atualiza os \input de município e reclamação no Documento.tex"""
    try:
        with open(caminho_tex, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        padrao_municipio = r'^(?!\s*%)\s*\\input\{\.\./\.\./Dados_Municipios/[^}]+\}\s*$'
        novo_input_municipio = f"\\input{{../../Dados_Municipios/{arquivo_municipio}}}"
        conteudo, alteracoes_municipio = re.subn(
            padrao_municipio,
            lambda _: novo_input_municipio,
            conteudo,
            count=1,
            flags=re.MULTILINE
        )

        padrao_reclamacao = r'^(?!\s*%)\s*\\input\{\.\./Tipos_de_reclamacao/[^}]+\}\s*$'
        novo_input_reclamacao = f"\\input{{../Tipos_de_reclamacao/{arquivo_reclamacao}}}"
        conteudo, alteracoes_reclamacao = re.subn(
            padrao_reclamacao,
            lambda _: novo_input_reclamacao,
            conteudo,
            count=1,
            flags=re.MULTILINE
        )

        if alteracoes_municipio == 0:
            print(f"❌ Erro: Não foi possível atualizar a importação de município em {caminho_tex.name}")
            return False

        if alteracoes_reclamacao == 0:
            print(f"❌ Erro: Não foi possível atualizar a importação de reclamação em {caminho_tex.name}")
            return False

        with open(caminho_tex, 'w', encoding='utf-8') as f:
            f.write(conteudo)

        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar importações: {e}")
        return False

def compilar_documento_pdf(caminho_tex):
    """Compila o Documento.tex e atualiza o Documento.pdf"""
    try:
        diretorio_tex = caminho_tex.parent
        nome_arquivo_tex = caminho_tex.name

        # Duas passagens para garantir referências e sumário consistentes
        for _ in range(2):
            resultado = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", nome_arquivo_tex],
                cwd=diretorio_tex,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            if resultado.returncode != 0:
                print("❌ Erro na compilação do PDF (pdflatex).")
                if resultado.stderr.strip():
                    print(f"   stderr: {resultado.stderr.strip()[-500:]}")
                if resultado.stdout.strip():
                    print(f"   stdout: {resultado.stdout.strip()[-500:]}")
                return False

        return True
    except FileNotFoundError:
        print("❌ Erro: 'pdflatex' não encontrado no sistema. Instale e adicione ao PATH.")
        return False
    except Exception as e:
        print(f"❌ Erro ao compilar PDF: {e}")
        return False


# ============================================================
# FUNÇÕES DE LISTAGEM E LEITURA
# ============================================================

def listar_arquivos_tipo(pasta_selecionada):
    """Lista arquivos em Tipos_de_reclamacao (sem arquivos auxiliares)"""
    tipos_dir = base_dir / pasta_selecionada / "Tipos_de_reclamacao"
    if tipos_dir.exists():
        arquivos = [
            f.name for f in tipos_dir.iterdir() 
            if f.is_file() and not f.name.endswith(('.aux', '.log', '.synctex.gz', '.toc'))
        ]
        return sorted(arquivos)
    return []


def listar_municipios():
    """Lista arquivos de dados de municípios disponíveis"""
    arquivos = sorted([f.name for f in dados_municipios_dir.glob("Dados_*.tex")])
    return arquivos


# ============================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================

def limpar_nome(nome):
    """Remove acentos e substitui espaços por underscore"""
    nome_normalizado = unicodedata.normalize('NFKD', nome)
    nome_sem_acento = ''.join([c for c in nome_normalizado if not unicodedata.combining(c)])
    return nome_sem_acento.replace(' ', '_')


def limpar_output():
    """Apaga todos os arquivos da pasta Output"""
    if output_dir.exists():
        for arquivo in output_dir.iterdir():
            if arquivo.is_file():
                try:
                    arquivo.unlink()
                    print(f"  Removido: {arquivo.name}")
                except Exception as e:
                    print(f"  ⚠ Erro ao remover {arquivo.name}: {e}")


# ============================================================
# FUNÇÕES DE ENTRADA DO USUÁRIO
# ============================================================

def escolher_pasta():
    """Permite o usuário escolher entre HLA ou RUDA"""
    print("\n1. Qual pasta deseja usar?")
    print("   1 - HLA")
    print("   2 - RUDA")
    print()
    
    while True:
        opcao = input("   Digite 1 ou 2: ").strip()
        if opcao in ["1", "2"]:
            return "HLA" if opcao == "1" else "RUDA"
        print("   Opção inválida! Digite 1 ou 2.")


def escolher_arquivo_lista(titulo, opcoes):
    """
    Permite o usuário escolher uma opção de uma lista
    
    Args:
        titulo: Texto exibido antes das opções
        opcoes: Lista de opções disponíveis
    
    Returns:
        Índice da opção escolhida (0-based)
    """
    print(f"\n{titulo}")
    for idx, opcao in enumerate(opcoes, 1):
        print(f"   {idx} - {opcao}")
    
    print()
    while True:
        try:
            escolha = int(input("   Escolha o número: ").strip()) - 1
            if 0 <= escolha < len(opcoes):
                return escolha
            print(f"   Opção inválida! Digite entre 1 e {len(opcoes)}.")
        except ValueError:
            print("   Digite um número válido!")


def pedir_valor_usuario(mensagem):
    """Pede um valor ao usuário até que não esteja vazio"""
    while True:
        valor = input(f"   {mensagem}: ").strip()
        if valor:
            return valor
        print("   Valor inválido! Digite um conteúdo.")


def pedir_unidades_consumidoras():
    """
    Pede unidades consumidoras ao usuário.
    Aceita múltiplas unidades separadas por vírgula ou quebra de linha.
    Retorna lista de unidades.
    """
    print("   Digite a(s) unidade(s) consumidora(s):")
    print("   (separadas por VÍRGULA ou ENTER para múltiplas linhas)")
    print("   (Digite uma linha vazia para terminar)\n")
    
    unidades = []
    while True:
        entrada = input("   ").strip()
        if not entrada:
            break
        # Se houver vírgula, divide por vírgula
        if ',' in entrada:
            unidades.extend([u.strip() for u in entrada.split(',') if u.strip()])
        else:
            unidades.append(entrada)
    
    # Remove duplicatas mantendo ordem
    unidades_unicas = []
    for u in unidades:
        if u not in unidades_unicas:
            unidades_unicas.append(u)
    
    return unidades_unicas


def incrementar_numero_reclamacao(num_reclamacao):
    """
    Incrementa o número de reclamação
    Exemplo: "001/2026" -> "002/2026"
    """
    try:
        partes = num_reclamacao.split('/')
        if len(partes) != 2:
            return None
        
        numero = int(partes[0])
        ano = partes[1]
        
        numero += 1
        novo_numero = f"{numero:03d}/{ano}"
        return novo_numero
    except (ValueError, IndexError):
        return None


# ============================================================
# FUNÇÕES DE PROCESSAMENTO
# ============================================================

def construir_nome_pdf(num_reclamacao, nome_municipio, nome_tipo, unidade_consumidora):
    """Constrói o nome do arquivo PDF final"""
    nome_tipo_limpo = limpar_nome(nome_tipo).upper()
    
    sufixo_uc = ""
    if unidade_consumidora:
        unidade_limpa = limpar_nome(unidade_consumidora).replace('/', '_').replace('-', '_')
        sufixo_uc = f"-{unidade_limpa}"
    
    if num_reclamacao and nome_municipio:
        nome_municipio_limpo = limpar_nome(nome_municipio)
        return f"REC-{num_reclamacao.replace('/', '_')}-{nome_municipio_limpo}-{nome_tipo_limpo}{sufixo_uc}.pdf"
    
    if num_reclamacao:
        return f"REC-{num_reclamacao.replace('/', '_')}-{nome_tipo_limpo}{sufixo_uc}.pdf"
    
    print("⚠ Aviso: Não foi possível extrair \\numReclamacao")
    return f"Documento-{nome_tipo_limpo}{sufixo_uc}.pdf"


def compilar_documento(pasta, arquivo_tipo, arquivo_municipio, num_reclamacao, unidade_consumidora):
    """Compila o documento com as configurações fornecidas"""
    tex_origem = base_dir / pasta / "Documento" / "Documento.tex"
    pdf_origem = base_dir / pasta / "Documento" / "Documento.pdf"
    
    # Verificar se o TEX existe
    if not tex_origem.exists():
        print(f"\n❌ Erro: TEX não encontrado em {tex_origem}")
        return False, None, None
    
    # Atualizar imports
    if not atualizar_inputs_documento(tex_origem, arquivo_municipio, arquivo_tipo):
        return False, None, None
    print("✓ Importações de município e reclamação atualizadas!")
    
    # Atualizar valores
    if not atualizar_newcommand_tex(tex_origem, "numReclamacao", num_reclamacao):
        return False, None, None
    
    if not atualizar_newcommand_tex(tex_origem, "unidadeConsumidora", unidade_consumidora):
        return False, None, None
    
    # Extrair e atualizar Reclamacao do arquivo tipo
    caminho_tipo = base_dir / pasta / "Tipos_de_reclamacao" / arquivo_tipo
    valor_reclamacao = extrair_comando_latex(caminho_tipo, "subrec")
    if valor_reclamacao:
        if not atualizar_newcommand_tex(tex_origem, "Reclamacao", valor_reclamacao):
            return False, None, None
    else:
        print(f"⚠ Aviso: Não foi possível extrair \\subrec de {arquivo_tipo}")
    
    print("✓ Documento.tex atualizado!")
    
    # Compilar
    print("\nCompilando Documento.tex...")
    if not compilar_documento_pdf(tex_origem):
        return False, None, None
    
    if not pdf_origem.exists():
        print(f"\n❌ Erro: PDF não encontrado após compilação")
        return False, None, None
    
    print("✓ Documento.pdf compilado!")
    
    # Extrair metadados para nome do arquivo
    num_rec = extrair_comando_latex(tex_origem, "numReclamacao")
    caminho_municipio = dados_municipios_dir / arquivo_municipio
    nome_municipio = extrair_comando_latex(caminho_municipio, "nomeMunicipio", maiuscula=True)
    unidade = extrair_comando_latex(tex_origem, "unidadeConsumidora")
    
    return True, pdf_origem, (num_rec, nome_municipio, unidade)


def executar_gerador_batch(pasta, arquivo_tipo, arquivo_municipio, num_reclamacao_inicial, unidades):
    """
    Gera múltiplos documentos para várias unidades consumidoras
    Incrementa o número de reclamação para cada documento
    """
    print(f"\n{'='*50}")
    print(f"MODO BATCH: {len(unidades)} documento(s)")
    print(f"{'='*50}\n")
    
    num_reclamacao_atual = num_reclamacao_inicial
    documentos_gerados = 0
    documentos_falhados = 0
    
    for idx, unidade in enumerate(unidades, 1):
        print(f"\n[{idx}/{len(unidades)}] Processando unidade: {unidade}")
        print(f"    Número de reclamação: {num_reclamacao_atual}")
        
        # Compilar documento
        sucesso, pdf_origem, metadados = compilar_documento(
            pasta,
            arquivo_tipo,
            arquivo_municipio,
            num_reclamacao_atual,
            unidade
        )
        
        if not sucesso:
            print(f"    ❌ Falha ao gerar documento")
            documentos_falhados += 1
        else:
            # Copiar para Output com nome adequado
            num_rec, nome_municipio, unidade_final = metadados
            nome_tipo = Path(arquivo_tipo).stem
            
            nome_saida = construir_nome_pdf(num_rec, nome_municipio, nome_tipo, unidade_final)
            pdf_destino = output_dir / nome_saida
            
            try:
                shutil.copy2(pdf_origem, pdf_destino)
                print(f"    ✓ Sucesso! Salvo em: {nome_saida}")
                documentos_gerados += 1
            except Exception as e:
                print(f"    ❌ Erro ao copiar: {e}")
                documentos_falhados += 1
        
        # Incrementar número para próximo documento
        proximo_numero = incrementar_numero_reclamacao(num_reclamacao_atual)
        if proximo_numero:
            num_reclamacao_atual = proximo_numero
        else:
            print(f"    ⚠ Aviso: Não foi possível incrementar número de reclamação")
            break
    
    print(f"\n{'='*50}")
    print(f"RESUMO: {documentos_gerados} sucesso(s), {documentos_falhados} falha(s)")
    print(f"{'='*50}\n")
    
    return documentos_gerados > 0


def executar_gerador():
    """Fluxo principal do gerador"""
    
    # Cabeçalho
    print("=" * 50)
    print("GERADOR DE RECLAMAÇÃO")
    print("=" * 50)
    print("\nLimpando pasta Output...")
    limpar_output()
    
    # 1. Escolher pasta (HLA ou RUDA)
    pasta_selecionada = escolher_pasta()
    
    # 2. Escolher tipo de reclamação
    print(f"\n2. Qual arquivo de {pasta_selecionada}/Tipos_de_reclamacao/ deseja usar?")
    arquivos_tipo = listar_arquivos_tipo(pasta_selecionada)
    
    if not arquivos_tipo:
        print(f"❌ Erro: Nenhum arquivo encontrado em {pasta_selecionada}/Tipos_de_reclamacao/")
        return False
    
    idx_arquivo = escolher_arquivo_lista("", arquivos_tipo)
    arquivo_selecionado = arquivos_tipo[idx_arquivo]
    
    # 3. Escolher município
    municipios = listar_municipios()
    if not municipios:
        print("❌ Erro: Nenhum arquivo de município encontrado em Dados_Municipios")
        return False
    
    nomes_municipios = [m.replace("Dados_", "").replace(".tex", "") for m in municipios]
    idx_municipio = escolher_arquivo_lista("3. Qual município deseja usar?", nomes_municipios)
    arquivo_municipio = municipios[idx_municipio]
    
    # 4. Pedir informações do usuário
    print("\n4. Informe os valores para atualizar no Documento.tex")
    num_reclamacao = pedir_valor_usuario("Digite o valor de \\numReclamacao")
    
    print("\n5. Digite a(s) unidade(s) consumidora(s):")
    unidades_consumidoras = pedir_unidades_consumidoras()
    
    if not unidades_consumidoras:
        print("❌ Erro: Nenhuma unidade consumidora fornecida")
        return False
    
    # Detectar modo automaticamente
    if len(unidades_consumidoras) == 1:
        # Modo único
        print(f"\n📄 MODO ÚNICO: 1 documento")
        
        sucesso, pdf_origem, metadados = compilar_documento(
            pasta_selecionada,
            arquivo_selecionado,
            arquivo_municipio,
            num_reclamacao,
            unidades_consumidoras[0]
        )
        
        if not sucesso:
            return False
        
        num_rec, nome_municipio, unidade = metadados
        nome_tipo = Path(arquivo_selecionado).stem
        
        nome_saida = construir_nome_pdf(num_rec, nome_municipio, nome_tipo, unidade)
        pdf_destino = output_dir / nome_saida
        
        try:
            shutil.copy2(pdf_origem, pdf_destino)
            print(f"\n✓ Sucesso! PDF copiado para:")
            print(f"  {pdf_destino}")
            return True
        except Exception as e:
            print(f"\n❌ Erro ao copiar: {e}")
            return False
    
    else:
        # Modo batch
        return executar_gerador_batch(
            pasta_selecionada,
            arquivo_selecionado,
            arquivo_municipio,
            num_reclamacao,
            unidades_consumidoras
        )


# ============================================================
# PONTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    executar_gerador()
