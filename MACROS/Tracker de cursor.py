import pyautogui
import time

try:
    while True:
        x, y = pyautogui.position()
        print(f"\rPosição do cursor: X={x:4d} | Y={y:4d}", end="", flush=True)
        time.sleep(0.05)  # Atualiza a cada 50 ms

except KeyboardInterrupt:
    print("\nPrograma encerrado.")
