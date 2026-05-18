# Reclamações - Base do gerador .tex

Estrutura inicial para gerar reclamacoes administrativas em LaTeX.

## Estrutura

- `Gerador_de_reclamacoes.py`: script principal.
- `templates/reclamacao_base.tex`: template inicial com placeholders.
- `data/concessionarias.json`: lista de concessionarias para o modo interativo.
- `exemplos/reclamacao_exemplo.json`: exemplo para geracao automatica via JSON.
- `output/`: diretorio onde os .tex gerados serao salvos.

## Como usar

### 1) Modo interativo

No terminal, dentro da pasta `Reclamações`:

```bash
python Gerador_de_reclamacoes.py
```

### 2) Modo automatico com JSON

```bash
python Gerador_de_reclamacoes.py --from-json exemplos/reclamacao_exemplo.json
```

### 3) Definir template e saida

```bash
python Gerador_de_reclamacoes.py --from-json exemplos/reclamacao_exemplo.json --template templates/reclamacao_base.tex --output-dir output
```

## Proximo passo sugerido

Padronizar os tipos de reclamacao (IP nao corrigida, IP corrigida, AES etc.) como templates separados dentro de `templates/`.
