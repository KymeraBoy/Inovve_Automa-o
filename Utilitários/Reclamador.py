from pathlib import Path
import shutil

SUBPASTAS = ["ANEEL", "PAGAMENTO", "RECLAMACAO_FORMAL", "DOCUMENTOS_RECEBIDOS", "E-MAILS"]

base = Path(__file__).resolve().parent

for pdf in base.glob("*.pdf"):
    pasta = base / pdf.stem
    for sub in SUBPASTAS:
        (pasta / sub).mkdir(parents=True, exist_ok=True)
    shutil.move(str(pdf), str(pasta / "RECLAMACAO_FORMAL" / pdf.name))
    print(f"[OK] {pdf.name}  →  {pasta.name}/RECLAMACAO_FORMAL/")

print("Concluído.")
