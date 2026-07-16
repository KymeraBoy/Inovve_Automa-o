import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

# Caminhos e URL centralizados para facilitar manutencao
BASE_DIR = Path(__file__).resolve().parent
CAMINHO_EMPRESAS_JSON = BASE_DIR / "Logins.JSON"
URL_LOGIN_ANEEL = "https://www2.aneel.gov.br/faleconosco/login.asp"
TIMEOUT_LOGIN_MANUAL_MS = 180000


def obter_caminho_opera_gx():
    """Retorna o caminho do executavel do Opera GX no Windows."""
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("PROGRAMFILES", "")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")

    candidatos = [
        Path(local_appdata) / "Programs" / "Opera GX" / "opera.exe",
        Path(program_files) / "Opera GX" / "opera.exe",
        Path(program_files_x86) / "Opera GX" / "opera.exe",
    ]

    for caminho in candidatos:
        if caminho.exists():
            return caminho

    raise FileNotFoundError(
        "Nao foi possivel localizar o Opera GX automaticamente. "
        "Verifique a instalacao do Opera GX neste computador."
    )

def carregar_credenciais():
    """Carrega o arquivo JSON com os logins das empresas."""
    if not os.path.exists(CAMINHO_EMPRESAS_JSON):
        # Caso o arquivo não exista, cria um modelo básico para evitar erros
        modelo = {
            "1": {"nome": "Empresa de Exemplo", "usuario": "00000000000", "senha": "123"}
        }
        with open(CAMINHO_EMPRESAS_JSON, "w", encoding="utf-8") as f:
            json.dump(modelo, f, indent=4, ensure_ascii=False)
        print(f"Arquivo '{CAMINHO_EMPRESAS_JSON}' não encontrado. Criamos um modelo para você preencher.")
    
    with open(CAMINHO_EMPRESAS_JSON, "r", encoding="utf-8") as f:
        cadastro_empresas = json.load(f)

    if not isinstance(cadastro_empresas, dict) or not cadastro_empresas:
        raise ValueError("O arquivo Logins.JSON esta vazio ou em formato invalido.")

    for opcao, info in cadastro_empresas.items():
        if not isinstance(info, dict):
            raise ValueError(f"Cadastro da opcao '{opcao}' esta invalido no Logins.JSON.")
        campos_obrigatorios = ["nome", "usuario", "senha"]
        faltando = [campo for campo in campos_obrigatorios if not info.get(campo)]
        if faltando:
            raise ValueError(
                f"Cadastro '{opcao}' sem campos obrigatorios: {', '.join(faltando)}."
            )

    return cadastro_empresas

def menu_selecao_empresa(cadastro_empresas):
    print("=" * 45)
    print("          PROTOCOLLER - SELEÇÃO DE EMPRESA          ")
    print("=" * 45)
    for opcao, info in cadastro_empresas.items():
        print(f"[{opcao}] {info['nome']}")
    print("=" * 45)
    
    while True:
        escolha = input("Selecione o número da empresa para este protocolo: ").strip()
        if escolha in cadastro_empresas:
            return cadastro_empresas[escolha]
        print("Opção inválida! Tente novamente.")


def realizar_login_aneel(page, empresa):
    """Preenche login na pagina da ANEEL e tenta submeter.

    Retorna True quando detecta saida da URL de login e False caso contrario.
    """
    usuario = str(empresa["usuario"]).strip()
    senha = str(empresa["senha"]).strip()

    print("Preenchendo credenciais de acesso...")
    page.fill("input#cpf", "")
    page.type("input#cpf", usuario, delay=120)

    page.wait_for_timeout(500)

    page.fill("input#senha", "")
    page.type("input#senha", senha, delay=120)

    print("Efetuando login...")
    # O botao de login oficial da pagina e um input[type='button'] com name='Entrar'.
    try:
        page.click("input[name='Entrar']", timeout=5000)
    except PlaywrightTimeoutError:
        # Fallback para ambientes em que o botao fica sobreposto por elementos da pagina.
        page.click("input[name='Entrar']", force=True)
    except Exception:
        # Fallback final: envia Enter no campo senha para acionar a submissao.
        page.press("input#senha", "Enter")

    # Aguarda tentativa de redirecionamento apos o clique.
    page.wait_for_timeout(2500)

    if "login.asp" in page.url.lower():
        print(
            "A pagina continuou no login. Verifique credenciais e, se solicitado, "
            "conclua manualmente algum desafio visual antes de prosseguir."
        )
        return False

    print("Login concluido com sucesso.")
    return True


def aguardar_login_manual(page):
    """Aguarda o usuario concluir login manual quando o login automatico for bloqueado."""
    print("\nModo assistido ativado.")
    print("Conclua o login manualmente na janela do Opera GX (captcha/desafio, se houver).")
    print("Aguardando aprovacao do login por ate 3 minutos...")

    try:
        page.wait_for_url("**", timeout=TIMEOUT_LOGIN_MANUAL_MS)
    except PlaywrightTimeoutError:
        # O wait_for_url acima pode nao disparar em toda navegacao interna.
        pass

    tempo_espera = 0
    while "login.asp" in page.url.lower() and tempo_espera < TIMEOUT_LOGIN_MANUAL_MS:
        page.wait_for_timeout(1000)
        tempo_espera += 1000

    if "login.asp" in page.url.lower():
        raise RuntimeError(
            "Login ainda nao foi aprovado pelo site apos o tempo de espera. "
            "Verifique credenciais, captcha e possiveis bloqueios de seguranca."
        )

    print("Login manual confirmado. Fluxo pode continuar.")

def executar_automacao():
    # 1. Carrega as credenciais do arquivo externo
    cadastro_empresas = carregar_credenciais()
    
    # 2. Roda a interface no Prompt
    empresa_selecionada = menu_selecao_empresa(cadastro_empresas)
    print(f"\nIniciando processo para: {empresa_selecionada['nome']}...")
    
    with sync_playwright() as p:
        print("Abrindo o Opera GX...")
        caminho_opera_gx = obter_caminho_opera_gx()
        browser = p.chromium.launch(
            executable_path=str(caminho_opera_gx),
            headless=False
        )
        page = browser.new_page()
        
        # 3. Vai para a tela de login
        print("Acessando a página de login da ANEEL...")
        page.goto(URL_LOGIN_ANEEL, wait_until="domcontentloaded")

        # 4. Realiza o login com os dados da empresa selecionada.
        login_ok = realizar_login_aneel(page, empresa_selecionada)
        if not login_ok:
            aguardar_login_manual(page)

        input("\nPressione ENTER no terminal para encerrar o processo...")
        browser.close()

if __name__ == "__main__":
    executar_automacao()