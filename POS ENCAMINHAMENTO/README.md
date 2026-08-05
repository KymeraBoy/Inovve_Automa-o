# Automação de Arquivamento de Tese (POS ENCAMINHAMENTO)

## Arquitetura adotada

A solução foi separada em módulos para manter baixo acoplamento e facilitar evolução:

- `main.py`: ponto de entrada, com interação mínima (seleção do PDF e mensagens finais).
- `config.py`: centraliza regras e caminhos fixos (empresas, tipos, nomes de pastas).
- `parser.py`: valida e interpreta o nome do PDF para extrair tipo, código e município.
- `finder.py`: localiza automaticamente o município e resolve a pasta correta de destino.
- `organizer.py`: orquestra a criação da estrutura e a movimentação do arquivo.
- `utils.py`: exceções de domínio e utilitários de normalização/formatos de mensagem.

Essa organização permite modificar regras sem mexer na lógica principal:

- Novas empresas: alterar apenas `COMPANY_ROOTS` em `config.py`.
- Novos estados: basta criar as pastas no filesystem (a busca já percorre Empresa/Estado/Município).
- Novos tipos de tese: incluir prefixos e estrutura em `config.py`.
- Mudança de subpastas: editar `PROCESS_SUBFOLDERS` em `config.py`.

## Regras de nome de arquivo

Formato esperado:

TIPO-CODIGO-MUNICIPIO-... .pdf

Exemplo:

REC-001_2026-CACIMBA_DE_DENTRO-TAXA_CIP-439836_8.pdf

Mapeamento padrão:

- `REC` -> Reclamação
- `REQ`, `PET`, `RQS`, `REQUISICAO`, `REQUISIÇÃO` -> Requerimento

## Como usar

1. Ajuste os caminhos reais em `COMPANY_ROOTS` no arquivo `config.py`.
2. Execute:

```bash
python main.py
```

3. Selecione o PDF.
4. O programa faz o restante automaticamente.

## Comportamento da automação

### Quando for REC

1. Localiza o município automaticamente.
2. Entra em `RECLAMAÇÕES`.
3. Cria uma pasta com o nome do PDF (sem extensão, por padrão).
4. Cria as subpastas:
   - `ANEEL`
   - `PAGAMENTO`
   - `DOCUMENTOS RECEBIDOS`
   - `RECLAMAÇÃO FORMAL`
   - `E-MAILS`
5. Move o PDF para `RECLAMAÇÃO FORMAL`.

### Quando for REQ

1. Localiza o município automaticamente.
2. Escolhe a primeira pasta existente entre:
   - `REQUERIMENTOS`
   - `PETIÇÕES`
   - `REQUISIÇÕES`
3. Cria a pasta do processo.
4. Cria as subpastas:
   - `ANEEL`
   - `DOCUMENTOS RECEBIDOS`
   - `REQUERIMENTO FORMAL`
   - `E-MAILS`
5. Move o PDF para `REQUERIMENTO FORMAL`.

## Tratamento de erros

A aplicação apresenta mensagens claras para:

- nome de PDF inválido;
- município não encontrado;
- estrutura de pastas ausente;
- caminho raiz de empresa inválido;
- pasta do processo já existente;
- arquivo já existente no destino;
- falta de permissão;
- falha de criação/movimentação por erro de sistema.

## Dependências

A solução usa apenas bibliotecas padrão do Python:

- `pathlib`
- `shutil`
- `re`
- `dataclasses`
- `tkinter`
- `typing`
- `unicodedata`
