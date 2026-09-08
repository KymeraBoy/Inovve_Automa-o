import time
import pyautogui


# Delay entre cada ação
DELAY = 1.0


def executar_acoes():
    acoes = [

        ("click", 778, 326),

        # Texto
        ("write", "Iluminacao Publica"),

        ("click", 1234, 325),

        # Shift + B
        ("write", "B"),
        ("click", 2078, 14),
        ("click", 2348, 391),
        ("click", 2348, 391),

        # Seta direita - 12 vezes
        ("press", "right", 12),

        # Ctrl + C
        ("hotkey", "ctrl", "c"),

        ("click", 413, 514),

        # Ctrl + V
        ("hotkey", "ctrl", "v"),

        # Quatro cliques
        ("click", 3453, 394),
        ("click", 3453, 394),
        ("click", 3453, 394),
        ("click", 3453, 394),

        # Ctrl + C
        ("hotkey", "ctrl", "c"),

        # Dois cliques
        ("click", 466, 523),
        ("click", 466, 523),

        # Ctrl + V
        ("hotkey", "ctrl", "v"),

        ("click", 2840, 1068),
        ("click", 2910, 978),
        ("click", 2393, 730),
        ("click", 428, 819),

        # Ctrl + V
        ("hotkey", "ctrl", "v"),

        ("click", 571, 899),
        ("click", 607, 347),
        ("click", 500, 1009),

        # Arrastar
        ("drag", 1914, 544, 1920, 764),

        ("click", 694, 927),
        ("click", 585, 803),
        ("click", 1205, 924),
        ("click", 1271, 839),

        # Arrastar
        ("drag", 1909, 639, 1922, 880),

        ("click", 2262, 823),
        ("click", 704, 470),

        # Ctrl + V
        ("hotkey", "ctrl", "v"),

        ("click", 2980, 1059),

        # ESC
        ("press", "esc"),
    ]

    for acao in acoes:
        tipo = acao[0]

        if tipo == "click":
            _, x, y = acao
            pyautogui.click(x, y)

        elif tipo == "drag":
            _, x1, y1, x2, y2 = acao
            pyautogui.moveTo(x1, y1)
            pyautogui.dragTo(
                x2,
                y2,
                duration=0.5,
                button="left"
            )

        elif tipo == "hotkey":
            _, tecla1, tecla2 = acao
            pyautogui.hotkey(tecla1, tecla2)

        elif tipo == "press":
            if len(acao) == 2:
                _, tecla = acao
                pyautogui.press(tecla)
            else:
                _, tecla, quantidade = acao
                pyautogui.press(
                    tecla,
                    presses=quantidade,
                    interval=0.1
                )

        elif tipo == "write":
            _, texto = acao
            pyautogui.write(texto)

        # Delay fixo entre cada ação
        time.sleep(DELAY)


if __name__ == "__main__":
    time.sleep(3)
    executar_acoes()
