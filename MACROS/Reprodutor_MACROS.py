import json
import time
import pyautogui
from pynput.keyboard import Key


# =========================
# CONFIGURAÇÕES
# =========================

ARQUIVO = r"C:\Users\Usuário 1\Documents\Inovve_Automação\MACROS\gravacao.json"

# Quantas vezes repetir
REPETICOES = 1

# 1.0 = velocidade original
# 2.0 = duas vezes mais rápido
VELOCIDADE = 1.0


# =========================
# CARREGAR GRAVAÇÃO
# =========================

with open(ARQUIVO, "r", encoding="utf-8") as f:
    eventos = json.load(f)


print(f"{len(eventos)} eventos carregados.")
print(f"Repetições: {REPETICOES}")
print()
print("A reprodução começará em 5 segundos.")
print("Mova o mouse para o canto superior esquerdo")
print("para acionar a proteção de emergência do PyAutoGUI.")
print()

time.sleep(5)


# =========================
# CONVERSÃO DE TECLAS
# =========================

def converter_tecla(tecla):

    especiais = {
        "Key.enter": "enter",
        "Key.space": "space",
        "Key.tab": "tab",
        "Key.backspace": "backspace",
        "Key.delete": "delete",
        "Key.esc": "esc",

        "Key.up": "up",
        "Key.down": "down",
        "Key.left": "left",
        "Key.right": "right",

        "Key.home": "home",
        "Key.end": "end",
        "Key.page_up": "pageup",
        "Key.page_down": "pagedown",

        "Key.shift": "shift",
        "Key.shift_l": "shift",
        "Key.shift_r": "shift",

        "Key.ctrl": "ctrl",
        "Key.ctrl_l": "ctrl",
        "Key.ctrl_r": "ctrl",

        "Key.alt": "alt",
        "Key.alt_l": "alt",
        "Key.alt_r": "alt",

        "Key.cmd": "win",
    }

    # Teclas especiais
    if tecla in especiais:
        return especiais[tecla]

    # --------------------------------
    # CARACTERES DE CONTROLE
    # --------------------------------

    controles = {
        "\x01": "a",  # Ctrl+A
        "\x02": "b",  # Ctrl+B
        "\x03": "c",  # Ctrl+C
        "\x04": "d",  # Ctrl+D
        "\x05": "e",  # Ctrl+E
        "\x06": "f",  # Ctrl+F
        "\x07": "g",  # Ctrl+G
        "\x08": "h",  # Ctrl+H
        "\x09": "i",  # Ctrl+I
        "\x0a": "j",  # Ctrl+J
        "\x0b": "k",  # Ctrl+K
        "\x0c": "l",  # Ctrl+L
        "\x0d": "m",  # Ctrl+M
        "\x0e": "n",  # Ctrl+N
        "\x0f": "o",  # Ctrl+O
        "\x10": "p",  # Ctrl+P
        "\x11": "q",  # Ctrl+Q
        "\x12": "r",  # Ctrl+R
        "\x13": "s",  # Ctrl+S
        "\x14": "t",  # Ctrl+T
        "\x15": "u",  # Ctrl+U
        "\x16": "v",  # Ctrl+V
        "\x17": "w",  # Ctrl+W
        "\x18": "x",  # Ctrl+X
        "\x19": "y",  # Ctrl+Y
        "\x1a": "z",  # Ctrl+Z
    }

    if tecla in controles:
        return controles[tecla]

    # --------------------------------
    # TECLAS NORMAIS
    # --------------------------------

    if len(tecla) == 1:
        return tecla

    return None



# =========================
# REPRODUÇÃO
# =========================

for repeticao in range(REPETICOES):

    print(
        f"Reprodução {repeticao + 1}/{REPETICOES}"
    )

    tempo_anterior = 0

    for evento in eventos:

        # -------------------------
        # RESPEITAR O TEMPO ORIGINAL
        # -------------------------

        tempo_evento = evento["tempo"]

        espera = (
            tempo_evento - tempo_anterior
        ) / VELOCIDADE

        if espera > 0:
            time.sleep(espera)

        tempo_anterior = tempo_evento

        tipo = evento["tipo"]

        # -------------------------
        # CLIQUE
        # -------------------------

        if tipo == "mouse_click":

            x = evento["x"]
            y = evento["y"]

            botao = evento["botao"]

            if "left" in botao:
                button = "left"

            elif "right" in botao:
                button = "right"

            elif "middle" in botao:
                button = "middle"

            else:
                continue

            pyautogui.click(
                x,
                y,
                button=button
            )

        # -------------------------
        # ARRASTAR
        # -------------------------

        elif tipo == "mouse_drag":

            x1 = evento["x"]
            y1 = evento["y"]

            x2 = evento["fim_x"]
            y2 = evento["fim_y"]

            pyautogui.moveTo(
                x1,
                y1
            )

            pyautogui.dragTo(
                x2,
                y2,
                duration=0.3,
                button="left"
            )

        # -------------------------
        # SCROLL
        # -------------------------

        elif tipo == "mouse_scroll":

            pyautogui.moveTo(
                evento["x"],
                evento["y"]
            )

            pyautogui.scroll(
                evento["dy"]
            )

        # -------------------------
        # TECLA PRESSIONADA
        # -------------------------

        elif tipo == "key_press":

            tecla = converter_tecla(
                evento["tecla"]
            )

            if tecla:
                pyautogui.keyDown(tecla)

        # -------------------------
        # TECLA SOLTA
        # -------------------------

        elif tipo == "key_release":

            tecla = converter_tecla(
                evento["tecla"]
            )

            if tecla:
                pyautogui.keyUp(tecla)


print()
print("Macro concluída!")
