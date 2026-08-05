# Registro Automático de Atividades + Pomodoro

Aplicação em Python para registrar atividades diárias com marcação automática de horário e Pomodoro integrado.

## Recursos

- Criação automática de arquivo diário em estrutura por ano/mês.
- Abertura automática do arquivo no Bloco de Notas.
- Monitoramento contínuo da seção NOVA ATIVIDADE com baixo consumo.
- Inserção automática de horário no formato HH:MM.
- Movimentação da atividade para a seção ATIVIDADES com separador.
- Limpeza da caixa NOVA ATIVIDADE após processamento.
- Ignora completamente a seção INFORMAÇÕES.
- Hash da região monitorada para evitar reprocessamento em salvamentos sem mudança real.
- Compilação mensal em arquivo consolidado.
- Pomodoro com foco/pausas, iniciar, pausar, reiniciar e próximo ciclo.
- Notificação e som ao fim de ciclo.

## Estrutura

O projeto segue a arquitetura solicitada:

- main.py
- config.py
- constants.py
- ui/
- monitor/
- pomodoro/
- registros/
- utils/
- data/

## Requisitos

- Python 3.11+
- Windows
- Biblioteca opcional para notificação moderna: `plyer`

Instalação opcional:

```bash
pip install plyer
```

## Execução

No diretório do projeto:

```bash
python main.py
```

## Observações

- O intervalo de monitoramento padrão é 60 segundos.
- O arquivo diário é salvo em `registro_atividades/registros_diarios/AAAA/MM/Registro-AAAA-MM-DD.txt`.
- Configurações ficam em `data/config.json` e `data/pomodoro.json`.
- Histórico simples do Pomodoro fica em `data/history.json`.
