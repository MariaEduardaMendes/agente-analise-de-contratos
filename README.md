# Sistema Multi-Agente de Análise de Contratos

**Projeto de Bloco — Desenvolvimento de Agentes Inteligentes**  
**Autora:** Maria Eduarda Mendes  
**Repositório Oficial:** [github.com/MariaEduardaMendes/agente-analise-de-contratos](https://github.com/MariaEduardaMendes/agente-analise-de-contratos)  
**Status da Entrega:** Microsserviços REST FastAPI, Context Engineering e Workflow n8n (TP3)  

---

## 📖 Visão Geral

Este projeto implementa um **sistema multi-agente assíncrono e desacoplado** para extração estruturada e auditoria de governança em contratos jurídicos.

Na fase **TP3**, o sistema foi reestruturado em **dois microsserviços REST independentes** orquestrados deterministicamente via **n8n**:

1. **Agente 1 (Extrator Enriquecido — `agent1/`):**
   - Microsserviço FastAPI na porta `8001`.
   - Extrai entidades e aciona ferramentas Python determinísticas para normalização de datas no padrão ISO-8601 (`normalizar_prazos_e_datas`) e conferência matemática de parcelas (`extrair_e_validar_tabela_financeira`).
   - Responde com `POST /run` retornando `202 Accepted` com `task_id` e execução assíncrona via `BackgroundTasks`.
   - Saída tipada via Pydantic v2 (`DadosContratoExtraido`).
   - Contexto exclusivo definido em `agent1/CLAUDE.md`.

2. **Agente 2 (Avaliador de Conformidade e Risco — `agent2/`):**
   - Microsserviço FastAPI na porta `8002`.
   - Recebe os dados estruturados do contrato repassados pelo orquestrador e confronta com as diretrizes corporativas (`auditar_parametros_contratuais_fn` e `consultar_base_regras_negocio_fn`).
   - Calcula score de conformidade (0 a 100), classifica o nível de risco (`BAIXO`, `MEDIO`, `ALTO`, `CRITICO`) e emite parecer executivo estruturado em Pydantic v2 (`RelatorioConformidade`).
   - Responde com `POST /run` (202 Accepted) e polling em `GET /status/{task_id}` via `BackgroundTasks`.
   - Contexto exclusivo definido em `agent2/CLAUDE.md`.

3. **Orquestração Determinística via n8n (`workflows/`):**
   - Primeiro workflow implementado conectando o nó de entrada HTTP ao Agente 1, com captura assíncrona do payload estruturado (`workflows/workflow_tp3_agente_extracao.json`).

4. **Pipeline de Prompts Consolidado (`evaluation/`):**
   - Documento formal avaliando 4 variantes com métricas objetivas (TCS, TIT, AFC, ASC, IGQ), ganho de +566% e diagnóstico sistemático de falhas (`evaluation/PIPELINE_PROMPTS_CONSOLIDADO.md`).

---

## 🎥 Vídeo de Demonstração (Pitch Técnico do TP3)

Demonstração prática dos dois microsserviços em execução separada, validação dos endpoints REST via Swagger/cURL, orquestração no n8n e justificativas das decisões de arquitetura e Context Engineering:

> 🔗 **Link direto do YouTube:** [https://youtu.be/UsQMdx9zVFo](https://youtu.be/UsQMdx9zVFo)


---

## 🏛️ Arquitetura do Sistema

```
┌─────────────────┐      HTTP POST /run       ┌────────────────────────┐
│                 │ ────────────────────────> │   Agente 1 (FastAPI)   │
│                 │ <──────────────────────── │   Porta 8001 (/run)    │
│                 │      202 Accepted         └────────────────────────┘
│                 │                                        │ BackgroundTask
│                 │      HTTP GET /status                  ▼
│       n8n       │ ────────────────────────> ┌────────────────────────┐
│  Orquestrador   │ <──────────────────────── │   Status: 'done'       │
│  Determinístico │      Payload Extraído     │   DadosContratoExtraido│
│                 │                           └────────────────────────┘
│                 │
│                 │      HTTP POST /run       ┌────────────────────────┐
│                 │ ────────────────────────> │   Agente 2 (FastAPI)   │
│                 │ <──────────────────────── │   Porta 8002 (/run)    │
│                 │      202 Accepted         └────────────────────────┘
│                 │                                        │ BackgroundTask
│                 │      HTTP GET /status                  ▼
│                 │ ────────────────────────> ┌────────────────────────┐
│                 │ <──────────────────────── │   Status: 'done'       │
│                 │      Relatório Risco      │   RelatorioConformidade│
└─────────────────┘                           └────────────────────────┘
```

---

## 📁 Estrutura do Repositório (TP3)

```text
agente-analise-de-contratos/
├── RELATORIO_TECNICO.md            # Relatório Técnico Unificado Oficial da Entrega
├── README.md                       # Documentação geral do repositório
│
├── agent1/                         # PRIMEIRO AGENTE (Extrator Enriquecido de Contratos)
│   ├── CLAUDE.md                   # Contexto e regras exclusivas do Agente 1
│   ├── main.py                     # Microsserviço FastAPI (Porta 8001) com BackgroundTasks
│   ├── agente_extracao.py          # Pipeline central de extração estruturada
│   ├── tools.py                    # Ferramentas Python de normalização temporal e matemática
│   ├── models.py                   # Schemas Pydantic v2 (DadosContratoExtraido)
│   ├── memoria_rag.py              # Memória de sessão SQLite e RAG vetorial
│   ├── contrato_exemplo.txt        # Minuta jurídica de homologação
│   ├── test_api.py                 # Testes automatizados dos endpoints REST
│   └── requirements.txt            # Dependências específicas do Agente 1
│
├── agent2/                         # SEGUNDO AGENTE (Avaliador de Conformidade e Risco)
│   ├── CLAUDE.md                   # Contexto e regras exclusivas do Agente 2
│   ├── main.py                     # Microsserviço FastAPI (Porta 8002) com BackgroundTasks
│   ├── agente_auditoria.py         # Motor de auditoria contra regras corporativas
│   ├── tools.py                    # Ferramentas Python de checagem de alçadas e multas
│   ├── models.py                   # Schemas Pydantic v2 (RelatorioConformidade)
│   ├── test_api.py                 # Testes automatizados dos endpoints REST
│   └── requirements.txt            # Dependências específicas do Agente 2
│
├── workflows/                      # WORKFLOWS DO N8N
│   └── workflow_tp3_agente_extracao.json # Workflow oficial homologado no n8n
│
├── evaluation/                     # PIPELINE DE PROMPTS E AVALIAÇÃO
│   └── PIPELINE_PROMPTS_CONSOLIDADO.md # Benchmark, diagnóstico e decisão final técnica
│
├── integration/                    # CONTRATOS DE INTERFACE E APIS
│   └── contrato_api_agentes.md     # Especificação técnica dos endpoints, schemas e estados
│
└── docs/                           # DOCUMENTAÇÃO AUXILIAR
    ├── CONFIGURACAO_AMBIENTE.md    # Detalhamento do ambiente Antigravity + Claude Code
    └── screenshots/                # Evidências visuais de execução
```

---

## 🚀 Como Executar os Microsserviços e Testes

### Pré-requisitos
- Python 3.10+ (recomendado `.venv` ativo)
- Dependências instaladas:
  ```bash
  pip install fastapi uvicorn pydantic python-dotenv requests
  ```

### 1. Iniciar os Serviços REST:

- **Agente 1 (Extração de Contratos):**
  ```powershell
  uvicorn agent1.main:app --host 0.0.0.0 --port 8001 --reload
  ```
  *Swagger interativo: `http://localhost:8001/docs`*

- **Agente 2 (Conformidade e Risco):**
  ```powershell
  uvicorn agent2.main:app --host 0.0.0.0 --port 8002 --reload
  ```
  *Swagger interativo: `http://localhost:8002/docs`*

### 2. Executar Testes Automatizados dos Endpoints:

- Testar Agente 1 (`POST /run` e `GET /status`):
  ```powershell
  python agent1/test_api.py
  ```

- Testar Agente 2 (`POST /run` e `GET /status`):
  ```powershell
  python agent2/test_api.py
  ```

### 3. Importar o Workflow no n8n:
1. Abra o n8n no navegador (`http://localhost:5678`).
2. Clique no menu superior direito do editor de workflows e selecione **"Import from File"**.
3. Escolha o arquivo [`workflows/workflow_tp3_agente_extracao.json`](workflows/workflow_tp3_agente_extracao.json).
4. Clique em **"Execute Workflow"** para validar o acionamento HTTP e a captura de status assíncrona.
