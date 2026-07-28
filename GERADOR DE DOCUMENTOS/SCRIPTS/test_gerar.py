import sys
sys.path.insert(0, str(__file__).replace('test_gerar.py',''))
import gerar_documento as g

muns = g.list_municipios()
print(f"Municipios: {len(muns)}")
for nome, _, dados in muns[:4]:
    print(f"  {nome} -> {dados.get('empresaResponsavel','?')}")

print()
rec = g.list_subtypes_rec()
print("Subtipos REC:", [l for l,_ in rec])

req = g.list_subtypes_req('RUDA')
print("Subtipos REQ RUDA:", [l for l,_ in req])

print()
for l, p in rec + req:
    print(f"  is_fragment({p.name}) = {g.is_fragment(p)}")
