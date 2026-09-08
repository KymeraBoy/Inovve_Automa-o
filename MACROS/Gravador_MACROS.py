import json
import time
from pynput import mouse, keyboard


eventos = []
inicio = time.time()

# Guarda informações sobre um possível arrasto
arrastando = False
inicio_arrasto = None
botao_arrasto = None


def timestamp():
    return round(time.time() - inicio, 3)


# =========================
# MOUSE
# =========================

def on_move(x, y):
    global arrastando

    # Movimento normal é ignorado.
    #
    # Se estivermos arrastando, apenas atualizamos
    # a posição final. Não criamos um evento para
    # cada movimento.
    if arrastando:
        eventos[-1]["fim_x"] = x
        eventos[-1]["fim_y"] = y


def on_click(x, y, button, pressed):
    global arrastando, inicio_arrasto, botao_arrasto

    # -------------------------
    # BOTÃO PRESSIONADO
    # -------------------------

    if pressed:

        arrastando = True
        inicio_arrasto = (x, y)
        botao_arrasto = button

        eventos.append({
            "tempo": timestamp(),
            "tipo": "mouse_down",
            "x": x,
            "y": y,
            "botao": str(button)
        })

        print(
            f"[{timestamp():8.3f}] "
            f"MOUSE DOWN {button} "
            f"x={x} y={y}"
        )

    # -------------------------
    # BOTÃO SOLTO
    # -------------------------

    else:

        # Descobre o evento anterior
        evento_anterior = eventos[-1] if eventos else None

        # Se o evento anterior for um mouse_down,
        # podemos determinar se foi clique ou arrasto.
        if (
            evento_anterior
            and evento_anterior["tipo"] == "mouse_down"
        ):

            x_inicio = evento_anterior["x"]
            y_inicio = evento_anterior["y"]

            distancia = (
                abs(x - x_inicio) +
                abs(y - y_inicio)
            )

            # Pequenos movimentos são tratados como clique
            if distancia < 5:

                evento_anterior["tipo"] = "mouse_click"

                evento_anterior["acao"] = "clique"

                evento_anterior["fim_x"] = x
                evento_anterior["fim_y"] = y

                print(
                    f"[{timestamp():8.3f}] "
                    f"CLICK {button} "
                    f"x={x} y={y}"
                )

            # Movimento significativo = arrasto
            else:

                evento_anterior["tipo"] = "mouse_drag"

                evento_anterior["fim_x"] = x
                evento_anterior["fim_y"] = y

                evento_anterior["acao"] = "arrastar"

                print(
                    f"[{timestamp():8.3f}] "
                    f"DRAG {button} "
                    f"({x_inicio},{y_inicio}) "
                    f"-> ({x},{y})"
                )

        arrastando = False
        inicio_arrasto = None
        botao_arrasto = None


def on_scroll(x, y, dx, dy):

    eventos.append({
        "tempo": timestamp(),
        "tipo": "mouse_scroll",
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy
    })

    print(
        f"[{timestamp():8.3f}] "
        f"SCROLL x={x} y={y} "
        f"dx={dx} dy={dy}"
    )


# =========================
# TECLADO
# =========================

def on_press(key):

    try:
        tecla = key.char
    except AttributeError:
        tecla = str(key)

    eventos.append({
        "tempo": timestamp(),
        "tipo": "key_press",
        "tecla": tecla
    })

    print(
        f"[{timestamp():8.3f}] "
        f"KEY DOWN {tecla}"
    )


def on_release(key):

    try:
        tecla = key.char
    except AttributeError:
        tecla = str(key)

    eventos.append({
        "tempo": timestamp(),
        "tipo": "key_release",
        "tecla": tecla
    })

    print(
        f"[{timestamp():8.3f}] "
        f"KEY UP   {tecla}"
    )

    # ESC encerra a gravação
    if key == keyboard.Key.esc:
        return False


# =========================
# INICIAR
# =========================

print("======================================")
print("          GRAVADOR DE MACRO")
print("======================================")
print()
print("Gravando...")
print("Movimentos normais do mouse serão ignorados.")
print("Pressione ESC para parar.")
print()


mouse_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll
)

keyboard_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release
)


mouse_listener.start()
keyboard_listener.start()

keyboard_listener.join()

mouse_listener.stop()


# =========================
# SALVAR
# =========================

arquivo = "gravacao.json"

with open(arquivo, "w", encoding="utf-8") as f:
    json.dump(
        eventos,
        f,
        indent=2,
        ensure_ascii=False
    )


print()
print("======================================")
print("Gravação encerrada!")
print(f"Eventos gravados: {len(eventos)}")
print(f"Arquivo: {arquivo}")
print("======================================")
