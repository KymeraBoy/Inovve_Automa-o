# OPERACIONAL - Nova Interface do Gerador

Este modulo cria uma interface grafica paralela ao fluxo antigo de terminal.

Objetivo desta versao:
- nao altera `gerar_documento.py`;
- nao substitui o sistema atual;
- organiza documentos em fila operacional;
- permite validacao e armazenamento temporario;
- possui motor dedicado de geracao para o fluxo operacional.

## Estrutura

- `main.py`: ponto de entrada da interface PySide6.
- `interface/janela_principal.py`: janela principal e orquestracao da tela.
- `interface/tabela_documentos.py`: tabela editavel da fila.
- `interface/formularios.py`: painel de campos dinamicos por tipo/subtipo.
- `modelos/documento.py`: modelo de dados do documento/chamado.
- `servicos/municipios.py`: leitura de municipios e metadados dos arquivos `.tex`.
- `servicos/empresas.py`: listagem e inferencia de empresas.
- `servicos/validacao.py`: validacoes de regras e formatacao monetaria.
- `servicos/fila.py`: gerenciamento e persistencia da fila em JSON.
- `servicos/gerador_operacional.py`: motor dedicado de montagem e compilacao LaTeX/PDF.
- `servicos/gerador_adapter.py`: adaptador entre fila e motor dedicado.
- `configuracao/config.py`: caminhos base da aplicacao.

## Como executar

1. Instale dependencia:

```bash
pip install PySide6
```

2. Execute a interface a partir da pasta `OPERACIONAL`:

```bash
python main.py
```

## Funcionalidades da primeira meta

- abertura de interface grafica;
- criacao e remocao de documentos na fila;
- edicao direta na tabela (municipio, empresa, tipo, subtipo, UC, numero);
- campos condicionais no painel lateral:
  - OFI: origem e codigo;
  - Perda nos Reatores: valor, periodo e imagens;
  - Perda por Transformacao: imagens obrigatorias;
- selecao de imagens via dialogo do sistema;
- validacao da fila com retorno por documento;
- botao `GERAR DOCUMENTOS` com geracao real de .tex e tentativa de compilacao PDF;
- salvamento/carregamento da fila em JSON.

## Observacoes

- A compilacao de PDF depende de `pdflatex` ou `xelatex` no PATH do sistema.
- Em caso de falha de compilacao, o .tex montado permanece salvo na pasta de saida.
