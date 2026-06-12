import importlib.util
from pathlib import Path
p = Path("Scripts/Texter_format_functions/texter_format_energisa.py")
spec = importlib.util.spec_from_file_location("tfe", p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

samples = [
    ("", "ARARUNA-OUT_2021-5_315470-5-L5_Poppler.txt"),
    ("CNPJ 18.3/0001-40", "ARARUNA-ABR_2023-5_1011213-4-L4_Poppler.txt"),
    ("CNPJ 10.5/0001-00", "ARARUNA-OUT_2021-5_1059295-4-L5_Poppler.txt"),
    ("mat 315470-2021-10-8", "arquivo_sem_uc.txt"),
]
for texto, fname in samples:
    print(fname, "=>", m._extrair_uc_documento(texto, fname))
