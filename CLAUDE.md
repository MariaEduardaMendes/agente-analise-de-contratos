# CLAUDE.md

Este arquivo fornece orientações ao Claude Code (claude.ai/code) ao trabalhar com o código neste repositório.

## Visão Geral do Projeto

Este repositório descreve um **sistema multi-agente de análise de contratos** construído com n8n, Python e LLMs. O sistema recebe o texto de um contrato, extrai dados estruturados e os valida contra regras de negócio, gerando um relatório de conformidade em Markdown.

## Arquitetura

O sistema é composto por dois agentes orquestrados via n8n:

### Agente 1: Extração
- **Entrada:** Nó de webhook/entrada do n8n recebe o texto bruto do contrato
- **Processamento:** Script Python usando o SDK da OpenAI envia o texto para um LLM com Structured Outputs, garantindo uma resposta JSON validada
- **Saída:** Payload JSON estruturado representando os dados extraídos do contrato

### Agente 2: Validação e Ferramentas
- **Entrada:** Payload JSON do Agente 1
- **Ferramentas:** Consulta um banco de dados local (SQLite ou DuckDB) para obter regras de negócio
- **Processamento:** Agente validador Python envia dados + regras para um LLM realizar a análise de conformidade
- **Saída:** Relatório de conformidade em Markdown entregue via nó de saída do n8n ao usuário ou sistema de destino

### Fluxo Resumido
```
Usuário/Webhook → n8n → Python (SDK OpenAI + Structured Outputs) → LLM
                                                                      ↓
Usuário/Sistema ← n8n ← Agente Validador Python ↔ SQLite/DuckDB ← Payload JSON
                               ↕
                              LLM (análise de conformidade)
```

## Tecnologias Principais
- **n8n** — orquestração e tratamento de webhooks
- **Python** — scripts dos agentes (SDK OpenAI)
- **Structured Outputs** — garante JSON validado a partir do LLM
- **SQLite / DuckDB** — armazenamento local das regras de negócio
- **LLM** — extração e raciocínio de conformidade (compatível com OpenAI)
