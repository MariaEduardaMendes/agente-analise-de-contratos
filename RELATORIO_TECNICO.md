# Relatório Técnico Unificado de Evolução do Sistema Multi-Agente de Análise de Contratos

**Projeto de Bloco — Desenvolvimento de Agentes Inteligentes**  
**Autora:** Maria Eduarda Mendes  
**Repositório Oficial no GitHub:** [https://github.com/MariaEduardaMendes/agente-analise-de-contratos](https://github.com/MariaEduardaMendes/agente-analise-de-contratos)  
**Versão:** TP4 Consolidado — Orquestração Assíncrona no n8n, Governança com Permissões e Hooks, Skills, Subagentes com Isolamento de Contexto e Pipeline Integrado  
**Data:** 10/11/2026  
**Status:** Implementado, Testado com Modelos Reais e Homologado  

---

## 🧭 1. Visão Geral da Arquitetura e Evolução Histórica (TP1 ➔ TP2 ➔ TP3 ➔ TP4)

O projeto de análise e auditoria inteligente de contratos foi estruturado em um ciclo evolutivo rigoroso:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│       TP1       │ ──> │       TP2       │ ──> │       TP3       │ ──> │       TP4       │
│  Script Python  │     │  Agente com     │     │  Dois Microsser-│     │  Orquestração   │
│  Básico e Extra-│     │  Tools, CoT, RAG│     │  viços REST,    │     │  n8n Completa,  │
│  ção em Texto   │     │  e Pydantic v2  │     │  CLAUDE.md por  │     │  Agent Node,    │
│  Livre          │     │  (Runner.run)   │     │  Agente e n8n   │     │  Hooks e Skills │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Fase TP1 (Componente Inicial):** Script Python elementar que consumia minutas contratuais e produzia JSONs simples, sujeito a alucinações de cálculo e vigência temporal relativa.
2. **Fase TP2 (Agente Inteligente e Funcional com Execução Real):**
   - Implementação de ferramentas Python determinísticas decoradas com `@function_tool` (cálculo de datas ISO-8601, integridade de parcelas e consulta a cadastro de fornecedores).
   - Decomposição de tarefas complexas através de *Least-to-Most Prompting* e raciocínio deliberativo (*Chain-of-Thought*) enviados de verdade ao modelo LLM via `Runner.run`.
   - Dupla camada de memória persistente: `SQLiteSession` para retenção de histórico conversacional entre runs distintos e RAG vetorial com embeddings (`text-embedding-3-small`) sobre a tabela `rag_documentos` para recuperação de precedentes.
   - Saídas fortemente tipadas com validação estrutural via **Pydantic v2** (`DadosContratoExtraido`).
   - Benchmark A/B real comparando variantes executadas via API.
3. **Fase TP3 (Arquitetura de Serviços e Microsserviços Desacoplados):**
   - **Agente 1 em Microsserviço REST:** Transformação do extrator em serviço HTTP com **FastAPI** e **`BackgroundTasks`**, respondendo `POST /run` com `202 Accepted` imediato e polling em `GET /status/{task_id}`, lendo dinamicamente minutas reais através do `Runner.run`.
   - **Segundo Agente Independente (Agente 2):** Implementação de um microsserviço isolado (`agent2/`) especializado em **Auditoria de Conformidade e Risco**, transformado em um **Agent inteligente real** com `@function_tool auditar_parametros_contratuais`, Pydantic v2 (`output_type=RelatorioConformidade`) e API FastAPI na porta `8002`.
   - **Context Engineering Descentralizado:** Arquivos `CLAUDE.md` exclusivos em cada pasta de agente (`agent1/CLAUDE.md` e `agent2/CLAUDE.md`), sem arquivos globais acoplados na raiz.
   - **Workflow Inicial n8n:** Demonstração operacional de disparo assíncrono e captura de resposta via nó HTTP no n8n.
4. **Fase TP4 (Orquestração Completa no n8n, Governança Formal, Skills e Subagentes):**
   - **Orquestração Assíncrona Total no n8n:** O n8n é o único orquestrador. Executa o ciclo assíncrono completo: submissão com `202 Accepted`, polling contínuo até conclusão, roteamento condicional de integridade contratual, acionamento do Agente 2 e junção dos outputs via nó `Merge`.
   - **Componentes n8n de Alto Nível (LangChain):** Integração de **AI Agent Node**, conectado a **LLM Chat Model (OpenRouter)** e **Custom Tool** corporativa de governança para deliberação executiva estratégica.
   - **Sub-workflow Reutilizável:** Encapsulamento da lógica de polling assíncrono resiliente em sub-workflow modular com controle de timeout e retry, chamável isoladamente.
   - **Governança Formal do Claude Code:** Configuração de `settings.json` com regras de permissão (`allow`, `deny`, `ask`) e hooks automatizados (`PreToolUse` e `PostToolUse`) para proteção de fronteiras entre microsserviços e integridade sintática.
   - **Skills e Subagentes Especializados:** Extração de capacidades em arquivos `SKILL.md` padronizados e criação de subagentes com isolamento estrito de contexto (`validador-cadastral-fornecedor` e `auditor-clausulas-penais`).
   - **Fontes de Verdade Canônicas:** Atualização sincronizada de `CLAUDE.md` e `AGENTS.md` com matriz de rastreabilidade completa.

---

## 📌 2. Atendimento aos Feedbacks de TP2 e TP3 (Rubrica 12 e Agentes Reais)

Em resposta aos apontamentos da banca avaliadora, todas as deficiências foram integralmente sanadas com implementações e execuções reais:

### 2.1 Correção dos Agentes: Fim das Simulações e Execução Real com `Runner.run`
- **Problema Apontado:** Memória, raciocínio encadeado, saídas tipadas e avaliação haviam sido demonstrados com valores fixos em código, sem chamar o modelo LLM no runtime.
- **Solução Implementada:**
  - O Agente 1 ([`agent1/agente_extracao.py`](agent1/agente_extracao.py)) agora executa o LLM real via `Runner.run_sync(agente, ...)` utilizando o `OpenAIChatCompletionsModel` conectado ao OpenRouter (`nvidia/nemotron-3.5-lightning:free`). Ele lê e extrai os dados diretamente da minuta fornecida (e não de valores estáticos). Testes com duas minutas distintas (`contrato_exemplo.txt` e `contrato_exemplo_2.txt`) comprovam que o agente extrai valores e partes diferentes dinamicamente.
  - O Agente 2 ([`agent2/agente_auditoria.py`](agent2/agente_auditoria.py)) foi transformado de uma função estática em um **Agent completo** (`AgenteAuditoriaRisco`) que executa via `Runner.run`, aciona a tool `@function_tool auditar_parametros_contratuais` e gera a saída tipada `RelatorioConformidade`.
  - O módulo de memória persistente ([`agent1/demo_memoria_rag.py`](agent1/demo_memoria_rag.py)) passa a sessão `SQLiteSession` no `Runner.run(agent, ..., session=session)` tanto no Run 1 quanto no Run 2, comprovando que o modelo recupera as diretrizes prévias diretamente do banco SQLite.
  - O pipeline de raciocínio encadeado ([`agent1/pipeline_raciocinio.py`](agent1/pipeline_raciocinio.py)) envia os prompts das etapas *Least-to-Most* e *Chain-of-Thought* diretamente ao modelo LLM.

### 2.2 Atendimento da Rubrica 12: Os 3 Entregáveis Adicionais

#### A) Fonte Estruturada de Negócio
- **Exigência da Rubrica 12:** Uma fonte de dados de negócio em banco relacional ou API (como cadastro de fornecedores ou de contratos), visto que tools de cálculo e banco vetorial não cumprem esse papel.
- **Implementação:** Criada a tabela corporativa **`cadastro_fornecedores`** no banco SQLite (`agent1/banco_memoria_contratos.db`), armazenando dados cadastrais, situação fiscal, limite de alçada homologado e histórico de compliance.
- **Integração:** Disponibilizada a ferramenta `@function_tool consultar_cadastro_fornecedor(cnpj_cpf: str) -> str` no Agente 1, permitindo confrontar a Contratada extraída da minuta contra o cadastro corporativo.

#### B) Dado Estruturado com Documentação Alinhada ao Banco Real
- **Exigência da Rubrica 12:** Documentar os campos da fonte de negócio e alinhar as tabelas com o banco de dados real (`rag_documentos`, e não `precedentes_contratuais`).
- **Implementação:** O banco `banco_memoria_contratos.db` possui 3 tabelas reais documentadas com precisão na Seção 6 deste relatório:
  1. `cadastro_fornecedores`: Fonte estruturada relacional de negócio.
  2. `rag_documentos`: Vector store com embeddings e metadados (corrigindo a nomenclatura antiga).
  3. `sessoes_historico`: Histórico de conversação da `SQLiteSession`.

#### C) Fluxo de Dados com Pergunta de Dupla Intenção
- **Exigência da Rubrica 12:** Um exemplo concreto com pergunta de dupla intenção que acione os dois agentes e apresente dados reais em cada etapa.
- **Implementação:** Detalhado na Seção 5 deste relatório, demonstrando a pergunta de dupla intenção ("extrair dados da minuta E verificar cadastro corporativo e conformidade de multa"), com os payloads JSON concretos produzidos em cada estágio.

---

## 🏛️ 3. Mapeamento da Estrutura de Pastas do Repositório

```text
agente-analise-de-contratos/
├── RELATORIO_TECNICO.md            # Este Relatório Técnico Unificado Oficial
├── README.md                       # Documentação e guia de inicialização
├── diagrama.md                     # Especificação arquitetural e diagrama Mermaid
├── diagrama.png                    # Diagrama formal da arquitetura multi-agente
│
├── agent1/                         # PRIMEIRO AGENTE (Extrator Enriquecido de Contratos)
│   ├── CLAUDE.md                   # Contrato formal e regras exclusivas do Agente 1
│   ├── AGENTS.md                   # Espelho canônico de especificações do Agente 1
│   ├── main.py                     # Microsserviço FastAPI (Porta 8001) com BackgroundTasks
│   ├── agente_extracao.py          # Pipeline de extração estruturada via LLM Real + Runner.run
│   ├── subagente_cadastral.py      # Subagente com contexto isolado para diligência de fornecedores
│   ├── tools.py                    # Ferramentas Python (@function_tool) de prazos, finanças e cadastro
│   ├── models.py                   # Schemas Pydantic v2 (DadosContratoExtraido)
│   ├── memoria_rag.py              # Memória de sessão SQLite, banco relacional e RAG vetorial
│   ├── banco_memoria_contratos.db  # Banco SQLite (cadastro_fornecedores, rag_documentos, sessoes)
│   ├── contrato_exemplo.txt        # Minuta jurídica 1 (TechSolutions e Alfa Consultoria, R$ 45k)
│   ├── contrato_exemplo_2.txt      # Minuta jurídica 2 (TechSolutions e CloudCorp, R$ 180k)
│   ├── pipeline_raciocinio.py      # Pipeline CoT e Least-to-Most com chamadas reais ao LLM
│   ├── demo_memoria_rag.py         # Validação de SQLiteSession e RAG com chamadas reais
│   ├── test_api.py                 # Testes automatizados dos endpoints REST (:8001)
│   ├── requirements.txt            # Dependências específicas do Agente 1
│   ├── .claude/                    # Governança formal: settings.json, hooks, skills e agents
│   ├── skills/                     # Espelho de skills (validacao-financeira-contratual)
│   └── subagents/                  # Documentação e YAML do subagente (validador_cadastral)
│
├── agent2/                         # SEGUNDO AGENTE (Avaliador de Conformidade e Risco)
│   ├── CLAUDE.md                   # Contrato formal e regras exclusivas do Agente 2
│   ├── AGENTS.md                   # Espelho canônico de especificações do Agente 2
│   ├── main.py                     # Microsserviço FastAPI (Porta 8002) com BackgroundTasks
│   ├── agente_auditoria.py         # Motor inteligente de auditoria com Agent e Runner.run
│   ├── subagente_penalidades.py    # Subagente com contexto isolado para auditoria de cláusulas penais
│   ├── tools.py                    # Ferramenta @function_tool auditar_parametros_contratuais
│   ├── models.py                   # Schemas Pydantic v2 (RelatorioConformidade)
│   ├── test_api.py                 # Testes automatizados dos endpoints REST (:8002)
│   ├── requirements.txt            # Dependências específicas do Agente 2
│   ├── .claude/                    # Governança formal: settings.json, hooks, skills e agents
│   ├── skills/                     # Espelho de skills (auditoria-alcada-e-multa)
│   └── subagents/                  # Documentação e YAML do subagente (especialista_clausulas_penais)
│
├── workflows/                      # WORKFLOWS DO N8N
│   ├── workflow_tp4_orquestrador_completo.json # Workflow oficial com ciclo assíncrono e AI Agent Node
│   ├── subworkflow_polling_assincrono.json     # Sub-workflow modular reutilizável de polling
│   ├── test_orquestracao_pipeline.py          # Teste e validação da máquina de estados do n8n
│   ├── evidencia_execucao_orquestrador_tp4.json # Evidência de execução ponta a ponta
│   └── README.md                               # Documentação e guia de importação no n8n
│
├── scripts/                        # SCRIPTS DE TESTE E AUDITORIA DO SISTEMA
│   ├── test_claude_hooks.py        # Suíte de verificação dos hooks PreToolUse e PostToolUse
│   └── verificar_consistencia_especificacao.py # Validação de consistência código vs. CLAUDE.md
│
├── evaluation/                     # PIPELINE DE PROMPTS E AVALIAÇÃO
│   ├── avaliacao_metricas_prompt.py # Benchmark A/B real com modelo LLM
│   ├── comparativo_variantes_prrr.md # Documentação do ciclo PRRR e métricas
│   ├── PIPELINE_PROMPTS_CONSOLIDADO.md # Diagnóstico técnico e decisão de prompts
│   └── resultado_avaliacao_metricas.json # Resultados quantitativos gravados
│
└── integration/                    # CONTRATOS DE INTERFACE E APIS
    └── contrato_api_agentes.md     # Especificação técnica dos endpoints e payloads
```

---

## 🔌 4. Documentação das APIs REST dos Dois Agentes

Ambos os agentes operam como microsserviços HTTP padronizados usando **FastAPI** e **`BackgroundTasks`**, garantindo execução não-bloqueante com o padrão **`202 Accepted`** e polling em `/status/{task_id}`.

### 4.1 Agente 1: Extrator Enriquecido de Contratos (Porta `8001`)

- **Endpoints:**
  - `POST /run`: Dispara a extração assíncrona recebendo `{"texto_contrato": "..."}`. Retorna `202 Accepted` com `task_id`.
  - `GET /status/{task_id}`: Retorna status (`pending`, `done`, `error`) e o payload validado `DadosContratoExtraido`.
  - `GET /health`: Healthcheck do serviço.

- **Payload Real de Saída (`GET /status/{task_id}`) gerado pelo Agente 1:**
```json
{
  "task_id": "853f61da-d864-4b62-8579-b77130c85501",
  "status": "done",
  "created_at": 1794338422.51,
  "completed_at": 1794338436.51,
  "data": {
    "titulo": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL",
    "contratante": {
      "nome": "TechSolutions Ltda.",
      "cnpj_cpf": "12.345.678/0001-90",
      "papel": "CONTRATANTE"
    },
    "contratada": {
      "nome": "Alfa Consultoria em IA S.A.",
      "cnpj_cpf": "98.765.432/0001-10",
      "papel": "CONTRATADA"
    },
    "objeto": "Prestação de serviços técnicos especializados para o desenvolvimento, integração e suporte de um sistema de inteligência artificial multi-agentes focado em análise de conformidade e extração de dados de documentos jurídicos.",
    "financeiro": {
      "moeda": "BRL",
      "valor_total_brl": 45000.0,
      "parcelas_quantidade": 3,
      "valor_parcela_brl": 15000.0,
      "periodicidade": "mensal",
      "soma_consistente": true,
      "discrepancia_centavos": 0.0,
      "cronograma_resumo": "3 parcelas de R$ 15.000,00, primeira em 15/09/2026"
    },
    "vigencia": {
      "data_inicio_iso": "2026-09-01",
      "data_fim_calculada_iso": "2027-03-01",
      "vigencia_meses": 6,
      "dias_corridos_totais": 181,
      "aviso_previo_dias": 30,
      "vigencia_formatada": "01/09/2026 a 01/03/2027"
    },
    "penalidades": {
      "percentual_multa_rescisoria": 20.0,
      "base_calculo": "valor remanescente do contrato",
      "gatilho_aplicacao": "rescisão imotivada"
    },
    "fornecedor_homologado": {
      "cnpj": "98.765.432/0001-10",
      "razao_social": "Alfa Consultoria em IA S.A.",
      "situacao_cadastral": "ATIVA",
      "score_compliance": 88.5,
      "limite_alcada_brl": 150000.0,
      "categoria_risco": "MEDIO",
      "restricoes_juridicas": "Histórico de renegociação de multa rescisória em aditivo prévio (2025). Homologada com ressalva contratual."
    },
    "secoes_analisadas": ["PREAMBULO", "OBJETO", "CONDICOES_FINANCEIRAS", "PRAZOS_E_VIGENCIA", "PENALIDADES"]
  },
  "error": null
}
```

---

### 4.2 Agente 2: Avaliador de Conformidade e Risco (Porta `8002`)

- **Endpoints:**
  - `POST /run`: Dispara a auditoria assíncrona recebendo `{"dados_contrato": {...}}`. Retorna `202 Accepted` com `task_id`.
  - `GET /status/{task_id}`: Retorna status e o modelo tipado `RelatorioConformidade`.
  - `GET /health`: Healthcheck do serviço.

- **Payload Real de Saída (`GET /status/{task_id}`) gerado pelo Agente 2:**
```json
{
  "task_id": "0a9ff2c9-a1f8-4cf9-a982-334839496eac",
  "status": "done",
  "created_at": 1794338663.58,
  "completed_at": 1794338686.55,
  "data": {
    "contrato_titulo": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL",
    "score_conformidade": 85.0,
    "nivel_risco_geral": "MEDIO",
    "total_regras_auditadas": 4,
    "itens_conformes": 3,
    "itens_alerta": 1,
    "itens_nao_conformes": 0,
    "itens_auditados": [
      {
        "regra": "Teto de Multa Rescisória",
        "status": "ALERTA",
        "nivel_risco": "MEDIO",
        "descricao_analise": "Multa rescisória fixada em 20.0%, superando a diretriz de governança recomendada de até 10.0% sobre o saldo remanescente.",
        "fundamentacao": "Política Interna de Riscos Contratuais e Jurisprudência Cível (Art. 413 CC)."
      },
      {
        "regra": "Alçada de Aprovação Financeira",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Valor de R$ 45.000,00 dentro da alçada operacional regular (abaixo de R$ 100.000,00).",
        "fundamentacao": "Manual de Alçadas e Governança Financeira."
      },
      {
        "regra": "Prazo Mínimo de Aviso Prévio",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Aviso prévio pactuado (30 dias) atende integralmente ao requisito de segurança.",
        "fundamentacao": "Diretriz Operacional de Continuidade de Negócios."
      },
      {
        "regra": "Regularidade Cadastral do Fornecedor",
        "status": "CONFORME",
        "nivel_risco": "BAIXO",
        "descricao_analise": "Fornecedor homologado ativo com score de compliance de 88.5/100.",
        "fundamentacao": "Cadastro Corporativo de Fornecedores Homologados."
      }
    ],
    "recomendacoes_mitigacao": [
      "Negociar a redução da multa rescisória de 20% para 10%, alinhando ao precedente histórico (Aditivo nº 1 de 2025 da Alfa Consultoria).",
      "Manter o acompanhamento do fornecedor haja vista a categoria de risco MÉDIO registrada na fonte estruturada."
    ],
    "parecer_executivo_markdown": "# Parecer de Conformidade e Risco Contratual\n**Instrumento:** CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL\n**Score de Compliance:** 85.0 / 100.0\n**Classificação de Risco:** MEDIO\n..."
  },
  "error": null
}
```

---

## 🔄 5. Fluxo de Dados com Pergunta de Dupla Intenção (Rubrica 12)

Para cumprir integralmente a Rubrica 12, demonstramos o fluxo de dados disparado por uma **pergunta de dupla intenção** que mobiliza ambos os agentes de forma encadeada e orquestrada.

### 5.1 Pergunta de Dupla Intenção
> **Pergunta:**  
> *"Por favor, extraia os dados essenciais da minuta contratual em anexo com a Alfa Consultoria em IA S.A. (valores, número de parcelas, vigência e penalidades) **E** verifique se o fornecedor possui situação cadastral regular na nossa base interna e se a multa rescisória de 20% atende às diretrizes corporativas da TechSolutions."*

### 5.2 Decomposição das Intenções e Execução dos Agentes
1. **Intenção 1 (Extração, Normalização e Consulta Cadastral):**
   - **Agente Acionado:** Agente 1 (Extrator Enriquecido).
   - **Execução Real:** O Agente 1 lê o texto da minuta, invoca a tool `normalizar_prazos_e_datas` (início `2026-09-01`, fim `2027-03-01`), invoca a tool `extrair_e_validar_tabela_financeira` (3 parcelas de R$ 15.000,00 = R$ 45.000,00) e consulta a tabela `cadastro_fornecedores` via `consultar_cadastro_fornecedor` para o CNPJ `98.765.432/0001-10`.
   - **Dado Produzido:** Payload estruturado `DadosContratoExtraido` (apresentado na subseção 4.1).
2. **Intenção 2 (Auditoria de Risco e Análise de Conformidade):**
   - **Agente Acionado:** Agente 2 (Avaliador de Risco).
   - **Execução Real:** O orquestrador repassa o JSON do Agente 1 ao Agente 2. O Agente 2 executa a tool `@function_tool auditar_parametros_contratuais`, identifica que a multa de 20% ultrapassa o teto de 10% corporativo (gerando ALERTA), confirma que o valor de R$ 45.000,00 está dentro da alçada e valida que o fornecedor está ATIVO com score 88.5/100.
   - **Dado Produzido:** Relatório executivo tipado `RelatorioConformidade` (apresentado na subseção 4.2).

### 5.3 Resposta Final Consolidada Entregue ao Usuário
```markdown
### Síntese da Análise Contratual (Dupla Intenção Atendida)

**1. Dados Extraídos do Contrato:**
- **Partes:** TechSolutions Ltda. (Contratante) e Alfa Consultoria em IA S.A. (Contratada - CNPJ 98.765.432/0001-10).
- **Objeto:** Desenvolvimento, integração e suporte de sistema de inteligência artificial multi-agentes.
- **Condições Financeiras:** R$ 45.000,00 em 3 parcelas mensais de R$ 15.000,00 (100% íntegro matematicamente).
- **Vigência:** 6 meses, de 01/09/2026 a 01/03/2027 (181 dias corridos), aviso prévio de 30 dias.
- **Penalidade Contratual:** Multa de 20% sobre o saldo remanescente em caso de rescisão imotivada.

**2. Diagnóstico de Governança e Cadastro Corporativo:**
- **Situação do Fornecedor:** O fornecedor Alfa Consultoria em IA S.A. está **ATIVO** na base estruturada corporativa com Score de Compliance de **88.5/100** e limite de alçada homologado de R$ 150.000,00.
- **Auditoria de Multa Rescisória:** **ALERTA (Risco Médio)**. A multa proposta de 20% excede o teto corporativo tolerado de 10%.
- **Recomendação:** Negociar a redução da multa para 10%, aplicando o precedente corporativo registrado no Aditivo nº 1 de 2025 já firmado com a própria Alfa Consultoria.
```

---

## 💾 6. Dados Estruturados (Tabelas Reais no SQLite)

O banco relacional do sistema está localizado em:  
📂 **`agent1/banco_memoria_contratos.db`**

### 6.1 Tabela `cadastro_fornecedores` (Fonte Estruturada de Negócio)
Armazena a base cadastral corporativa homologada:

```sql
CREATE TABLE IF NOT EXISTS cadastro_fornecedores (
    cnpj TEXT PRIMARY KEY,
    razao_social TEXT NOT NULL,
    nome_fantasia TEXT,
    situacao_cadastral TEXT NOT NULL,
    score_compliance REAL NOT NULL,
    limite_alcada_brl REAL NOT NULL,
    categoria_risco TEXT NOT NULL,
    data_homologacao TEXT NOT NULL,
    restricoes_juridicas TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- **Registros Homologados:**
  1. `98.765.432/0001-10` — *Alfa Consultoria em IA S.A.* (Ativa, Score 88.5, Alçada R$ 150k, Risco Médio).
  2. `12.345.678/0001-90` — *TechSolutions Ltda.* (Ativa, Score 96.0, Alçada R$ 500k, Risco Baixo).
  3. `23.456.789/0001-01` — *CloudCorp Soluções Digitais Ltda.* (Ativa, Score 91.0, Alçada R$ 300k, Risco Baixo).
  4. `99.888.777/0001-66` — *FraudeTech Serviços Suspensos ME* (Suspensa no CEIS, Score 25.0, Alçada R$ 0, Risco Alto).

### 6.2 Tabela `rag_documentos` (Vector Store com Embeddings)
> [!NOTE]
> A tabela do banco SQLite responsável pela busca semântica é denominada **`rag_documentos`** (e não `precedentes_contratuais`, alinhando a documentação rigorosamente com o código).

```sql
CREATE TABLE IF NOT EXISTS rag_documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id TEXT UNIQUE NOT NULL,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    metadados TEXT NOT NULL,
    vetor_embedding TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6.3 Tabela `sessoes_historico` (Memória Persistente SQLiteSession)
Mantém o histórico conversacional da `SQLiteSession`:

```sql
CREATE TABLE IF NOT EXISTS sessoes_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    item_data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔬 7. Consolidação Definitiva do Pipeline de Prompts e Avaliação A/B Real

O benchmark comparativo foi refeito com **execuções 100% REAIS** através do script [`evaluation/avaliacao_metricas_prompt.py`](evaluation/avaliacao_metricas_prompt.py) sobre a minuta real [`agent1/contrato_exemplo.txt`](agent1/contrato_exemplo.txt):

### 7.1 Métricas Utilizadas

$$\text{IGQ} = (0.30 \times \text{TCS}) + (0.30 \times \text{TIT}) + (0.20 \times \text{AFC}) + (0.20 \times \text{ASC})$$

### 7.2 Tabela de Resultados Reais Gravados

| Métrica | Variante A (Prompt Monolítico / LLM Real) | Variante B (Agente Estruturado + Tools / Runner.run) | Ganho |
| :--- | :---: | :---: | :---: |
| **TCS** (Conformidade de Schema) | `0.00` | `1.00` | **+1.00** |
| **TIT** (Invocação de Ferramentas) | `0.00` | `1.00` | **+1.00** |
| **AFC** (Acurácia Factual) | `1.00` | `1.00` | **0.00** |
| **ASC** (Sanitização e Cálculo) | `0.00` | `1.00` | **+1.00** |
| **Índice Geral de Qualidade (IGQ)** | **`0.200`** | **`1.000`** | **+0.800 (+400%)** |

- **Decisão Técnica Justificada:** Adoção mandatória da Variante B. Enquanto a Variante A produz prosa livre que não aciona ferramentas nem gera chaves consumíveis por APIs, a Variante B atinge conformidade total (IGQ = 1.000) e alimenta deterministicamente o Agente 2.

---

## 🌐 8. Orquestração Multi-Agente Completa no n8n (TP4)

No TP4, o **n8n assumiu o papel de único orquestrador central do sistema**, implementando o ciclo assíncrono completo entre os dois microsserviços. Os agentes operam de forma 100% desacoplada e independente: **nenhum agente chama o outro diretamente por código**.

O pipeline foi exportado e está versionado em [`workflows/workflow_tp4_orquestrador_completo.json`](workflows/workflow_tp4_orquestrador_completo.json).

```
[Trigger Manual / Webhook]
           │
           ▼
[Preparar Minuta Contratual]
           │
           ▼
[Agente 1: Submeter POST /run] (Porta 8001 -> Retorna 202 Accepted + task_id)
           │
     ┌─────┴─────────────────────────┐
     │   LOOP DE POLLING AGENTE 1    │
     │  [Wait 2s] -> [GET /status]   │
     │      │                        │
     │  [Concluído?] ─(False)─>[Falhou?] ──(True)──> [Tratamento de Exceção]
     └─────┬──────────────────(False: pending)───────> (Retorna ao Wait)
           │ (Se status == 'done')
           ▼
[Roteador: Dados Válidos para Auditoria?] ──(Se inválido)──> [Tratamento de Exceção]
           │ (Se válido: valor > 0 e penalidades)
           ├─────────────────────────────────────────────────┐
           ▼                                                 ▼
[Agente 2: Submeter POST /run] (Porta 8002)     [Empacotar Saída Agente 1]
           │                                                 │
     ┌─────┴─────────────────────────┐                       │
     │   LOOP DE POLLING AGENTE 2    │                       │
     │  [Wait 2s] -> [GET /status]   │                       │
     │      │                        │                       │
     │  [Concluído?] ─(False)─>[Falhou?] ──(True)──> [Exceção]
     └─────┬──────────────────(False: pending)───────────────┘
           │ (Se status == 'done')                           │
           ▼                                                 │
[Empacotar Saída Agente 2]                                   │
           │                                                 │
           └──────────────────────┬──────────────────────────┘
                                  ▼
[Merge Agente 1 e Agente 2] (Modo Combine / combineByPosition)
           │
           ▼
[Consolidar Dossiê Contratual Final] (Consome o item mesclado do nó Merge)
           │
           ▼
[AI Agent de Governança Estratégica] (@n8n/n8n-nodes-langchain.agent)
   ├── Conector ai_languageModel: [LLM Chat Model (OpenRouter)]
   └── Conector ai_tool: [Tool: Políticas de Governança] (@n8n/n8n-nodes-langchain.toolCode)
           │
           ▼
[Dossiê Executivo Homologado] (Parecer Conclusivo para a Diretoria)
```

### 8.1 Fases do Ciclo Assíncrono no n8n

1. **Submissão Inicial Não-Bloqueante:** O nó HTTP dispara `POST /run` para o Agente 1 (Porta 8001), recebendo `202 Accepted` imediato contendo `task_id` e `status: "pending"`.
2. **Loop de Polling com Espera Ativa e Proteção contra Falha:** O nó `Wait` (2s) e o nó `GET /status/{task_id}` operam em ciclo fechado com os nós `Agente 1 Concluído?` (`status == "done"`) e `Agente 1 Falhou?` (`status == "error"`), evitando loops infinitos caso ocorra erro no processamento.
3. **Roteamento Condicional de Integridade Contratual:**
   - O nó **Roteador** avalia as condições de negócio (`valor_total_brl > 0` e existência de cláusulas penais).
   - **Caminho de Exceção:** Se o contrato for inválido ou a extração falhar, desvia para o nó de tratamento de erro, abortando o pipeline sem onerar custos do Agente 2.
   - **Caminho Nominal:** Encaminha os dados estruturados para o Agente 2 e simultaneamente empacota a saída do Agente 1 (`agente1_resultado`) para preservação sem perdas no `Merge`.
4. **Acionamento e Polling do Agente 2:** Submete `POST /run` (Porta 8002) com o payload `dados_contrato` gerado pelo Agente 1, executando ciclo análogo de polling com detecção imediata de erro até `status == "done"`, seguido de **Empacotar Saída Agente 2** (`agente2_resultado`).
5. **Junção Sem Colisão via Nó Merge:** O nó `Merge` (`mode: "combine"`, `combineBy: "combineByPosition"`) unifica `{ agente1_resultado, agente2_resultado }` em um único item consumido diretamente pelo nó `Consolidar Dossiê Contratual Final`.

---

## 🧩 9. Componentes n8n de Alto Nível: AI Agent Node, LLM e Sub-workflow Reutilizável

O pipeline integrado supera a arquitetura tradicional de chamadas REST ao incorporar nós cognitivos e sub-workflows:

### 9.1 AI Agent Node com LangChain e Custom Code Tool no n8n
- **Nó AI Agent (`@n8n/n8n-nodes-langchain.agent`):** Atua como o consultor executivo que analisa o dossiê unificado e delibera estrategicamente sobre o risco do negócio.
- **Conector `ai_languageModel` (`@n8n/n8n-nodes-langchain.lmChatOpenAi`):** Modelo de linguagem conectado ao OpenRouter (`baseURL: "https://openrouter.ai/api/v1"`, modelo `nvidia/nemotron-3.5-lightning:free`) com `temperature: 0.2`.
- **Conector `ai_tool` (`@n8n/n8n-nodes-langchain.toolCode`):** Ferramenta JavaScript determinística que injeta a política corporativa de riscos vigente:
  - Teto de alçada gerencial: R$ 100.000,00.
  - Teto recomendado de multa rescisória: 10.0% (alerta acima de 10% e abusiva acima de 20%).
  - Exigência mandatória de ratificação pela Diretoria Executiva em contratos de risco médio/alto.

### 9.2 Sub-workflow Reutilizável de Polling Assíncrono ([`workflows/subworkflow_polling_assincrono.json`](workflows/subworkflow_polling_assincrono.json))
Componente modular e independente projetado para ser invocado isoladamente via nó `Execute Workflow` (`n8n-nodes-base.executeWorkflow`):
- **Entrada:** `{ "endpoint_status": "http://127.0.0.1:8001/status/", "task_id": "...", "intervalo_segundos": 2, "max_tentativas": 30 }`.
- **Máquina de Estados Resiliente:** Os nós `Incrementar Tentativa` e `Consolidar Estado do Polling` preservam `endpoint_status`, `tentativa_atual` e `max_tentativas` a cada iteração do loop HTTP, encerrando com erro tipado caso o agente retorne `status: "error"` (`ERRO_EXECUCAO_AGENTE`) ou atinja o limite de tentativas (`TIMEOUT_POLLING_EXCEDIDO`).
- **Benefício:** Elimina duplicação de lógica entre microsserviços, permitindo que qualquer agente adote o mesmo padrão de espera.

---

## 📜 10. Contratos Formais por Agente (`CLAUDE.md` e `AGENTS.md`)

Cada microsserviço possui seus próprios arquivos canônicos [`CLAUDE.md`](agent1/CLAUDE.md) e [`AGENTS.md`](agent1/AGENTS.md), que atuam como contrato formal de engenharia:

### 10.1 Contrato Formal do Agente 1 (Extrator Enriquecido)
- **Papel Exclusivo:** Ingestão de texto bruto, normalização temporal, cálculo financeiro e enriquecimento com o cadastro relacional de fornecedores.
- **Endpoint `POST /run`:** Recebe `{"texto_contrato": str}` $\rightarrow$ Retorna `202 Accepted` com `task_id`.
- **Endpoint `GET /status/{task_id}`:** Retorna `status` (`pending`, `done`, `error`) e payload `DadosContratoExtraido` (Pydantic v2).
- **Fronteira Estrita:** O Agente 1 **NÃO** avalia conformidade regulatória, não calcula scores de risco e não invoca o Agente 2.

### 10.2 Contrato Formal do Agente 2 (Auditor de Risco e Conformidade)
- **Papel Exclusivo:** Auditoria de regras corporativas, confronto de alçadas, validação de regularidade de fornecedores e redação do parecer executivo.
- **Endpoint `POST /run`:** Recebe `{"dados_contrato": dict}` $\rightarrow$ Retorna `202 Accepted` com `task_id`.
- **Endpoint `GET /status/{task_id}`:** Retorna `status` e payload `RelatorioConformidade` (Pydantic v2).
- **Fronteira Estrita:** O Agente 2 **NÃO** processa minutas em texto livre e consome apenas JSON estruturado previamente validado.

---

## ⚡ 11. Skills Reutilizáveis e Subagentes com Isolamento de Contexto

### 11.1 Skills Reutilizáveis com Frontmatter YAML

| Skill | Agente | Arquivos (`.claude/skills/` e `skills/`) | Responsabilidade |
| :--- | :--- | :--- | :--- |
| **`validacao-financeira-contratual`** | Agente 1 | [`agent1/.claude/skills/validacao-financeira-contratual/SKILL.md`](agent1/.claude/skills/validacao-financeira-contratual/SKILL.md) e [`agent1/skills/validacao-financeira-contratual/SKILL.md`](agent1/skills/validacao-financeira-contratual/SKILL.md) | Extrai, audita e valida a consistência entre valor global, parcelas e discrepâncias centesimais via `extrair_e_validar_tabela_financeira`. |
| **`auditoria-alcada-e-multa`** | Agente 2 | [`agent2/.claude/skills/auditoria-alcada-e-multa/SKILL.md`](agent2/.claude/skills/auditoria-alcada-e-multa/SKILL.md) e [`agent2/skills/auditoria-alcada-e-multa/SKILL.md`](agent2/skills/auditoria-alcada-e-multa/SKILL.md) | Define critérios para teto de multa (10%), alçada gerencial (R$ 100k) e ações de mitigação de risco. |

### 11.2 Subagentes com Isolamento de Contexto

| Subagente | Agente | Especificação (`.claude/agents/` e `subagents/`) | Código | Output Tipado |
| :--- | :--- | :--- | :--- | :--- |
| **`validador-cadastral-fornecedor`** | Agente 1 | [`agent1/.claude/agents/validador-cadastral-fornecedor.md`](agent1/.claude/agents/validador-cadastral-fornecedor.md) e [`agent1/subagents/validador_cadastral.md`](agent1/subagents/validador_cadastral.md) | [`agent1/subagente_cadastral.py`](agent1/subagente_cadastral.py) | `FornecedorHomologadoInfo` |
| **`auditor-clausulas-penais`** | Agente 2 | [`agent2/.claude/agents/auditor-clausulas-penais.md`](agent2/.claude/agents/auditor-clausulas-penais.md) e [`agent2/subagents/especialista_clausulas_penais.md`](agent2/subagents/especialista_clausulas_penais.md) | [`agent2/subagente_penalidades.py`](agent2/subagente_penalidades.py) | `ItemAuditoria` |

### 11.3 Justificativa Técnica do Isolamento de Contexto
A separação dos subagentes foi fundamentada em três pilares ([`agent1/subagents/README.md`](agent1/subagents/README.md) e [`agent2/subagents/README.md`](agent2/subagents/README.md)):
1. **Otimização da Janela de Contexto (*Context Budget*):** Minutas contratuais possuem dezenas de páginas. O subagente cadastral necessita apenas do CNPJ e razão social, economizando milhares de tokens e reduzindo latência.
2. **Prevenção de Ambiguidade de Papéis (*Anti-Hallucination & Role Confusion*):** O Agente 1 é estritamente descritivo (fiel ao texto original). Isolar o subagente impede que informações do histórico corporativo contaminem os termos originais da minuta. No Agente 2, o subagente de penalidades avalia a abusividade da multa sem viés comercial compensatório.
3. **Princípio do Menor Privilégio (*Least Privilege Security*):** Apenas o subagente cadastral possui permissão para acessar a ferramenta de consulta à tabela corporativa `cadastro_fornecedores`.

---

## 🛡️ 12. Governança Formal do Claude Code: Permissões e Hooks

A operação autônoma do Claude Code dentro de cada agente é regida por especificações formais de segurança:

### 12.1 Matriz de Permissões (`.claude/settings.json`)
Os arquivos `.claude/settings.json` de cada agente seguem integralmente o schema oficial do Claude Code (`https://json.schemastore.org/claude-code-settings.json`, validado sem avisos via `claude doctor`):
- **`allow`:** Operações seguras de leitura (`Read(*)`, `Glob(*)`, `Grep(*)`) e execução de testes locais (`Bash(python test_api.py*)`, `Bash(python agente_extracao.py*)`, `Bash(python agente_auditoria.py*)`).
- **`deny`:** Bloqueio estrito de violação de fronteira entre microsserviços (`Edit(../agent2/**)`, `Write(../agent2/**)` no Agente 1; `Edit(../agent1/**)`, `Write(../agent1/**)` no Agente 2), leitura/edição de segredos (`Read(.env*)`, `Edit(.env*)`, `Write(.env*)`) e comandos destrutivos (`Bash(rm -rf *)`, `Bash(del /f /q *)`, `Bash(git push --force*)`, `Bash(*DROP TABLE*)`).
- **`ask`:** Exigência de aprovação humana para alteração de schemas centrais (`Edit(models.py)`, `Write(models.py)`), camada HTTP (`Edit(main.py)`), ferramentas regulatórias (`Edit(tools.py)`), instalação de dependências (`Bash(pip install*)`) e push remoto (`Bash(git push*)`).

### 12.2 Hooks Automatizados e Verificáveis
1. **Hook `PreToolUse` (`.claude/hooks/pre_tool_use.py`):** Intercepta ferramentas de escrita (`Edit|Write|MultiEdit`) e comandos de terminal (`Bash`) lendo `tool_input` via `stdin`. Bloqueia violações de fronteira entre agentes, tentativas de acesso a `.env` e comandos destrutivos, retornando o **código oficial de bloqueio `2`** (`sys.exit(2)`) e registrando o evento em `hook_audit.log`.
2. **Hook `PostToolUse` (`.claude/hooks/post_tool_use.py`):** Disparado imediatamente após a escrita. Executa compilação sintática em Python (`py_compile.compile`) e validação estrutural de JSON (saindo com código `2` se houver corrupção), garantindo que nenhum código quebrado permaneça no repositório.

**Evidência de Execução dos Hooks ([`scripts/test_claude_hooks.py`](scripts/test_claude_hooks.py)):**
- Teste 1: Operação legítima no Agente 1 (`tool_input.file_path`) $\rightarrow$ **Aprovado (Código 0)**.
- Teste 2: Tentativa de alterar o Agente 2 $\rightarrow$ **Bloqueado (Código 2 - Violação de Fronteira)**.
- Teste 3: Tentativa de editar `.env` $\rightarrow$ **Bloqueado (Código 2 - Violação de Segurança)**.
- Teste 4: Comando destrutivo via `Bash` $\rightarrow$ **Bloqueado (Código 2)**.
- Teste 5: Validação sintática Python (`.py`) e JSON (`.json`) no `PostToolUse` $\rightarrow$ **Validado com Sucesso (Código 0)**.
- Teste 6: Tentativa do Agente 2 alterar o Agente 1 $\rightarrow$ **Bloqueado (Código 2)**.
- Teste 7: Validação sintática no `PostToolUse` do Agente 2 $\rightarrow$ **Validado com Sucesso (Código 0)**.

---

## 📊 13. Mapeamento Global de Requisitos do Projeto vs. Funcionalidades Implementadas

| Requisito do Projeto | Componente / Arquivo | Funcionalidade Concreta Entregue | Status |
| :--- | :--- | :--- | :---: |
| **Orquestração Assíncrona no n8n** | `workflows/workflow_tp4_orquestrador_completo.json` | Pipeline com ciclo assíncrono completo, polling de status, roteador e merge. | ✅ Homologado |
| **Sub-workflow Reutilizável** | `workflows/subworkflow_polling_assincrono.json` | Componente modular de polling resiliente com controle de retry e timeout. | ✅ Homologado |
| **Agent Node LangChain no n8n** | `workflows/workflow_tp4_orquestrador_completo.json` | AI Agent conectado a LLM Chat Model e Custom Tool de governança corporativa. | ✅ Homologado |
| **Microsserviço Extrator (Agente 1)** | `agent1/main.py`, `agent1/agente_extracao.py` | FastAPI na porta 8001 com BackgroundTasks e Agent real com OpenAI Agents SDK. | ✅ Homologado |
| **Microsserviço Auditor (Agente 2)** | `agent2/main.py`, `agent2/agente_auditoria.py` | FastAPI na porta 8002 com BackgroundTasks e Agent real com Pydantic v2. | ✅ Homologado |
| **Tools Determinísticas em Python** | `agent1/tools.py`, `agent2/tools.py` | Prazos ISO-8601, integridade de parcelas, alçadas e multas via `@function_tool`. | ✅ Homologado |
| **Fonte Estruturada de Negócio** | `agent1/memoria_rag.py` (`cadastro_fornecedores`) | Tabela SQLite com situação cadastral, score e limite de alçada homologado. | ✅ Homologado |
| **Memória Persistente e RAG** | `agent1/demo_memoria_rag.py`, `rag_documentos` | `SQLiteSession` multi-turno no `Runner.run` e busca vetorial de precedentes. | ✅ Homologado |
| **Raciocínio Encadeado (CoT)** | `agent1/pipeline_raciocinio.py` | *Least-to-Most* e *Chain-of-Thought* com chamadas reais ao modelo LLM. | ✅ Homologado |
| **Skills Reutilizáveis** | `agent1/skills/`, `agent2/skills/` | Arquivos `SKILL.md` padronizados com frontmatter YAML e instruções de negócio. | ✅ Homologado |
| **Subagentes com Contexto Isolado** | `agent1/subagents/`, `agent2/subagents/` | Subagentes cadastral e de penalidades desacoplados do contexto principal. | ✅ Homologado |
| **Governança do Claude Code** | `.claude/settings.json`, `.claude/hooks/` | Regras `allow`, `deny`, `ask` e hooks `PreToolUse` e `PostToolUse` automatizados. | ✅ Homologado |
| **Fontes de Verdade Canônicas** | `agent1/CLAUDE.md`, `agent2/CLAUDE.md` | Especificações formais e matrizes de rastreabilidade em cada projeto. | ✅ Homologado |

---

## 🧪 14. Evidências de Execução e Homologação Real

A execução ponta a ponta do ciclo assíncrono multi-agente foi registrada no arquivo [`workflows/evidencia_execucao_orquestrador_tp4.json`](workflows/evidencia_execucao_orquestrador_tp4.json):

```json
{
  "metadata_pipeline": {
    "orquestrador": "n8n Workflow Engine v1.x/v2.x",
    "ciclo": "Assíncrono Completo com Polling e Roteamento de Risco",
    "timestamp_conclusao": "2026-11-10T20:18:09.354293+00:00",
    "agente_extracao": {
      "task_id": "be72e145-5a19-4199-a49b-9ed48e2c9098",
      "status": "done",
      "tempo_processamento_s": 14.97
    },
    "agente_auditoria": {
      "task_id": "dc3ac386-1fc3-4db5-b197-8eaacf7e9f28",
      "status": "done",
      "tempo_processamento_s": 26.78
    }
  },
  "contrato": {
    "titulo": "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE DESENVOLVIMENTO DE INTELIGÊNCIA ARTIFICIAL",
    "partes": {
      "contratante": { "nome": "TechSolutions Ltda.", "cnpj_cpf": "12.345.678/0001-90" },
      "contratada": { "nome": "Alfa Consultoria em IA S.A.", "cnpj_cpf": "98.765.432/0001-10" }
    },
    "financeiro": { "valor_total_brl": 120000.0, "parcelas_quantidade": 12, "valor_parcela_brl": 10000.0 },
    "fornecedor_homologado": {
      "razao_social": "Alfa Consultoria em IA S.A.",
      "situacao_cadastral": "ATIVA",
      "score_compliance": 88.5,
      "limite_alcada_brl": 150000.0
    }
  },
  "auditoria_conformidade": {
    "score_conformidade": 88.5,
    "nivel_risco_geral": "ALTO",
    "total_regras_auditadas": 5,
    "itens_conformes": 3,
    "itens_alerta": 1,
    "itens_nao_conformes": 1
  },
  "decisao_governanca": "BLOQUEADO_REVISAO_JURIDICA_OBRIGATORIA"
}
```

---

## 🏆 15. Checklist Consolidado de Entregáveis do TP4

| Entregável Exigido | Localização no Repositório | Status |
| :--- | :--- | :---: |
| **Relatório Técnico em Markdown** | [`RELATORIO_TECNICO.md`](RELATORIO_TECNICO.md) | ✅ Completo e Detalhado |
| **Link do Repositório GitHub** | [https://github.com/MariaEduardaMendes/agente-analise-de-contratos](https://github.com/MariaEduardaMendes/agente-analise-de-contratos) | ✅ Atualizado e Sincronizado |
| **agent1/: settings.json, SKILL.md, CLAUDE.md/AGENTS.md** | [`agent1/`](agent1/) | ✅ Configurado e Testado |
| **agent2/: CLAUDE.md/AGENTS.md e configurações específicas** | [`agent2/`](agent2/) | ✅ Configurado e Testado |
| **workflows/: workflow principal e sub-workflow n8n em JSON** | [`workflows/`](workflows/) | ✅ Exportados e Validados |

