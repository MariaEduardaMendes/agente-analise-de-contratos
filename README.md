# Sistema Multi-Agente de Análise de Contratos

**Projeto de Bloco — Desenvolvimento de Agentes Inteligentes**  
**Autora:** Maria Eduarda Mendes  
**Repositório Oficial:** [github.com/MariaEduardaMendes/agente-analise-de-contratos](https://github.com/MariaEduardaMendes/agente-analise-de-contratos)  
**Status da Entrega:** **TP4 Concluído** — Orquestração Assíncrona Completa no n8n, Governança Formal (Claude Code `settings.json` + Hooks `PreToolUse`/`PostToolUse`), Skills Reutilizáveis, Subagentes com Isolamento de Contexto, AI Agent Node e Sub-workflow Reutilizável

---

## 📖 Visão Geral

Este projeto implementa um **sistema multi-agente assíncrono e desacoplado** para extração estruturada, consulta cadastral corporativa e auditoria de governança em contratos jurídicos.

Na fase **TP4**, o **n8n** atua como o **único orquestrador real do sistema**, coordenando dois microsserviços REST independentes com ciclo assíncrono completo, governança formal no Claude Code, skills reutilizáveis e subagentes isolados:

1. **Agente 1 (Extrator Enriquecido de Contratos — `agent1/`, Porta `8001`):**
   - Microsserviço FastAPI (`main.py`) com execução real via OpenAI Agents SDK (`Runner.run` / OpenRouter) e saída tipada em Pydantic v2 (`DadosContratoExtraido` via `AgentOutputSchema(..., strict_json_schema=False)`).
   - Aciona ferramentas `@function_tool` determinísticas (`normalizar_prazos_e_datas`, `extrair_e_validar_tabela_financeira` e `consultar_cadastro_fornecedor`), integradas à base relacional `cadastro_fornecedores`, busca vetorial RAG (`rag_documentos`) e histórico `SQLiteSession` em `banco_memoria_contratos.db`.
   - Expõe `POST /run` (`202 Accepted` com `task_id`) e polling `GET /status/{task_id}`.
   - Governado formalmente por [`agent1/CLAUDE.md`](agent1/CLAUDE.md), [`agent1/AGENTS.md`](agent1/AGENTS.md), [`agent1/.claude/settings.json`](agent1/.claude/settings.json), hooks `PreToolUse`/`PostToolUse` (bloqueio oficial `exit code 2`), skill [`validacao-financeira-contratual`](agent1/.claude/skills/validacao-financeira-contratual/SKILL.md) e subagente isolado [`validador-cadastral-fornecedor`](agent1/.claude/agents/validador-cadastral-fornecedor.md).

2. **Agente 2 (Avaliador de Conformidade e Risco Contratual — `agent2/`, Porta `8002`):**
   - Microsserviço FastAPI (`main.py`) isolado, alimentado exclusivamente pelo payload estruturado roteado pelo n8n.
   - Executa inferência real via OpenAI Agents SDK (`AgenteAuditoriaRisco`) acionando a tool `@function_tool auditar_parametros_contratuais`, confrontando teto de multa rescisória (`10%`), alçada gerencial (`R$ 100.000,00`), aviso prévio (`30 dias`) e regularidade do fornecedor.
   - Emite parecer executivo tipado em Pydantic v2 (`RelatorioConformidade`).
   - Governado formalmente por [`agent2/CLAUDE.md`](agent2/CLAUDE.md), [`agent2/AGENTS.md`](agent2/AGENTS.md), [`agent2/.claude/settings.json`](agent2/.claude/settings.json), hooks `PreToolUse`/`PostToolUse`, skill [`auditoria-alcada-e-multa`](agent2/.claude/skills/auditoria-alcada-e-multa/SKILL.md) e subagente isolado [`auditor-clausulas-penais`](agent2/.claude/agents/auditor-clausulas-penais.md).

3. **Orquestração Assíncrona Completa e AI Agent Node no n8n (`workflows/`):**
   - **Workflow Principal ([`workflows/workflow_tp4_orquestrador_completo.json`](workflows/workflow_tp4_orquestrador_completo.json)):** Submete `POST /run` para o Agente 1 (`8001`), executa loop de polling (`Wait` + `GET /status/{task_id}` com tratamento de erro e conclusão), aplica roteamento condicional de integridade contratual, aciona o Agente 2 (`8002`) com novo polling, consolida os resultados sem perda de campos via nó `Merge` (`combineByPosition`) e delibera estrategicamente por meio de um **AI Agent Node** (`@n8n/n8n-nodes-langchain.agent`) conectado a **LLM Chat Model (OpenRouter)** e **Tool: Políticas de Governança** (`@n8n/n8n-nodes-langchain.toolCode`).
   - **Sub-workflow Reutilizável ([`workflows/subworkflow_polling_assincrono.json`](workflows/subworkflow_polling_assincrono.json)):** Encapsula a máquina de estados de polling assíncrono com controle dinâmico de tentativas (`Incrementar Tentativa` + `Consolidar Estado do Polling`), detecção imediata de erro e saída padronizada de timeout, chamável de forma isolada via `Execute Workflow`.

4. **Consistência Especificação $\leftrightarrow$ Código e Pipeline de Avaliação (`scripts/` e `evaluation/`):**
   - Scripts automatizados validam os hooks do Claude Code ([`scripts/test_claude_hooks.py`](scripts/test_claude_hooks.py)), a consistência entre código e `CLAUDE.md`/`AGENTS.md` ([`scripts/verificar_consistencia_especificacao.py`](scripts/verificar_consistencia_especificacao.py)) e o pipeline completo ponta a ponta ([`workflows/test_orquestracao_pipeline.py`](workflows/test_orquestracao_pipeline.py)).

---

## 🎥 Vídeo de Demonstração (Pitch Técnico — TP4)

> 🔗 **Link do Vídeo no YouTube (TP4):** [https://youtu.be/Jq7_SBp8xps](https://youtu.be/Jq7_SBp8xps)

---

## 🏛️ Arquitetura do Sistema (TP4)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        n8n — ÚNICO ORQUESTRADOR DO SISTEMA                   │
│                                                                              │
│  [Input Minuta] ─> POST /run (8001) ─> [Loop Polling GET /status + Wait]     │
│                                              │ (status == 'done')            │
│                                              ▼                               │
│                    [Roteador: Dados Válidos para Auditoria?]                 │
│                       ├── False ──> [Tratamento de Exceção Contratual]       │
│                       └── True ───┬──> [Empacotar Saída Agente 1] ─────────┐ │
│                                   │                                        │ │
│                                   ▼                                        │ │
│                       POST /run (8002) ─> [Loop Polling GET /status]       │ │
│                                              │ (status == 'done')          │ │
│                                              ▼                             ▼ │
│                                  [Empacotar Saída Agente 2] ──> [Merge Agentes]
│                                                                      │       │
│  ┌────────────────────────────────────┐                              ▼       │
│  │ Sub-workflow Reutilizável          │        [Consolidar Dossiê Final]     │
│  │ subworkflow_polling_assincrono.json│                              │       │
│  └────────────────────────────────────┘                              ▼       │
│                                          [AI Agent de Governança Estratégica]│
│                                            ├── ai_languageModel: OpenRouter  │
│                                            └── ai_tool: Políticas Governança │
│                                                                      │       │
│                                                                      ▼       │
│                                                 [Dossiê Executivo Homologado]│
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura do Repositório (TP4)

```text
agente-analise-de-contratos/
├── RELATORIO_TECNICO.md                        # Relatório Técnico Unificado Oficial (TP4)
├── README.md                                   # Documentação geral do repositório
├── diagrama.md / diagrama.png                  # Especificação visual da arquitetura
├── .claude/
│   └── settings.json                           # Permissões base do projeto no Claude Code
│
├── agent1/                                     # AGENTE 1 — Extrator Enriquecido (Porta 8001)
│   ├── CLAUDE.md / AGENTS.md                   # Fonte de verdade, contratos e matriz de requisitos
│   ├── main.py                                 # Microsserviço FastAPI (/run, /status, /health)
│   ├── agente_extracao.py                      # Extrator real via OpenAI Agents SDK + Runner.run
│   ├── subagente_cadastral.py                  # Subagente isolado de homologação cadastral
│   ├── tools.py                                # @function_tool (prazos, finanças, fornecedores)
│   ├── models.py                               # Schemas Pydantic v2 (DadosContratoExtraido)
│   ├── memoria_rag.py                          # SQLiteSession, cadastro_fornecedores e rag_documentos
│   ├── test_api.py                             # Suíte de testes REST do Agente 1
│   ├── .claude/
│   │   ├── settings.json                       # Regras allow / deny / ask e hooks (schema oficial)
│   │   ├── hooks/                              # pre_tool_use.py e post_tool_use.py (exit code 2)
│   │   ├── skills/validacao-financeira-contratual/SKILL.md
│   │   └── agents/validador-cadastral-fornecedor.md
│   ├── skills/validacao-financeira-contratual/SKILL.md
│   └── subagents/                              # README.md + validador_cadastral.md
│
├── agent2/                                     # AGENTE 2 — Auditor de Risco e Conformidade (Porta 8002)
│   ├── CLAUDE.md / AGENTS.md                   # Fonte de verdade, contratos e matriz de requisitos
│   ├── main.py                                 # Microsserviço FastAPI (/run, /status, /health)
│   ├── agente_auditoria.py                     # Auditor real via OpenAI Agents SDK + Runner.run
│   ├── subagente_penalidades.py                # Subagente isolado de cláusulas penais
│   ├── tools.py                                # @function_tool auditar_parametros_contratuais
│   ├── models.py                               # Schemas Pydantic v2 (RelatorioConformidade)
│   ├── test_api.py                             # Suíte de testes REST do Agente 2
│   ├── .claude/
│   │   ├── settings.json                       # Regras allow / deny / ask e hooks (schema oficial)
│   │   ├── hooks/                              # pre_tool_use.py e post_tool_use.py (exit code 2)
│   │   ├── skills/auditoria-alcada-e-multa/SKILL.md
│   │   └── agents/auditor-clausulas-penais.md
│   ├── skills/auditoria-alcada-e-multa/SKILL.md
│   └── subagents/                              # README.md + especialista_clausulas_penais.md
│
├── workflows/                                  # WORKFLOWS n8n (TP4)
│   ├── workflow_tp4_orquestrador_completo.json # Pipeline completo com polling, Merge e AI Agent Node
│   ├── subworkflow_polling_assincrono.json     # Sub-workflow modular reutilizável de polling
│   ├── test_orquestracao_pipeline.py           # Validação estrutural JSON + execução E2E real
│   ├── evidencia_execucao_orquestrador_tp4.json# Evidência consolidada da última execução E2E
│   └── README.md                               # Documentação dos componentes e importação no n8n
│
├── scripts/                                    # AUDITORIA E TESTES DE GOVERNANÇA
│   ├── test_claude_hooks.py                    # Testes dos hooks PreToolUse (exit 2) e PostToolUse
│   └── verificar_consistencia_especificacao.py # Auditoria automática Código ↔ CLAUDE.md/AGENTS.md
│
├── evaluation/                                 # BENCHMARK E PIPELINE DE PROMPTS
│   └── PIPELINE_PROMPTS_CONSOLIDADO.md
│
└── integration/                                # CONTRATOS FORMALIZADOS DE API
    └── contrato_api_agentes.md
```

---

## 🚀 Como Executar os Microsserviços, Workflows e Testes

### Pré-requisitos
- Python 3.10+ (ambiente virtual `.venv` configurado na raiz)
- Variáveis de ambiente em `.env` (`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENROUTER_MODEL`)

### 1. Iniciar os Microsserviços REST

```powershell
# Terminal 1 — Agente 1 (Extrator, Porta 8001)
uvicorn agent1.main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 — Agente 2 (Auditor de Conformidade, Porta 8002)
uvicorn agent2.main:app --host 0.0.0.0 --port 8002 --reload
```
- Swagger Agente 1: `http://localhost:8001/docs`
- Swagger Agente 2: `http://localhost:8002/docs`

### 2. Executar as Suítes de Verificação Automatizada

```powershell
# 1. Validar configuração formal do Claude Code
claude doctor

# 2. Testar hooks PreToolUse (bloqueio exit=2) e PostToolUse
.\.venv\Scripts\python.exe scripts/test_claude_hooks.py

# 3. Auditar consistência entre código-fonte, skills, subagentes e CLAUDE.md/AGENTS.md
.\.venv\Scripts\python.exe scripts/verificar_consistencia_especificacao.py

# 4. Testar API REST dos dois agentes individualmente
Set-Location agent1; ..\.venv\Scripts\python.exe test_api.py
Set-Location agent2; ..\.venv\Scripts\python.exe test_api.py

# 5. Validar JSONs do n8n e executar orquestração assíncrona ponta a ponta
.\.venv\Scripts\python.exe workflows/test_orquestracao_pipeline.py
```

### 3. Importar os Workflows no n8n
1. Abra sua instância do n8n (ex.: `http://localhost:5678`).
2. Vá em **Workflows** → **Import from File** e importe:
   - [`workflows/subworkflow_polling_assincrono.json`](workflows/subworkflow_polling_assincrono.json)
   - [`workflows/workflow_tp4_orquestrador_completo.json`](workflows/workflow_tp4_orquestrador_completo.json)
3. Com ambos os serviços ativos nas portas `8001` e `8002`, clique em **Execute Workflow** para rodar o ciclo completo até o **AI Agent de Governança Estratégica**.
